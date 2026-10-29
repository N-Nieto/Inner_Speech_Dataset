"""
Load the raw recordings and the derivatives of the Inner Speech Dataset.

``root_dir`` is the dataset folder (``ds003626``); the derivatives are read from
``<root_dir>/derivatives`` through :mod:`innerspeech.derivatives_io`.

Arrays returned by the loaders:

- ``X``: ``(n_trials, n_channels, n_times)`` float64 data, in volts.
- ``Y``: ``(n_trials, 4)`` events ``[sample, class, condition, session]``
  (class 0-3 = up, down, right, left; condition 0-2 = pronounced, inner,
  visualized).

For selections of conditions and classes across subjects,
:func:`extract_condition_epochs` reads only the selected trials and returns an
``mne.EpochsArray`` with the trial metadata.

@author: Nicolás Nieto
"""

from __future__ import annotations

from pathlib import Path

import mne
import numpy as np
import pandas as pd

from innerspeech import derivatives_io
from innerspeech.data_processing import filter_by_class, filter_by_condition
from innerspeech.derivatives_io import derivative_path, session_label, subject_label
from innerspeech.protocol import KNOWN_ISSUES
from innerspeech.utils import unify_names

SESSIONS = (1, 2, 3)

# datatype -> derivative file kind
_EPOCH_KINDS = {
    "eeg": "eeg-epo.fif",
    "exg": "exg-epo.fif",
    "baseline": "baseline-epo.fif",
}


def _derivatives_dir(root_dir: str | Path) -> Path:
    """``<root_dir>/derivatives`` (root_dir is the ``ds003626`` folder)."""
    return Path(root_dir) / "derivatives"


def _epochs_path(root_dir: str | Path, n_s: int, n_b: int, datatype: str) -> Path:
    kind = _EPOCH_KINDS.get(datatype.lower())
    if kind is None:
        raise ValueError(
            f"Invalid datatype {datatype!r}; use one of {tuple(_EPOCH_KINDS)}"
        )
    return derivative_path(_derivatives_dir(root_dir), n_s, n_b, kind)


def _read_epochs(root_dir, n_s, n_b, datatype) -> mne.BaseEpochs:
    """Epochs of one session, header only (data are read on ``get_data``)."""
    return mne.read_epochs(
        _epochs_path(root_dir, n_s, n_b, datatype), preload=False, verbose="WARNING"
    )


def _stack_sessions(
    root_dir: str | Path, sessions: list[tuple[int, int]], datatype: str
) -> tuple[np.ndarray, np.ndarray]:
    """Data and events of several sessions, read into preallocated arrays.

    The files are opened without loading their data, so the output can be
    allocated before reading and every session is copied into it once.
    """
    epochs = [_read_epochs(root_dir, n_s, n_b, datatype) for n_s, n_b in sessions]
    n_channels, n_times = len(epochs[0].ch_names), len(epochs[0].times)
    for ep, (n_s, n_b) in zip(epochs, sessions, strict=True):
        if (len(ep.ch_names), len(ep.times)) != (n_channels, n_times):
            raise ValueError(
                f"{subject_label(n_s)} {session_label(n_b)}: {datatype} epochs of "
                f"shape {(len(ep.ch_names), len(ep.times))}, expected "
                f"{(n_channels, n_times)}"
            )
    x = np.empty((sum(len(ep) for ep in epochs), n_channels, n_times))
    start = 0
    for ep in epochs:
        x[start : start + len(ep)] = ep.get_data(verbose="WARNING")
        start += len(ep)
    y = np.concatenate([load_events(root_dir, n_s, n_b) for n_s, n_b in sessions])
    return x, y


