import numpy as np
from scipy.io.wavfile import write

import fakebox.dsp as dsp

def test(dsp_ctx=dsp.ctx):
    return dsp.ctx.sample_rate

def init_waveform(duration=None, sample_n=None, ctx=dsp.ctx):

    assert(duration or sample_n)

    sample_rate = ctx.sample_rate

    if duration:
        sample_n = int(round(duration * sample_rate))

    return np.zeros(sample_n, dtype=dsp.DSPFloat)


def save_waveform(waveform, path, quiet_factor=0.5, ctx=dsp.ctx):

    bit_n = ctx.bit_n
    sample_rate = ctx.sample_rate
    waveform_quiet = waveform * quiet_factor
    waveform_integers = np.int16(waveform_quiet * (2 ** (bit_n - 1) - 1))
    write(path, sample_rate, waveform_integers)
