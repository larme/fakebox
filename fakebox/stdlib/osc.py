import numpy as np

from fakebox.dsp import DSPObj, DSPFloat, DSPZero
from fakebox.lib.ba import Pipe


class Phasor(DSPObj):

    def __init__(self, freq, init_phase=0.0):

        self.in_n = 2
        self.out_n = 1
        self.freq = freq
        self.init_phase = init_phase
        self.phase = self.init_phase
        super().__init__()

    def _tick(self, ins):
        freq_mod = ins[0]
        reset_phase_gate = ins[1]

        if reset_phase_gate > 0:
            self.reset_phase()

        current_phase = self.phase

        freq = self.freq + freq_mod
        inc_per_sample = freq / self.sample_rate
        raw_phase = current_phase + inc_per_sample
        self.phase = raw_phase % 1
        return current_phase

    def reset_phase(self):
        self.phase = self.init_phase
        self.counter = 0


class Sin(DSPObj):

    def __init__(self):

        self.in_n = 1
        self.out_n = 1

        super().__init__()

    def _tick(self, ins):
        phase = ins[0]
        return np.sin(2 * np.pi * phase)


def make_sinosc(freq, init_phase=0.0):
    phasor = Phasor(freq, init_phase)
    sinraw = Sin()
    sinosc = Pipe([phasor, sinraw])
    return sinosc
