import numpy as np
from fakebox.dsp import DSPObj, DSPZero, DSPOne

class Sum(DSPObj):

    def __init__(self, c=None, in_n=None):

        if not in_n:
            if c:
                in_n = 1
            else:
                in_n = 2

        self.in_n = in_n
        self.out_n = 1
        self.c = DSPZero if c is None else c

        super().__init__()

    def _tick(self, ins):
        res = np.sum(ins, initial=self.c)
        return [res]


class Mul(DSPObj):

    def __init__(self, c=None, in_n=None, **kwargs):

        if not in_n:
            if c:
                in_n = 1
            else:
                in_n = 2

        self.in_n = in_n
        self.out_n = 1
        self.c = DSPOne if c is None else c

        super().__init__(**kwargs)

    def _tick(self, ins):
        res = np.prod(ins, initial=self.c)
        return [res]


class Neg(DSPObj):

    def __init__(self):

        self.in_n = 1
        self.out_n = 1

        super().__init__()

    def _tick(self, ins):
        res = np.negative(ins)
        return [res]
