"""Reading and writing the derivative files."""

import json
import pickle

import numpy as np
import pandas as pd

from innerspeech.derivatives_io import (
    LEGACY_REPORT_KEYS,
    TRIAL_COLUMNS,
    derivative_path,
    load_events,
    load_events_table,
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
    assert path.name == "sub-01_ses-01_events.tsv"
    loaded = load_events(tmp_path, 1, 1)
    assert loaded.dtype == np.int64 and np.array_equal(loaded, events)
    dat = derivative_path(tmp_path, 1, 1, "events.dat")
    assert np.array_equal(np.load(dat, allow_pickle=False), events)  # plain .npy


def test_trial_table_roundtrip(tmp_path):
    table = pd.DataFrame(
        {
            "sample": [1024, 9000],
            "class": [0, 3],
            "condition": [1, 2],
            "session": [1, 1],
            "cue_inferred": [False, True],
            "emg_power_exg7": [1.5e-11, 2.25e-11],
            "emg_power_exg8": [3e-12, 4e-12],
            "emg_tagged": [False, True],
        }
    )
    path = save_events(table, tmp_path, 1, 1, legacy=False)
    assert not derivative_path(tmp_path, 1, 1, "events.dat").exists()
    text = path.read_text().splitlines()
    assert text[0].split("\t") == list(TRIAL_COLUMNS)
    loaded = load_events_table(tmp_path, 1, 1)
    assert loaded["onset"].tolist() == [1.0, 9000 / 1024]
    assert loaded["cue_inferred"].tolist() == [False, True]
    for column in ("emg_power_exg7", "emg_power_exg8"):
        assert np.array_equal(loaded[column], table[column])


def test_missing_values_are_na(tmp_path):
    save_events(np.array([[1024, 0, 1, 1]]), tmp_path, 1, 1)
    path = derivative_path(tmp_path, 1, 1, "events.tsv")
    assert path.read_text().splitlines()[1].endswith("n/a\tn/a\tn/a\tn/a")
    table = load_events_table(tmp_path, 1, 1)
    assert table["emg_tagged"].isna().all()


def test_reads_published_pickled_events(tmp_path):
    """Files up to 2.1.2 hold a pickled DataFrame; they must still load."""
    frame = pd.DataFrame([[1024, 0, 1, 2], [9000, 3, 2, 2]])
    path = derivative_path(tmp_path, 2, 2, "events.dat")
    path.parent.mkdir(parents=True)
    with path.open("wb") as f:
        np.save(f, frame, allow_pickle=True)
    assert np.array_equal(load_events(tmp_path, 2, 2), frame.to_numpy())


def test_legacy_files_give_the_trial_table(tmp_path):
    """Without events.tsv the table comes from events.dat and report.pkl."""
    events = np.array([[1024, 0, 1, 1], [5000, 1, 1, 1], [9000, 3, 2, 1]])
    path = derivative_path(tmp_path, 1, 1, "events.dat")
    path.parent.mkdir(parents=True)
    with path.open("wb") as f:
        np.save(f, events)
    report = {"Age": 30, "EMG_trials": [1.0], "Power_EXG7": [2.0], "Power_EXG8": [3.0]}
    with derivative_path(tmp_path, 1, 1, "report.pkl").open("wb") as f:
        pickle.dump(report, f)
    table = load_events_table(tmp_path, 1, 1)
    assert table["emg_tagged"].tolist() == [False, True, False]
    assert table.loc[1, "emg_power_exg7"] == 2.0
    assert table["cue_inferred"].isna().all()


def test_report_roundtrip(tmp_path):
    report = {
        "Age": np.int64(30),
        "Gender": "F",
        "EMG_trials": np.array([3.0, 7.0]),
        "Baseline_EXG7_mean": np.float64(1e-11),
        "Event_corrections": [{"sample": 5, "code": 44, "action": "inserted"}],
    }
    path = save_report(report, tmp_path, 5, 1)
    assert json.loads(path.read_text())["Age"] == 30
    loaded = load_report(tmp_path, 5, 1)
    assert loaded["Age"] == 30 and np.array_equal(loaded["EMG_trials"], [3.0, 7.0])
    assert loaded["Event_corrections"] == report["Event_corrections"]
    # report.pkl keeps the keys of the published files only
    with derivative_path(tmp_path, 5, 1, "report.pkl").open("rb") as f:
        legacy = pickle.load(f)
    assert set(legacy) <= set(LEGACY_REPORT_KEYS)
    assert "Event_corrections" not in legacy
