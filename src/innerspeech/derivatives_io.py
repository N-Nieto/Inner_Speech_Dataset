"""
Read/write helpers for the files in the ``derivatives`` folder.

Every module that touches a derivative file goes through this module, so the
folder layout and the on-disk formats are defined in exactly one place::

    <derivatives_dir>/sub-XX/ses-YY/sub-XX_ses-YY_<kind>

Files of a session:

- ``eeg-epo.fif``, ``exg-epo.fif``, ``baseline-epo.fif``: MNE ``Epochs``.
- ``events.tsv``: one row per trial, tab-separated, ``n/a`` for missing
  values. Columns (``TRIAL_COLUMNS``):

  - ``sample``: cue onset as a sample of the raw 1024 Hz recording (first
    sample = 0), not of the 256 Hz epoch files; equals
    ``epochs.events[:, 0]`` of the matching ``.fif`` files.
  - ``onset``: the same in seconds from the start of the recording.
  - ``class``: 0 = up, 1 = down, 2 = right, 3 = left.
  - ``condition``: 0 = pronounced, 1 = inner speech, 2 = visualized.
  - ``session``: session number.
  - ``cue_inferred``: True when the cue trigger was missing and inserted by
    the event correction.
  - ``emg_power_exg7``, ``emg_power_exg8``: mean power of the band-passed,
    rectified mouth channels in the action interval (EMG control).
  - ``emg_tagged``: True when the EMG control tagged the trial (only inner
    speech and visualized trials are tagged).

- ``report.json``: session information (``Age``, ``Gender``,
  ``Recording_time``, ``Ans_R``, ``Ans_W``, ``Event_corrections``, and the
  EMG control results ``EMG_trials``, ``Power_EXG7``, ``Power_EXG8``,
  ``Baseline_EXG7_mean``, ...).

Legacy files, published up to version 2.2.0 and still written next to the new
ones (``legacy=True``) for code that reads them:

- ``events.dat``: ``(n_trials, 4)`` integer array ``[sample, class,
  condition, session]`` (Table 5 of Nieto et al., 2022). Published files are
  NumPy pickles, new ones plain ``.npy`` arrays; ``np.load(path,
  allow_pickle=True)`` reads both.
- ``report.pkl``: pickled ``dict`` with the keys of ``LEGACY_REPORT_KEYS``.

The loaders read the new files when present and fall back to the legacy ones.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

# Sampling rate of the raw recordings, the unit of the "sample" column
RAW_SFREQ = 1024

# Columns of events.dat (Table 5 of the paper)
EVENTS_COLUMNS = ("sample", "class", "condition", "session")

# Columns of events.tsv
TRIAL_COLUMNS = (
    "sample",
    "onset",
    "class",
    "condition",
    "session",
    "cue_inferred",
    "emg_power_exg7",
    "emg_power_exg8",
    "emg_tagged",
)

# Description of the events.tsv columns (BIDS sidecar, derivatives/events.json)
TRIAL_COLUMNS_JSON = {
    "sample": {
        "Description": "Cue onset as a sample of the raw 1024 Hz recording "
        "(first sample = 0), not of the 256 Hz epoch files; equals "
        "epochs.events[:, 0] of the session's -epo.fif files."
    },
    "onset": {"Description": "Cue onset from the start of the recording", "Units": "s"},
    "class": {
        "Description": "Direction shown by the cue",
        "Levels": {"0": "up", "1": "down", "2": "right", "3": "left"},
    },
    "condition": {
        "Description": "Condition the trial was performed in",
        "Levels": {
            "0": "pronounced speech",
            "1": "inner speech",
            "2": "visualized condition",
        },
    },
    "session": {"Description": "Session number"},
    "cue_inferred": {
        "Description": "True when the cue trigger was missing from the recording "
        "and inserted by the event correction (class inferred from the class "
        "balance); the trial's report lists the correction."
    },
    "emg_power_exg7": {
        "Description": "EMG control: mean power of EXG7 (band-passed, rectified) "
        "in sliding windows over the action interval",
        "Units": "V^2",
    },
    "emg_power_exg8": {
        "Description": "As emg_power_exg7, for EXG8",
        "Units": "V^2",
    },
    "emg_tagged": {
        "Description": "True when the power of EXG7 or EXG8 exceeds the baseline "
        "mean plus 3 standard deviations; pronounced speech trials are never "
        "tagged."
    },
}

# Keys of report.pkl (published files); report.json may hold more
LEGACY_REPORT_KEYS = (
    "Age",
    "Gender",
    "Recording_time",
    "Ans_R",
    "Ans_W",
    "EMG_trials",
    "Power_EXG7",
    "Power_EXG8",
    "Baseline_EXG7_mean",
    "Baseline_EXG8_mean",
    "Baseline_EXG7_std",
    "Baseline_EXG8_std",
)
# Report values returned as float arrays, whatever the file
_ARRAY_KEYS = ("EMG_trials", "Power_EXG7", "Power_EXG8")

DERIVATIVE_KINDS = (
    "eeg-epo.fif",
    "exg-epo.fif",
    "baseline-epo.fif",
    "events.tsv",
    "report.json",
    "events.dat",
    "report.pkl",
)


def subject_label(n_s: int) -> str:
    """BIDS subject label, e.g. ``1 -> "sub-01"``."""
    return f"sub-{int(n_s):02d}"


def session_label(n_b: int) -> str:
    """BIDS session label, e.g. ``1 -> "ses-01"``."""
    return f"ses-{int(n_b):02d}"


def session_dir(derivatives_dir: str | Path, n_s: int, n_b: int) -> Path:
    """Folder holding the derivative files of one subject and session."""
    return Path(derivatives_dir) / subject_label(n_s) / session_label(n_b)


def derivative_path(derivatives_dir: str | Path, n_s: int, n_b: int, kind: str) -> Path:
    """
    Path of one derivative file.

    Parameters
    ----------
    derivatives_dir : str or Path
        The ``derivatives`` folder (e.g. ``<data>/ds003626/derivatives``).
    n_s, n_b : int
        Subject and session (block) numbers, starting at 1.
    kind : str
        One of ``DERIVATIVE_KINDS`` (e.g. ``"events.tsv"``).
    """
    if kind not in DERIVATIVE_KINDS:
        raise ValueError(f"Unknown derivative kind {kind!r}; use {DERIVATIVE_KINDS}")
    stem = f"{subject_label(n_s)}_{session_label(n_b)}"
    return session_dir(derivatives_dir, n_s, n_b) / f"{stem}_{kind}"


# ----------------------------------------------------------------------
# Events
# ----------------------------------------------------------------------
def _as_events_array(events: pd.DataFrame | np.ndarray) -> np.ndarray:
    """``(n_trials, 4)`` int64 array ``[sample, class, condition, session]``."""
    if isinstance(events, pd.DataFrame):
        events = events.loc[:, list(EVENTS_COLUMNS)].to_numpy()
    array = np.asarray(events)
    if array.ndim != 2 or array.shape[1] != len(EVENTS_COLUMNS):
        raise ValueError(
            f"Events must have shape (n_trials, {len(EVENTS_COLUMNS)}) with columns "
            f"{EVENTS_COLUMNS}; got shape {array.shape}."
        )
    as_int = array.astype(np.int64)
    if not np.array_equal(as_int, array):
        raise ValueError("Events must contain integer values only.")
    return as_int


def _as_trial_table(events: pd.DataFrame | np.ndarray) -> pd.DataFrame:
    """Trial table with every column of ``TRIAL_COLUMNS`` (missing ones = NA)."""
    if isinstance(events, pd.DataFrame):
        table = events.copy()
    else:
        table = pd.DataFrame(_as_events_array(events), columns=list(EVENTS_COLUMNS))
    table["onset"] = table["sample"] / RAW_SFREQ
    for column in TRIAL_COLUMNS:
        if column not in table:
            table[column] = pd.NA
    return table.loc[:, list(TRIAL_COLUMNS)].reset_index(drop=True)


def save_events(
    events: pd.DataFrame | np.ndarray,
    derivatives_dir: str | Path,
    n_s: int,
    n_b: int,
    legacy: bool = True,
) -> Path:
    """
    Save the trials of one session.

    Parameters
    ----------
    events : pandas.DataFrame or numpy.ndarray
        Trial table (columns of ``TRIAL_COLUMNS``; at least ``sample``,
        ``class``, ``condition`` and ``session``) or an ``(n_trials, 4)``
        array with those four columns.
    derivatives_dir : str or Path
        The ``derivatives`` folder.
    n_s, n_b : int
        Subject and session numbers.
    legacy : bool
        Also write ``events.dat``.

    Returns
    -------
    Path
        Path of ``events.tsv``.
    """
    table = _as_trial_table(events)
    path = derivative_path(derivatives_dir, n_s, n_b, "events.tsv")
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, sep="\t", index=False, na_rep="n/a")  # floats round-trip
    if legacy:
        dat = derivative_path(derivatives_dir, n_s, n_b, "events.dat")
        # Write through a file handle so np.save keeps the ".dat" name
        with dat.open("wb") as f:
            np.save(f, _as_events_array(table), allow_pickle=False)
    return path


def load_events_table(derivatives_dir: str | Path, n_s: int, n_b: int) -> pd.DataFrame:
    """
    Trial table of one session (``TRIAL_COLUMNS``).

    Reads ``events.tsv``; for legacy derivatives, builds the table from
    ``events.dat`` and the EMG results of the report (powers are then known
    for the tagged trials only, ``cue_inferred`` is NA).
    """
    path = derivative_path(derivatives_dir, n_s, n_b, "events.tsv")
    if path.exists():
        table = pd.read_csv(
            path,
            sep="\t",
            na_values="n/a",
            keep_default_na=False,
            float_precision="round_trip",
        )
        for column in ("cue_inferred", "emg_tagged"):
            table[column] = table[column].astype("boolean")
        return table
    path = derivative_path(derivatives_dir, n_s, n_b, "events.dat")
    table = _as_trial_table(np.load(path, allow_pickle=True))
    try:
        report = load_report(derivatives_dir, n_s, n_b)
    except FileNotFoundError:
        return table
    if "EMG_trials" in report:
        tagged = np.asarray(report["EMG_trials"], dtype=int)
        table["emg_tagged"] = False
        table.loc[tagged, "emg_tagged"] = True
        table.loc[tagged, "emg_power_exg7"] = report["Power_EXG7"]
        table.loc[tagged, "emg_power_exg8"] = report["Power_EXG8"]
    return table


def load_events(derivatives_dir: str | Path, n_s: int, n_b: int) -> np.ndarray:
    """
    Trials of one session as an ``(n_trials, 4)`` int64 array with the
    columns ``[sample, class, condition, session]``.

    Reads ``events.tsv`` when present, otherwise ``events.dat`` (published
    pickled files or ``.npy`` files written by ``save_events``).
    """
    path = derivative_path(derivatives_dir, n_s, n_b, "events.tsv")
    if path.exists():
        table = pd.read_csv(path, sep="\t", usecols=list(EVENTS_COLUMNS))
        return _as_events_array(table)
    path = derivative_path(derivatives_dir, n_s, n_b, "events.dat")
    return _as_events_array(np.load(path, allow_pickle=True))


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------
def _to_json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot write {type(value).__name__} to JSON")


def save_report(
    report: dict,
    derivatives_dir: str | Path,
    n_s: int,
    n_b: int,
    legacy: bool = True,
) -> Path:
    """
    Save the report of one session as ``report.json``.

    With ``legacy=True`` the keys of ``LEGACY_REPORT_KEYS`` are also written
    to ``report.pkl``. Returns the path of ``report.json``.
    """
    path = derivative_path(derivatives_dir, n_s, n_b, "report.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, default=_to_json) + "\n", "utf-8")
    if legacy:
        legacy_report = {k: v for k, v in report.items() if k in LEGACY_REPORT_KEYS}
        with derivative_path(derivatives_dir, n_s, n_b, "report.pkl").open("wb") as f:
            pickle.dump(legacy_report, f, pickle.HIGHEST_PROTOCOL)
    return path


def load_report(derivatives_dir: str | Path, n_s: int, n_b: int) -> dict:
    """
    Report of one session.

    Reads ``report.json`` when present, otherwise ``report.pkl``. The EMG
    trial lists (``EMG_trials``, ``Power_EXG7``, ``Power_EXG8``) are returned
    as float arrays in both cases.
    """
    path = derivative_path(derivatives_dir, n_s, n_b, "report.json")
    if path.exists():
        report = json.loads(path.read_text("utf-8"))
    else:
        with derivative_path(derivatives_dir, n_s, n_b, "report.pkl").open("rb") as f:
            report = pickle.load(f)
    for key in _ARRAY_KEYS:
        if key in report:
            report[key] = np.asarray(report[key], dtype=float)
    return report
