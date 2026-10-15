"""Reading and writing the derivative files."""

import numpy as np
import pandas as pd

from innerspeech.derivatives_io import (
    derivative_path,
    load_events,
    load_report,
    save_events,
    save_report,
)


def test_layout(tmp_path):
    path = derivative_path(tmp_path, 3, 1, "eeg-epo.fif")
    assert path == tmp_path / "sub-03" / "ses-01" / "sub-03_ses-01_eeg-epo.fif"


def test_events_roundtrip(tmp_path):
    events = np.array([[1024, 0, 1, 1], [9000, 3, 2, 1]])
    path = save_events(events, tmp_path, 1, 1)
    loaded = load_events(tmp_path, 1, 1)
    assert loaded.dtype == np.int64 and np.array_equal(loaded, events)
    assert np.array_equal(np.load(path, allow_pickle=False), events)  # plain .npy


def test_reads_published_pickled_events(tmp_path):
    """Files up to 2.1.2 hold a pickled DataFrame; they must still load."""
    frame = pd.DataFrame([[1024, 0, 1, 2], [9000, 3, 2, 2]])
    path = derivative_path(tmp_path, 2, 2, "events.dat")
    path.parent.mkdir(parents=True)
    with path.open("wb") as f:
        np.save(f, frame, allow_pickle=True)
    assert np.array_equal(load_events(tmp_path, 2, 2), frame.to_numpy())


def test_report_roundtrip(tmp_path):
    report = {"Age": 30, "Gender": "F", "EMG_trials": np.array([3.0, 7.0])}
    save_report(report, tmp_path, 5, 1)
    loaded = load_report(tmp_path, 5, 1)
    assert loaded["Age"] == 30 and np.array_equal(loaded["EMG_trials"], [3.0, 7.0])
