import numpy as np
from fakebox.dsp import DSPObj, DSPZero, DSPOne


class Bypass(DSPObj):

    def __init__(self, n=1):

        self.in_n = n
        self.out_n = n
        super().__init__()

    def _tick(self, ins):
        return ins


class Const(DSPObj):

    def __init__(self, c):

        self.in_n = 0
        self.out_n = 1
        self.c = c
        super().__init__()

    def _tick(self, ins):
        return self.c


class Parameter(DSPObj):

    def __init__(self, preset, ptr):

        self.in_n = 0
        self.out_n = 1

        self.preset = preset
        self.ptr = ptr

        super().__init__()

    def _tick(self, ins):
        return self.preset[self.ptr]


class Dummy(DSPObj):

    def __init__(self, in_n, out_n=None, outs=None):

        assert(out_n or outs)

        if outs:
            try:
                iter(outs)
            except TypeError:
                outs = (outs, )

        if out_n:
            if outs:
                assert(out_n == len(outs))
            else:
                outs = DSPZero
        else:
            out_n = len(outs)

        self.outs = outs

        self.in_n = in_n
        self.out_n = out_n
        self.outs = outs
        super().__init__()

    def _tick(self, ins):
        return self.outs


class Dup(DSPObj):

    def __init__(self, in_n, factor):

        self.in_n = in_n
        self.out_n = in_n * factor
        super().__init__()

    def _tick(self, ins):

        outs = [ins[i % self.in_n] for i in range(self.out_n)]
        return outs


class Router(DSPObj):

    def __init__(self, ins2outs, in_n=None, out_n=None):

        try:
            ins2outs.keys()
        except AttributeError:
            ins2outs = {in_: out for out, in_ in enumerate(ins2outs)}

        if not in_n:
            in_n = max(ins2outs.keys()) + 1

        if not out_n:
            out_n = max(ins2outs.values()) + 1

        zero_outlets = set()

        self.in_n = in_n
        self.out_n = out_n
        self.ins2outs = ins2outs
        super().__init__()

    def _tick(self, ins):

        outs_d = {out: ins[in_] for in_, out in self.ins2outs.items()}
        outs = [outs_d.get(o, DSPZero) for o in range(self.out_n)]
        return outs


class Mixer(DSPZero):

    def __init__(self, weights=None, in_n=None):

        assert(weights or in_n)

        if weights:
            in_n = len(weights)
        else:
            weights = [1.0 for i in range(in_n)]

        self.in_n = in_n
        self.out_n = 1
        self.weights = weights
        super().__init__()

    def _tick(self, ins):

        pairs = zip(ins, self.weights)
        out = sum(v * weight for v, weight in pairs)
        return out


class Pipe(DSPObj):

    def __init__(self, objs):

        assert(objs)

        for idx, obj in enumerate(objs[:-1]):
            next_obj = objs[idx + 1]
            assert(obj.out_n == next_obj.in_n)

        self.objs = objs
        self.in_n = self.objs[0].in_n
        self.out_n = self.objs[-1].out_n

        super().__init__()

    def _tick(self, ins):

        objs = self.objs

        for i in range(len(ins)):
            objs[0].in_buffer[i] = ins[i]

        for idx, obj in enumerate(objs[:-1]):
            next_obj = objs[idx + 1]
            obj.tick()
            for i in range(len(obj.out_buffer)):
                next_obj.in_buffer[i] = obj.out_buffer[i]

        last_obj = objs[-1]
        last_obj.tick()
        
        return np.copy(last_obj.out_buffer)


class Stack(DSPObj):

    def __init__(self, objs):

        assert(objs)

        self.in_n = sum(obj.in_n for obj in objs)
        self.out_n = sum(obj.out_n for obj in objs)
        self.objs = objs
        super().__init__()

    def _tick(self, ins):

        objs = self.objs

        # copy input to objs' input

        in_idx = 0
        outs = []

        for obj in objs:
            for i in range(obj.in_n):
                obj.in_buffer[i] = ins[in_idx]
                in_idx += 1

            obj.tick()
            outs.extend(obj.out_buffer)

        return outs


def partial(func, args, router=None):

    assert(args)
    func_in_n = func.in_n
    args_out_n = sum(arg.out_n for arg in args)
    assert(func_in_n > args_out_n)

    bypass_n = func_in_n - args_out_n
    bypass = Bypass(n=bypass_n)
    objs = args + [bypass]
    stack = Stack(objs)

    if router:
        seqs = [stack, router, func]
    else:
        seqs = [stack, func]

    return Pipe(seqs)
