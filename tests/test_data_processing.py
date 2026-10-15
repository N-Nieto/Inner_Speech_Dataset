"""Windowed power (EMG control) and trial selection helpers."""

import numpy as np
import pytest

from innerspeech.data_processing import (
    calculate_power_windowed,
    filter_by_class,
    filter_by_condition,
)


def reference_power(signal, fc, window_len, window_step, t_min, t_max):
    """The original loop implementation (releases up to 2.1.2)."""
    initial = round(t_min * fc)
    last = round(t_max * fc)
    length = round(fc * window_len)
    step = round(fc * window_step)
    power, final = [], 0
    while final <= last:
        final = initial + length
        cut = signal[initial:final]
        power.append(np.sum(cut**2, axis=0) / cut.size)
        initial += step
    return np.mean(power, axis=0), np.std(power, axis=0)


@pytest.mark.parametrize(
    ("n_times", "t_min", "t_max"),
    [
        (1153, 1, 3.5),  # trials: all windows inside the signal
        (3841, 0, 15),  # baseline: the last window passes the end of the signal
        (600, 0.2, 0.3),  # first window already ends after t_max
    ],
)
def test_power_matches_original_loop(n_times, t_min, t_max):
    rng = np.random.default_rng(0)
    x = np.abs(rng.normal(size=(5, n_times)))
    mean, std = calculate_power_windowed(x, 256, 0.5, 0.05, t_min, t_max)
    for row, m, s in zip(x, mean, std, strict=True):
        ref_m, ref_s = reference_power(row, 256, 0.5, 0.05, t_min, t_max)
        assert m == ref_m and s == ref_s  # bit-identical
    one_m, one_s = calculate_power_windowed(x[0], 256, 0.5, 0.05, t_min, t_max)
    assert np.ndim(one_m) == 0 and one_m == mean[0] and one_s == std[0]


def test_filters_select_condition_and_class():
    y = np.array([[0, c % 4, c % 3, 1] for c in range(12)])
    x = np.arange(12)
    xi, yi = filter_by_condition(x, y, "inner")
    assert (yi[:, 2] == 1).all() and np.array_equal(xi, x[y[:, 2] == 1])
    xc, yc = filter_by_class(x, y, "Left")
    assert (yc[:, 1] == 3).all() and np.array_equal(xc, x[y[:, 1] == 3])
    assert filter_by_condition(x, y, "all")[0] is x
    with pytest.raises(ValueError):
        filter_by_class(x, y, "forward")
