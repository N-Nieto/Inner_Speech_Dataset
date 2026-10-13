"""
Read/write helpers for the files in the ``derivatives`` folder.

Every module that touches a derivative file goes through this module, so the
folder layout and the on-disk formats are defined in exactly one place::

    <derivatives_dir>/sub-XX/ses-YY/sub-XX_ses-YY_<kind>

Formats (as published on OpenNeuro, ds003626):

- ``events.dat``: integer array of shape ``(n_trials, 4)`` with the columns
  ``[sample, class, condition, session]`` (Table 5 of Nieto et al., 2022).
  The published files are NumPy pickles; new files are written in NumPy's
  ``.npy`` container (no pickle). Both are read by
  ``np.load(path, allow_pickle=True)``, the loader used since the original
  release, so old and new files are interchangeable.
- ``report.pkl``: pickled ``dict``.
- ``*-epo.fif``: MNE ``Epochs``.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

# Column order of the events file (Table 5 of the paper)
EVENTS_COLUMNS = ("sample", "class", "condition", "session")

# Columns of the events DataFrame built by InnerSpeech_preprocessing.py
_PIPELINE_COLUMNS = ("Time", "Code", "condition", "block")

DERIVATIVE_KINDS = (
    "eeg-epo.fif",
    "exg-epo.fif",
    "baseline-epo.fif",
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
        One of ``DERIVATIVE_KINDS`` (e.g. ``"events.dat"``).
    """
    if kind not in DERIVATIVE_KINDS:
        raise ValueError(f"Unknown derivative kind {kind!r}; use {DERIVATIVE_KINDS}")
    stem = f"{subject_label(n_s)}_{session_label(n_b)}"
    return session_dir(derivatives_dir, n_s, n_b) / f"{stem}_{kind}"


# ----------------------------------------------------------------------
# Events
# ----------------------------------------------------------------------
def _as_events_array(events: pd.DataFrame | np.ndarray) -> np.ndarray:
    """Convert pipeline events to the published ``(n, 4)`` int64 array."""
    if isinstance(events, pd.DataFrame):
        if set(_PIPELINE_COLUMNS).issubset(events.columns):
            events = events.loc[:, list(_PIPELINE_COLUMNS)]
        elif set(EVENTS_COLUMNS).issubset(events.columns):
            events = events.loc[:, list(EVENTS_COLUMNS)]
        events = events.to_numpy()

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


def save_events(
    events: pd.DataFrame | np.ndarray,
    derivatives_dir: str | Path,
    n_s: int,
    n_b: int,
) -> Path:
    """
    Save the events of one session in the published layout.

    ``events`` is either the pipeline DataFrame (columns ``Time``, ``Code``,
    ``condition``, ``block``) or an ``(n_trials, 4)`` array. Returns the path.
    """
    array = _as_events_array(events)
    path = derivative_path(derivatives_dir, n_s, n_b, "events.dat")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write through a file handle so np.save keeps the ".dat" name
    with path.open("wb") as f:
        np.save(f, array, allow_pickle=False)
    return path


def load_events(derivatives_dir: str | Path, n_s: int, n_b: int) -> np.ndarray:
    """
    Load the events of one session as an ``(n_trials, 4)`` int64 array with
    columns ``[sample, class, condition, session]``.

    Reads both the published (pickled) files and files written by
    ``save_events``.
    """
    path = derivative_path(derivatives_dir, n_s, n_b, "events.dat")
    return _as_events_array(np.load(path, allow_pickle=True))


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------
def save_report(report: dict, derivatives_dir: str | Path, n_s: int, n_b: int) -> Path:
    """Save the report ``dict`` of one session. Returns the path."""
    path = derivative_path(derivatives_dir, n_s, n_b, "report.pkl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as output:
        pickle.dump(report, output, pickle.HIGHEST_PROTOCOL)
    return path


def load_report(derivatives_dir: str | Path, n_s: int, n_b: int) -> dict:
    """Load the report ``dict`` of one session."""
    path = derivative_path(derivatives_dir, n_s, n_b, "report.pkl")
    with path.open("rb") as input_file:
        return pickle.load(input_file)
