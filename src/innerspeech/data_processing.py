"""
Select trials, time windows and frequency bands of the loaded data.

The functions work on the arrays returned by
:mod:`innerspeech.data_extractions`: ``X`` with trials on the first axis and
time on the last, and ``Y`` the ``(n_trials, 4)`` events
``[sample, class, condition, session]``. They return views or single copies
and do not print.

@author: Nicolás Nieto
"""

from __future__ import annotations

import numpy as np

from innerspeech.exceptions import InvalidSelectionError

# Names accepted for every condition and class (case-insensitive)
CONDITIONS = {
    0: ("pron", "pronounced", "pronunciado"),
    1: ("in", "inner", "interno"),
    2: ("vis", "visualized", "visualizado"),
}
CLASSES = {
    0: ("up", "arriba"),
    1: ("down", "abajo"),
    2: ("right", "derecha"),
    3: ("left", "izquierda"),
}
_ALL = ("all", "todos", "todo")


def _code(name: str, names: dict[int, tuple[str, ...]], what: str) -> int | None:
    """Code of a condition or class name; None for "all"."""
    if not name:
        raise InvalidSelectionError(f"Select a {what}.")
    name = name.lower()
    if name in _ALL:
        return None
    for code, aliases in names.items():
        if name in aliases:
            return code
    raise InvalidSelectionError(f"The {what} {name!r} doesn't exist!")


def condition_code(condition: str) -> int | None:
    """
    Number of a condition name (``None`` for ``"all"``).

    Accepted names: ``"pron"``/``"pronounced"`` (0), ``"in"``/``"inner"`` (1),
    ``"vis"``/``"visualized"`` (2), their Spanish names, and ``"all"``;
    case-insensitive.
    """
    return _code(condition, CONDITIONS, "condition")


def class_code(class_label: str) -> int | None:
    """
    Number of a class name (``None`` for ``"all"``).

    Accepted names: ``"up"`` (0), ``"down"`` (1), ``"right"`` (2), ``"left"``
    (3), their Spanish names, and ``"all"``; case-insensitive.
    """
    return _code(class_label, CLASSES, "class")


def filter_by_condition(X: np.ndarray, Y: np.ndarray, condition: str) -> tuple:
    """
    Trials of one condition.

    Parameters
    ----------
    X : numpy.ndarray
        Data (or any array) with trials on the first axis.
    Y : numpy.ndarray
        ``(n_trials, 4)`` events.
    condition : str
        Condition name, see :func:`condition_code`.

    Returns
    -------
    tuple
        ``(X, Y)`` of the selected trials (unchanged for ``"all"``).
    """
    code = condition_code(condition)
    if code is None:
        return X, Y
    keep = Y[:, 2] == code
    return X[keep], Y[keep]


def filter_by_class(X: np.ndarray, Y: np.ndarray, class_condition: str) -> tuple:
    """
    Trials of one class.

    Parameters
    ----------
    X : numpy.ndarray
        Data (or any array) with trials on the first axis.
    Y : numpy.ndarray
        ``(n_trials, 4)`` events.
    class_condition : str
        Class name, see :func:`class_code`.

    Returns
    -------
    tuple
        ``(X, Y)`` of the selected trials (unchanged for ``"all"``).
    """
    code = class_code(class_condition)
    if code is None:
        return X, Y
    keep = Y[:, 1] == code
    return X[keep], Y[keep]


def transform_for_classifier(
    X: np.ndarray, Y: np.ndarray, classes: list, conditions: list
) -> tuple:
    """
    Data and labels for a classifier, one label per group of condition/class
    pairs.

    Parameters
    ----------
    X : numpy.ndarray
        Data with trials on the first axis.
    Y : numpy.ndarray
        ``(n_trials, 4)`` events.
    classes, conditions : list of list of str
        One list per group (label ``0, 1, ...``), with the class and condition
        of every pair in the group, e.g. ``classes=[["up"], ["down"]]`` and
        ``conditions=[["inner"], ["inner"]]`` for up vs down in inner speech.

    Returns
    -------
    X : numpy.ndarray
        The trials of every pair, group by group, in that order.
    Y : numpy.ndarray
        Float label (group number) of every trial.
    """
    if len(conditions) < 1 or len(classes) < 1:
        raise ValueError("You have to select classes and conditions")
    if len(conditions) != len(classes):
        raise ValueError("Incorrect number of conditions or classes")

    selected, labels = [], []
    for group, (group_conditions, group_classes) in enumerate(
        zip(conditions, classes, strict=True)
    ):
        if len(group_conditions) < 1 or len(group_classes) < 1:
            raise ValueError("You have to select classes for each condition")
        if len(group_conditions) != len(group_classes):
            raise ValueError("Incorrect number of conditions or classes")
        for condition, class_label in zip(group_conditions, group_classes, strict=True):
            index, _ = filter_by_condition(np.arange(len(Y)), Y, condition)
            index, _ = filter_by_class(index, Y[index], class_label)
            selected.append(index)
            labels.append(np.full(len(index), float(group)))
    return X[np.concatenate(selected)], np.concatenate(labels)


