"""EMG control: trials with mouth activity are tagged, pronounced ones are not."""

import shutil

import mne
import numpy as np

from innerspeech.derivatives_io import derivative_path, load_events, load_report
from innerspeech.emg_control import EMG_control_single_th

PARAMS = {
    "low_f": 1,
    "high_f": 20,
    "t_min": 1,
    "t_max": 3.5,
    "window_len": 0.5,
    "window_step": 0.05,
    "std_times": 3,
    "t_min_baseline": 0,
    "t_max_baseline": 15,
}


def test_tags_only_non_pronounced_trials_with_emg(derivatives, tmp_path):
    deriv = tmp_path / "derivatives"
    shutil.copytree(derivatives / "derivatives", deriv)
    events = load_events(deriv, 1, 1)
    inner = np.flatnonzero(events[:, 2] == 1)[:2]
    pronounced = np.flatnonzero(events[:, 2] == 0)[:1]

    path = derivative_path(deriv, 1, 1, "exg-epo.fif")
    exg = mne.read_epochs(path, preload=True)
    t = exg.times
    burst = 200e-6 * np.sin(2 * np.pi * 10 * t) * ((t > 1) & (t < 2.5))
    for trial in (*inner, *pronounced):
        exg._data[trial, exg.ch_names.index("EXG7")] += burst
    exg.save(path, overwrite=True)

    EMG_control_single_th(
        derivatives_dir=deriv, N_Subj_arr=[1], N_block_arr=[1], **PARAMS
    )
    report = load_report(deriv, 1, 1)
    assert report["EMG_trials"].tolist() == sorted(float(i) for i in inner)
    assert len(report["Power_EXG7"]) == len(report["Power_EXG8"]) == 2
    assert report["Baseline_EXG7_std"] > 0
