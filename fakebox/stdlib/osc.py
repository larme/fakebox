import numpy as np

from fakebox.dsp import DSPObj, DSPFloat, DSPZero
from fakebox.stdlib.ba import Pipe, Router, Const, partial


class Phasor(DSPObj):

    def __init__(self):

        self.in_n = 4
        self.out_n = 1
        self.phase = 0.0
        super().__init__()

    def _tick(self, ins):
        freq = ins[0]
        init_phase = ins[1]
        freq_mod = ins[2]
        reset_phase_gate = ins[3]

        if reset_phase_gate > 0:
            self.reset_phase(init_phase)

        current_phase = self.phase

        freq = freq + freq_mod
        inc_per_sample = freq / self.sample_rate
        raw_phase = current_phase + inc_per_sample
        self.phase = raw_phase % 1
        return current_phase

    def reset_phase(self, init_phase):
        self.phase = init_phase
        self.counter = 0


class Sin(DSPObj):

    def __init__(self):

        self.in_n = 1
        self.out_n = 1

        super().__init__()

    def _tick(self, ins):
        phase = ins[0]
        return np.sin(2 * np.pi * phase)


def make_sinosc():

    phasor = Phasor()
    sinraw = Sin()
    sinosc = Pipe([phasor, sinraw])
    return sinosc


def make_simple_phasor(freq, init_phase=0.0):

    freq = Const(freq)
    init_phase = Const(init_phase)
    phasor = Phasor()

    # 0 freq | 1 init_phase | 2 freq mode in | 3 phase reset in
    # => 0 freq mode in | 1 phase reset in
    simple_phasor = partial(phasor, [freq, init_phase])

    return simple_phasor


def make_simple_sinosc(freq, init_phase=0.0):

    phasor = make_simple_phasor(freq, init_phase)
    sinraw = Sin()
    sinosc = Pipe([phasor, sinraw])
    return sinosc