# ----------------------------------------------------------------------------
# Raw data
# ----------------------------------------------------------------------------
def extract_subject_from_bdf(data_dir: Path, n_s: int, n_b: int) -> tuple:
    """
    Read the raw recording of one session.

    Parameters
    ----------
    data_dir : Path
        The ``ds003626`` folder with the raw data.
    n_s, n_b : int
        Subject and session numbers.

    Returns
    -------
    raw : mne.io.Raw
        The recording, loaded into memory (1024 Hz, 128 EEG + 8 EXG + Status).
    subject : str
        Subject label, e.g. ``"sub-01"``.
    """
    sub, ses = subject_label(n_s), session_label(n_b)
    file_name = (
        Path(data_dir) / sub / ses / "eeg" / f"{sub}_{ses}_task-innerspeech_eeg.bdf"
    )
    raw = mne.io.read_raw_bdf(input_fname=file_name, preload=True, verbose="WARNING")
    return raw, sub


def get_events_from_raw(
    rawdata: mne.io.BaseRaw, N_S: int, N_B: int, known_issues: dict | None = None
) -> pd.DataFrame:
    """
    Triggers of a raw recording.

    Parameters
    ----------
    rawdata : mne.io.BaseRaw
        Raw recording with its Status channel.
    N_S, N_B : int
        Subject and session numbers.
    known_issues : dict, optional
        Per-session exceptions (default
        :data:`innerspeech.protocol.KNOWN_ISSUES`); a ``"find_events"`` entry
        holds extra arguments of :func:`mne.find_events` for that session.

    Returns
    -------
    pandas.DataFrame
        Columns ``Time`` (sample), ``Trigger`` (previous Status value) and
        ``Code``.
    """
    issues = KNOWN_ISSUES if known_issues is None else known_issues
    extra = issues.get((N_S, N_B), {}).get("find_events", {})
    events = mne.find_events(
        rawdata, initial_event=True, consecutive=True, verbose="WARNING", **extra
    )
    return pd.DataFrame(events, columns=["Time", "Trigger", "Code"])


# ----------------------------------------------------------------------------
# Derivatives
# ----------------------------------------------------------------------------
def load_events(root_dir: Path, n_s: int, n_b: int) -> np.ndarray:
    """
    Events of one session.

    Parameters
    ----------
    root_dir : Path
        The ``ds003626`` folder (containing ``derivatives``).
    n_s, n_b : int
        Subject and session numbers.

    Returns
    -------
    numpy.ndarray
        ``(n_trials, 4)`` int64 array ``[sample, class, condition, session]``.
        :func:`innerspeech.derivatives_io.load_events_table` gives the full
        trial table, EMG control results included.
    """
    return derivatives_io.load_events(_derivatives_dir(root_dir), n_s, n_b)


def extract_report(root_dir: Path, n_b: int, n_s: int) -> dict:
    """
    Report of one session (note the order: session, then subject).

    Parameters
    ----------
    root_dir : Path
        The ``ds003626`` folder (containing ``derivatives``).
    n_b, n_s : int
        Session and subject numbers.

    Returns
    -------
    dict
        See :func:`innerspeech.derivatives_io.load_report`.
    """
    return derivatives_io.load_report(_derivatives_dir(root_dir), n_s, n_b)


def extract_block_data_from_subject(
    root_dir: Path, n_s: int, datatype: str, n_b: int
) -> tuple:
    """
    Epochs and events of one session.

    Parameters
    ----------
    root_dir : Path
        The ``ds003626`` folder (containing ``derivatives``).
    n_s : int
        Subject number.
    datatype : {"eeg", "exg", "baseline"}
        File to read.
    n_b : int
        Session number.

    Returns
    -------
    X : mne.Epochs
        The epochs, loaded into memory.
    Y : numpy.ndarray
        Events of the session's trials (also for ``"baseline"``, whose file
        holds a single epoch).
    """
    file_name = _epochs_path(root_dir, n_s, n_b, datatype)
    y = load_events(root_dir, n_s, n_b)
    X = mne.read_epochs(file_name, verbose="WARNING")
    return X, y


def extract_data_from_subject(root_dir: Path, n_s: int, datatype: str) -> tuple:
    """
    Data and events of the three sessions of one subject.

    Parameters
    ----------
    root_dir : Path
        The ``ds003626`` folder (containing ``derivatives``).
    n_s : int
        Subject number.
    datatype : {"eeg", "exg", "baseline"}
        File to read.

    Returns
    -------
    X : numpy.ndarray
        ``(n_trials, n_channels, n_times)`` data of the sessions, in order
        (``(3, n_channels, n_times)`` for ``"baseline"``).
    Y : numpy.ndarray
        ``(n_trials, 4)`` int64 events of the trials of the sessions.
    """
    return _stack_sessions(root_dir, [(n_s, n_b) for n_b in SESSIONS], datatype)


