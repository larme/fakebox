import abc

import numpy as np

from fakebox.conf import DEFAULT_SAMPLE_RATE, DEFAULT_BIT_N

DSPFloat = np.float64
DSPEpsilon = DSPFloat(1e-8)
DSPZero = DSPFloat(0.0)
DSPOne = DSPFloat(1.0)
DSPOne_L = DSPFloat(1.0) - DSPEpsilon

class DSPContext(object):

    def __init__(self, sample_rate=DEFAULT_SAMPLE_RATE, bit_n=DEFAULT_BIT_N):
        self.sample_rate = sample_rate
        self.bit_n = bit_n
        self.sample_step = 0

    def tick(self):
        self.sample_step += 1


ctx = DSPContext()


class DSPObj(abc.ABC):

    def __init__(self):

        try:
            self.in_n + self.out_n
        except AttributeError:
            raise NotImplementedError

        self._ctx = ctx
        self.counter = 0
        self.in_buffer = np.zeros(self.in_n, dtype=DSPFloat)
        self.out_buffer = np.zeros(self.out_n, dtype=DSPFloat)

    def reset(self):
        self.counter = 0
        self.in_buffer = np.zeros(self.in_n, dtype=DSPFloat)
        self.out_buffer = np.zeros(self.out_n, dtype=DSPFloat)

    @abc.abstractmethod
    def _tick(self, ins):
        raise NotImplementedError

    def tick(self):
        outs = self._tick(self.in_buffer)
        self.out_buffer[:] = outs
        self.in_buffer[:] = DSPZero
        self.counter += 1

    @property
    def sample_rate(self):
        return self._ctx.sample_rate

    @property
    def bit_n(self):
        return self._ctx.bit_n

