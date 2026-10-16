"""Windowed power (EMG control), trial selection and name helpers."""

import numpy as np
import pytest

from innerspeech.data_processing import (
    average_in_frequency,
    calculate_power_windowed,
    filter_by_class,
    filter_by_condition,
    split_trial_in_time,
    transform_for_classifier,
)
from innerspeech.utils import map_class, map_condition


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


def test_transform_for_classifier():
    y = np.array([[0, c % 4, c % 3, 1] for c in range(24)])
    x = np.arange(24)
    xt, yt = transform_for_classifier(
        x, y, classes=[["up", "down"], ["left"]], conditions=[["inner", "vis"], ["all"]]
    )
    up_inner = x[(y[:, 1] == 0) & (y[:, 2] == 1)]
    down_vis = x[(y[:, 1] == 1) & (y[:, 2] == 2)]
    left = x[y[:, 1] == 3]
    assert np.array_equal(xt, np.concatenate([up_inner, down_vis, left]))
    assert yt.tolist() == [0.0] * (len(up_inner) + len(down_vis)) + [1.0] * len(left)
    with pytest.raises(ValueError):
        transform_for_classifier(
            x, y, classes=[["up"]], conditions=[["inner"], ["vis"]]
        )


def test_split_trial_in_time():
    x = np.arange(2 * 3 * 10, dtype=float).reshape(2, 3, 10)
    y = np.array([[0, 1, 1, 1], [5, 2, 0, 1]])
    xs, ys = split_trial_in_time(x, y, window_len=0.4, window_step=0.3, fs=10)
    starts = [0, 3, 6]  # windows of 4 samples that fit in 10
    assert xs.shape == (6, 3, 4)
    for k, (trial, start) in enumerate((t, s) for t in range(2) for s in starts):
        assert np.array_equal(xs[k], x[trial, :, start : start + 4])
        assert np.array_equal(ys[k], y[trial])
    with pytest.raises(ValueError):
        split_trial_in_time(x, y, window_len=2, window_step=0.1, fs=10)


def test_average_in_frequency():
    rng = np.random.default_rng(0)
    power = rng.random((3, 6, 5))
    freqs = np.array([2, 4, 6, 8, 10, 12])
    bands = average_in_frequency(power, freqs, [(3, 7), (7, 13)])
    assert bands.shape == (3, 2, 5)
    assert np.allclose(bands[:, 0], power[:, 1:3].mean(axis=1))
    assert np.allclose(bands[:, 1], power[:, 3:].mean(axis=1))


@pytest.mark.parametrize(
    ("name", "condition"),
    [("p", "pronounced"), ("IN", "inner"), ("visualizado", "visualized")],
)
def test_condition_names(name, condition):
    assert map_condition(name) == condition


@pytest.mark.parametrize(
    ("name", "label"),
    [("d", "down"), ("r", "right"), ("der", "right"), ("i", "left"), ("ARRIBA", "up")],
)
def test_class_names(name, label):
    assert map_class(name) == label