def extract_data_multisubject(
    root_dir: Path, n_s_list: list, datatype: str = "eeg"
) -> np.ndarray | tuple:
    """
    Data and events of the three sessions of several subjects.

    Parameters
    ----------
    root_dir : Path
        The ``ds003626`` folder (containing ``derivatives``).
    n_s_list : list of int
        Subject numbers.
    datatype : {"eeg", "exg", "baseline"}
        File to read.

    Returns
    -------
    X : numpy.ndarray
        ``(n_trials, n_channels, n_times)`` data, subject by subject and
        session by session.
    Y : numpy.ndarray
        ``(n_trials, 4)`` events as float (as in earlier releases). Not
        returned for ``"baseline"``, which has one epoch per session.
    """
    datatype = datatype.lower()
    sessions = [(n_s, n_b) for n_s in n_s_list for n_b in SESSIONS]
    x, y = _stack_sessions(root_dir, sessions, datatype)
    if datatype == "baseline":
        return x
    return x, y.astype(float)


def extract_condition_epochs(
    root_dir: str | Path,
    subjects: list[int],
    datatype: str = "eeg",
    condition: str = "all",
    class_label: str = "all",
    montage: str | None = "biosemi128",
) -> mne.EpochsArray:
    """
    Trials of one condition and class of several subjects, as one Epochs.

    Trials are selected from the events files first and only the selected
    trials are read, into one preallocated array. Channel information,
    sampling rate and time axis come from the ``*-epo.fif`` files, so the
    result works with any MNE method (``compute_psd``, ``compute_tfr``,
    ``average``, ...).

    Parameters
    ----------
    root_dir : str or Path
        The ``ds003626`` folder (containing ``derivatives``).
    subjects : list of int
        Subject numbers (all three sessions of each are used).
    datatype : {"eeg", "exg"}
        File to read (the baseline files hold no trials).
    condition : str
        ``"all"``, ``"pron"``, ``"inner"`` or ``"vis"`` (aliases accepted, see
        :func:`innerspeech.data_processing.filter_by_condition`).
    class_label : str
        ``"all"``, ``"up"``, ``"down"``, ``"right"`` or ``"left"``.
    montage : str or None
        Standard montage to attach (EEG only).

    Returns
    -------
    mne.EpochsArray
        The selected trials. ``epochs.metadata`` holds the subject, session,
        class and condition of every trial; the event codes are the class
        (0 = up, 1 = down, 2 = right, 3 = left) plus one.
    """
    if not subjects:
        raise ValueError("Select at least one subject.")
    if datatype.lower() not in ("eeg", "exg"):
        raise ValueError(
            f"datatype must be 'eeg' or 'exg', not {datatype!r}; the baseline files "
            "hold no trials (read them with extract_block_data_from_subject)."
        )

    template = _read_epochs(root_dir, subjects[0], 1, datatype)
    info = template.info.copy()
    if montage is not None and datatype.lower() == "eeg":
        info.set_montage(montage, on_missing="ignore")

    selection = []  # (subject, session, trial indices, events of those trials)
    for n_s in subjects:
        for n_b in SESSIONS:
            Y = load_events(root_dir, n_s, n_b)
            index, Y = filter_by_condition(np.arange(len(Y)), Y, condition)
            index, Y = filter_by_class(index, Y, class_label)
            if len(index):
                selection.append((n_s, n_b, index, Y))
    n_trials = sum(len(index) for _, _, index, _ in selection)
    if n_trials == 0:
        raise ValueError(
            f"No trials for condition={condition!r}, class={class_label!r} "
            f"in subjects {subjects}."
        )

    data = np.empty((n_trials, len(info["ch_names"]), len(template.times)))
    start = 0
    for n_s, n_b, index, _ in selection:
        epochs = _read_epochs(root_dir, n_s, n_b, datatype)
        data[start : start + len(index)] = epochs[index].get_data(verbose="WARNING")
        start += len(index)
    labels = np.concatenate([Y for _, _, _, Y in selection]).astype(int)
    subject_ids = [np.full(len(index), n_s) for n_s, _, index, _ in selection]

    class_names = ("up", "down", "right", "left")
    events = np.column_stack(
        [np.arange(len(labels)), np.zeros(len(labels), int), labels[:, 1] + 1]
    )
    event_id = {class_names[c]: c + 1 for c in np.unique(labels[:, 1])}
    metadata = pd.DataFrame(
        {
            "subject": np.concatenate(subject_ids),
            "session": labels[:, 3],
            "class": labels[:, 1],
            "condition": labels[:, 2],
        }
    )
    return mne.EpochsArray(
        data,
        info,
        events=events,
        tmin=template.tmin,
        event_id=event_id,
        metadata=metadata,
        baseline=None,
        verbose="WARNING",
    )


