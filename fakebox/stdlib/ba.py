import numpy as np
from fakebox.dsp import DSPObj, DSPZero


class Dummy(DSPObj):

    def __init__(self, in_n, out_n):

        self.in_n = in_n
        self.out_n = out_n
        super().__init__()

    def _tick(self, ins):
        return DSPZero


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

        if not in_n:
            in_n = max(ins2outs.keys())

        if not out_n:
            out_n = max(ins2outs.values)

        zero_outlets = set()

        self.in_n = in_n
        self.out_n = out_n
        self.ins2outs = ins2outs
        super().__init__()

    def _tick(self, ins):

        outs_d = {out: ins[in_] for in_, out in ins2outs.items()}
        outs = [outs_d.get(o, DSPZero) for o in range(self.out_n)]
        return outs


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
