import numpy as np
from fakebox.dsp import DSPObj, DSPZero, DSPEpsilon

class LineSegs(DSPObj):

    def __init__(self, seg_n):

        self.seg_n = seg_n
        self.in_n = seg_n * 2 + 1
        self.out_n = 1
        self.amp = DSPZero
        self.running = False

        super().__init__()


    def _tick(self, ins):

        # trigger
        trig = ins[-1]
        if trig > DSPZero:
            self.running = True
            self.counter = 0

        if self.running == False:
            return [DSPZero]

        # time in ms
        running_time = 1000.0 * self.counter / self.sample_rate

        # seg_n durations to next point
        durations = ins[1:self.seg_n + 1]
        time_points = [DSPZero]
        for dur in durations:
            time_points.append(time_points[-1] + dur)


        if running_time > time_points[-1] - DSPEpsilon:
            self.running = False
            return [DSPZero]

        tp_pairs = list(zip(time_points[:-1], time_points[1:]))

        current_seg_idx = None
        current_seg_end = None
        for idx, pair in enumerate(tp_pairs):
            start, end = pair
            if start <= running_time < end:
                current_seg_idx = idx
                current_seg_end = end
                break

        # convert time from ms to seconds
        time_diff_in_s = (current_seg_end - running_time) / 1000.0
        sample_diff = time_diff_in_s * self.sample_rate

        current_amp = self.amp

        # seg_n - 1 amps, the beginning and ending amp is 0.0
        amp_factor = ins[0]
        next_amps = ins[self.seg_n + 1:-1]
        amps = [DSPZero] + [a * amp_factor for a in next_amps] + [DSPZero]
        amp_pairs = list(zip(amps[:-1], amps[1:]))
        pair = amp_pairs[current_seg_idx]
        target_amp = pair[1]

        amp_diff = target_amp - current_amp
        amp_inc_per_sample = amp_diff / sample_diff
        self.amp = current_amp + amp_inc_per_sample

        return [self.amp]