# ----------------------------------------------------------------------------
# Results of the analysis scripts
# ----------------------------------------------------------------------------
def tfr_path(
    tfr_dir: str | Path, cond: str, class_label: str, tfr_method: str, tfr_type: str
) -> Path:
    """
    Path of a time-frequency result written by ``TFR_representations.py``.

    Parameters
    ----------
    tfr_dir : str or Path
        Folder with the TFR results.
    cond : str
        Condition (``"all"``, ``"pron"``, ``"inner"``, ``"vis"``; aliases
        accepted).
    class_label : str
        Class (``"all"``, ``"up"``, ``"down"``, ``"right"``, ``"left"``).
    tfr_method : {"Morlet", "Multitaper"}
        Method.
    tfr_type : {"power", "itc"}
        Quantity.

    Returns
    -------
    Path
        ``<tfr_dir>/<method>_<cond>_<class>_<type>-tfr.h5``.
    """
    cond, class_label = unify_names(cond, class_label)
    return Path(tfr_dir) / f"{tfr_method}_{cond}_{class_label}_{tfr_type}-tfr.h5"


def extract_tfr(
    tfr_dir: str | Path, cond: str, class_label: str, tfr_method: str, tfr_type: str
) -> mne.time_frequency.AverageTFR:
    """
    Time-frequency result written by ``TFR_representations.py``.

    The parameters are those of :func:`tfr_path`; returns the stored power or
    ITC.
    """
    tfr = mne.time_frequency.read_tfrs(
        tfr_path(tfr_dir, cond, class_label, tfr_method, tfr_type)
    )
    # Depending on the MNE version a single TFR or a list with one is returned
    return tfr[0] if isinstance(tfr, list) else tfr


def psd_path(psd_dir: str | Path, cond: str, class_label: str) -> Path:
    """Path of a PSD result written by ``PSD_representation.py``."""
    cond, class_label = unify_names(cond, class_label)
    return Path(psd_dir) / f"PSD_{cond}_{class_label}-psd.h5"


# ----------------------------------------------------------------------------
# Participants
# ----------------------------------------------------------------------------
# Table 1 of Nieto et al. (2022), also in participants.tsv. sub-05 is 30
# (releases up to 2.1.2 stored 31 in the reports).
_AGE = (56, 50, 34, 24, 30, 29, 26, 28, 35, 31)
_GENDER = ("F", "M", "M", "F", "F", "M", "M", "F", "M", "M")


def get_age_gender(N_S: int) -> tuple[int, str]:
    """
    Age and gender of a participant (Table 1 of the paper).

    Parameters
    ----------
    N_S : int
        Subject number, 1 to 10.

    Returns
    -------
    tuple
        ``(age, gender)``, gender ``"F"`` or ``"M"``.
    """
    if not 1 <= N_S <= len(_AGE):
        raise ValueError(f"Subject number must be 1 to {len(_AGE)}, not {N_S}")
    return _AGE[N_S - 1], _GENDER[N_S - 1]