def select_time_window(
    X: np.ndarray, t_start: float = 1, t_end: float = 2.5, fs: int = 256
) -> np.ndarray:
    """
    Samples of a time window.

    Parameters
    ----------
    X : numpy.ndarray
        ``(n_trials, n_channels, n_times)`` data.
    t_start, t_end : float
        Window in seconds from the first sample (clipped to the data).
    fs : int
        Sampling frequency (Hz).

    Returns
    -------
    numpy.ndarray
        View of ``X`` restricted to the window.
    """
    start = max(round(t_start * fs), 0)
    end = min(round(t_end * fs), X.shape[2])
    return X[:, :, start:end]


def split_trial_in_time(
    X: np.ndarray, Y: np.ndarray, window_len: float, window_step: float, fs: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Cut every trial into overlapping time windows.

    Parameters
    ----------
    X : numpy.ndarray
        ``(n_trials, n_channels, n_times)`` data.
    Y : numpy.ndarray
        Labels or events, one row per trial.
    window_len, window_step : float
        Window length and step (s).
    fs : int
        Sampling frequency (Hz).

    Returns
    -------
    X : numpy.ndarray
        ``(n_trials * n_windows, n_channels, window samples)``: the windows of
        the first trial, then those of the second, ...
    Y : numpy.ndarray
        The row of ``Y`` of every window.
    """
    length = round(fs * window_len)
    step = round(fs * window_step)
    if length > X.shape[2]:
        raise ValueError(
            f"Window of {length} samples longer than the trials ({X.shape[2]})"
        )
    # (n_trials, n_channels, n_windows, length) view, then one copy
    windows = np.lib.stride_tricks.sliding_window_view(X, length, axis=2)[:, :, ::step]
    n_windows = windows.shape[2]
    X_windows = windows.transpose(0, 2, 1, 3).reshape(-1, X.shape[1], length)
    return X_windows, np.repeat(np.asarray(Y), n_windows, axis=0)


def average_in_frequency(
    power: np.ndarray, frequency: np.ndarray, bands: list
) -> np.ndarray:
    """
    Mean power in frequency bands.

    Parameters
    ----------
    power : numpy.ndarray
        ``(n, n_frequencies, n_times)`` power.
    frequency : numpy.ndarray
        Frequency of every row of the second axis (Hz).
    bands : list of tuple
        ``(f_min, f_max)`` of every band; frequencies strictly inside are
        averaged.

    Returns
    -------
    numpy.ndarray
        ``(n, n_bands, n_times)`` mean power of every band.
    """
    frequency = np.asarray(frequency)
    return np.stack(
        [
            power[:, (frequency > f_min) & (frequency < f_max), :].mean(axis=1)
            for f_min, f_max in bands
        ],
        axis=1,
    )


def calculate_power_windowed(
    signal_data: np.ndarray,
    fc: int,
    window_len: float,
    window_step: float,
    t_min: float,
    t_max: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Mean and standard deviation of the power in sliding windows.

    The power of a window is ``sum(x**2) / n_samples``. Windows of
    ``window_len`` seconds start at ``t_min`` and move by ``window_step``
    seconds; they continue while the previous window ended at or before
    ``t_max``, so the last window may reach past ``t_max`` (it is cut at the
    end of the signal). All windows are computed at once.

    Parameters
    ----------
    signal_data : numpy.ndarray
        Signal with time on the last axis, e.g. one channel ``(n_times,)`` or
        many trials and channels ``(n_trials, n_channels, n_times)``.
    fc : int
        Sampling frequency (Hz).
    window_len, window_step : float
        Window length and step (s).
    t_min : float
        Start of the first window (s from the first sample).
    t_max : float
        Windows start while the previous one ended at or before this time (s).

    Returns
    -------
    tuple of numpy.ndarray
        Mean and standard deviation of the window powers, with the shape of
        ``signal_data`` without its last axis (scalars for a 1-D signal).
    """
    signal_data = np.asarray(signal_data)
    n_times = signal_data.shape[-1]
    first = round(t_min * fc)
    last = round(t_max * fc)
    length = round(fc * window_len)
    step = round(fc * window_step)

    # Windows that end at or before ``last``, plus the one after them
    n_inside = (last - first - length) // step + 1 if last - first >= length else 0
    starts = first + step * np.arange(n_inside + 1)
    ends = np.minimum(starts + length, n_times)

    squared = signal_data**2
    power = np.empty((*signal_data.shape[:-1], len(starts)))
    full = ends - starts == length
    if full.any():
        # (..., n_windows, length) copy of the full windows, summed along time
        windows = np.lib.stride_tricks.sliding_window_view(squared, length, axis=-1)
        power[..., full] = windows[..., starts[full], :].sum(axis=-1) / length
    for k in np.flatnonzero(~full):  # windows cut at the end of the signal
        power[..., k] = squared[..., starts[k] : ends[k]].sum(axis=-1) / (
            ends[k] - starts[k]
        )

    return power.mean(axis=-1), power.std(axis=-1)
