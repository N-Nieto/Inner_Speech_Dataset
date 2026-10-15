"""End-to-end run of InnerSpeech_preprocessing.py on a synthetic recording."""

import mne
import numpy as np

from innerspeech.derivatives_io import derivative_path, load_events, load_report

N_EEG, N_TRIALS = 8, 200


def read(deriv, kind):
    return mne.read_epochs(derivative_path(deriv, 3, 1, kind), preload=True)


def test_all_files_written(pipeline_output):
    for kind in (
        "eeg-epo.fif",
        "exg-epo.fif",
        "baseline-epo.fif",
        "events.dat",
        "report.pkl",
    ):
        assert derivative_path(pipeline_output, 3, 1, kind).exists(), kind


def test_epoch_files(pipeline_output):
    eeg, exg = (
        read(pipeline_output, "eeg-epo.fif"),
        read(pipeline_output, "exg-epo.fif"),
    )
    events = load_events(pipeline_output, 3, 1)
    assert eeg.get_data().shape == (N_TRIALS, N_EEG, 1153)
    assert exg.ch_names == [f"EXG{i}" for i in range(1, 9)]
    for epochs in (eeg, exg):
        assert epochs.info["sfreq"] == 256
        assert np.isclose(epochs.tmin, -0.5) and np.isclose(epochs.tmax, 4)
        assert np.array_equal(epochs.events[:, 0], events[:, 0])
        assert np.array_equal(epochs.events[:, 2] - 31, events[:, 1])
    # Re-referenced to the mean of EXG1 and EXG2
    assert np.abs(exg.get_data(picks=["EXG1", "EXG2"]).sum(axis=1)).max() < 1e-12


def test_baseline_has_no_trigger_channel(pipeline_output):
    baseline = read(pipeline_output, "baseline-epo.fif")
    assert "Status" not in baseline.ch_names
    assert len(baseline.ch_names) == N_EEG + 8
    assert baseline.get_data().shape[-1] == 15 * 256 + 1


def test_events_and_ad_hoc_correction(pipeline_output):
    events = load_events(pipeline_output, 3, 1)
    assert events.shape == (N_TRIALS, 4)
    # sub-03 ses-01: trials 80-119 relabelled as visualized condition
    assert np.bincount(events[:, 2]).tolist() == [40, 40, 120]
    assert (events[80:120, 2] == 2).all()


def test_report(pipeline_output):
    report = load_report(pipeline_output, 3, 1)
    assert report["Age"] == 34 and report["Gender"] == "M"
    assert (report["Ans_R"], report["Ans_W"]) == (20, 0)
    for key in ("EMG_trials", "Power_EXG7", "Power_EXG8", "Baseline_EXG7_mean"):
        assert key in report
