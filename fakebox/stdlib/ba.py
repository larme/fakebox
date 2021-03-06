import numpy as np
from fakebox.dsp import DSPObj, DSPZero, DSPOne


class Bypass(DSPObj):

    def __init__(self, n=1, **kwargs):

        self.in_n = n
        self.out_n = n
        super().__init__(**kwargs)

    def _tick(self, ins):
        return ins


class Const(DSPObj):

    def __init__(self, c):

        self.in_n = 0
        self.out_n = 1
        self.c = c
        super().__init__()

    def _tick(self, ins):
        return [self.c]

    def get_value(self):
        return self.c


class Parameter(DSPObj):

    def __init__(self, preset, ptr):

        self.in_n = 0
        self.out_n = 1

        self.preset = preset
        self.ptr = ptr

        super().__init__()

    def _tick(self, ins):
        return self.preset[self.ptr:self.ptr+1]

    def get_value(self):
        return self.preset[self.ptr]

    def set_value(self, v):
        self.preset[self.ptr] = v


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
                outs = np.zeros(out_n)
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

    def __init__(self, in_n=1, factor=2):

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


class Mixer(DSPObj):

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
        return [out]


class Pipe(DSPObj):

    def __init__(self, objs, unsafe=True, **kwargs):

        assert(objs)

        for idx, obj in enumerate(objs[:-1]):
            next_obj = objs[idx + 1]
            assert(obj.out_n == next_obj.in_n)

        self.objs = objs
        self.unsafe = unsafe
        self.in_n = self.objs[0].in_n
        self.out_n = self.objs[-1].out_n

        super().__init__(**kwargs)

    def __repr__(self):
        this_repr = super().__repr__()
        objs_repr = str([repr(obj) for obj in self.objs])
        return this_repr + ' with objs: ' + objs_repr

    def _tick_safe(self, ins):

        objs = self.objs

        objs[0].in_buffer[:] = ins

        for idx, obj in enumerate(objs[:-1]):
            next_obj = objs[idx + 1]
            obj.tick()
            next_obj.in_buffer[:] = obj.out_buffer

        last_obj = objs[-1]
        last_obj.tick()
        
        return np.copy(last_obj.out_buffer)

    def _tick_unsafe(self, ins):

        objs = self.objs

        for obj in objs:
            ins = obj._tick(ins)
            obj.inc_counter()

        return ins

    def _tick(self, ins):
        if self.unsafe:
            return self._tick_unsafe(ins)
        else:
            return self._tick_safe(ins)


class Stack(DSPObj):

    def __init__(self, objs, unsafe=True, **kwargs):

        assert(objs)

        self.in_n = sum(obj.in_n for obj in objs)
        self.out_n = sum(obj.out_n for obj in objs)
        self.objs = objs
        self.unsafe = unsafe
        super().__init__(**kwargs)

    def __repr__(self):
        this_repr = super().__repr__()
        objs_repr = str([repr(obj) for obj in self.objs])
        return this_repr + ' with objs: ' + objs_repr

    def _tick_safe(self, ins):

        # copy input to objs' input

        in_idx = 0
        out_idx = 0
        outs = np.zeros(self.out_n)

        for obj in self.objs:

            obj.in_buffer[:] = ins[in_idx:in_idx+obj.in_n]
            in_idx += obj.in_n

            obj.tick()

            outs[out_idx:out_idx+obj.out_n] = obj.out_buffer
            out_idx += obj.out_n

        return outs

    def _tick_unsafe(self, ins):

        l = []
        in_idx = 0
        for obj in self.objs:
            out = obj._tick(ins[in_idx:in_idx+obj.in_n])
            obj.inc_counter()
            in_idx += obj.in_n
            l.append(out)
        outs = np.concatenate(l)
        return outs

    def _tick(self, ins):
        if self.unsafe:
            return self._tick_unsafe(ins)
        else:
            return self._tick_safe(ins)


def partial(func, args, router=None):

    assert(args)
    func_in_n = func.in_n
    args_out_n = sum(arg.out_n for arg in args)
    assert(func_in_n >= args_out_n)

    bypass_n = func_in_n - args_out_n
    bypass = Bypass(n=bypass_n)
    objs = args + [bypass]
    stack = Stack(objs)

    if router:
        seqs = [stack, router, func]
    else:
        seqs = [stack, func]

    return Pipe(seqs)


class RecursiveIn(DSPObj):

    def __init__(self, in_n, buff, bypass=True):

        assert(in_n == len(buff))

        self.in_n = in_n

        if bypass:
            self.out_n = in_n
        else:
            self.out_n = 0

        self.buff = buff
        self.bypass = bypass

        super().__init__()

    def _tick(self, ins):
        self.buff[:] = ins

        if self.bypass:
            return ins
        else:
            return DSPZero


class RecursiveOut(DSPObj):

    def __init__(self, out_n, buff):

        assert(out_n == len(buff))

        self.in_n = 0
        self.out_n = out_n
        self.buff = buff

        super().__init__()

    def _tick(self, ins):
        return self.buff


def make_recursive_pair(io_n, bypass=True):

    buff = np.zeros(io_n)
    rin = RecursiveIn(io_n, buff, bypass=bypass)
    rout = RecursiveOut(io_n, buff)
    return rout, rin
