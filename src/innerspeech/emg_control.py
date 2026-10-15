"""
Created on Thu Mar 26 16:37:48 2020

@author: Nicolás Nieto

Description:
    This code automatically tags trials by EMG artifacts

TODO:
    Add a column in the events with the EMG control information. Useful for
    further filtering the contaminated trials.
    Add 0 if the trial is not contaminated
    Add 1 if the trial is  contaminated
    The default is False.
verbose : bool, optional
    The default is False.
"""

# Imports
from pathlib import Path

import mne
import numpy as np

from innerspeech.data_processing import calculate_power_windowed
from innerspeech.derivatives_io import (
    derivative_path,
    load_events,
    load_report,
    save_report,
)


def EMG_control_single_th(
    derivatives_dir: Path,
    N_Subj_arr: list,
    N_block_arr: list,
    low_f: float,
    high_f: float,
    t_min: float,
    t_max: float,
    window_len: float,
    window_step: float,
    std_times: int | float,
    t_min_baseline: float,
    t_max_baseline: float,
    n_jobs: int | None = None,
    verbose: bool = False,
) -> None:
    """
    Parameters
    ----------
    derivatives_dir : Path
        The ``derivatives`` folder written by the pipeline (read and updated)
    N_Subj_arr : list
        array with subjects to perform the control
    N_block_arr : list
        array with block to perform the control
    low_f : float
        Low Frequency cut-off.
    high_f : float
        High Frequency cut-off.
    t_min : float
        Initial time to consider in the trials
    t_max : float
        Final time to consider in the trials
    window_len : float
        window length considered in the analysis.
    window_step : float
        step time the window moves.
    std_times : int | float
        Number of standard deviations added to the mean in the threshold method.
    t_min_baseline : float
        Initial time to consider in the Baselines
    t_max_baseline : float
        Final time to consider in the Baseline
    n_jobs : int | None, optional
        CPU cores for filtering (-1 = all). The default is None (one core).
    tag_events : bool, optional
        Add a column in the events with the EMG control information. Useful for
        further filtering the contaminated trials.
        Add 0 if the trial is not contaminated
        Add 1 if the trial is contaminated
        The default is False.
    verbose : bool, optional
        The default is False.

    Returns
    -------
    None
    """

    # Trials of Pronounced condition are excluded in the EMG control
    Pronounced_id = 0
    emg_channels = ["EXG7", "EXG8"]
    window = {"window_len": window_len, "window_step": window_step}

    for N_S in N_Subj_arr:
        for N_B in N_block_arr:
            # Baseline: EMG channels only, band-pass filtered, rectified.
            # Filtering acts on each channel separately, so picking the two EMG
            # channels first gives the same values while filtering 2 channels
            # instead of all 137.
            X_baseline = mne.read_epochs(
                derivative_path(derivatives_dir, N_S, N_B, "baseline-epo.fif"),
                verbose="WARNING",
            )
            X_baseline.pick(emg_channels).filter(low_f, high_f, n_jobs=n_jobs)
            FC = int(X_baseline.info["sfreq"])
            baseline = np.abs(X_baseline.get_data()[0])  # (2, n_times)
            del X_baseline

            # Mean and std of the windowed power over the baseline, per channel
            base_mean, base_std = calculate_power_windowed(
                baseline, FC, t_min=t_min_baseline, t_max=t_max_baseline, **window
            )
            threshold = base_mean + std_times * base_std

            # Trials: same filtering and rectification
            EMG = mne.read_epochs(
                derivative_path(derivatives_dir, N_S, N_B, "exg-epo.fif"),
                verbose="WARNING",
            )
            EMG.pick(emg_channels).filter(low_f, high_f, n_jobs=n_jobs)
            trials = np.abs(EMG.get_data())  # (n_trials, 2, n_times)
            del EMG
            Y = load_events(derivatives_dir, N_S, N_B)

            # Mean windowed power of every trial and channel, all at once
            trial_power, _ = calculate_power_windowed(
                trials, FC, t_min=t_min, t_max=t_max, **window
            )  # (n_trials, 2)

            # A trial is tagged when either channel exceeds its threshold,
            # except trials of the Pronounced condition
            tagged = (trial_power > threshold).any(axis=1) & (Y[:, 2] != Pronounced_id)
            tagged_idx = np.flatnonzero(tagged)
            if verbose:
                for n_trial in tagged_idx:
                    print("Warning at trial", n_trial + 1)

            print(
                "Tagged Trials: " + str(len(tagged_idx)),
                "for Subject " + str(N_S) + " in Session " + str(N_B),
            )

            # Update Report
            report = load_report(derivatives_dir, N_S, N_B)

            report["EMG_trials"] = tagged_idx.astype(float)
            report["Power_EXG7"] = trial_power[tagged, 0]
            report["Power_EXG8"] = trial_power[tagged, 1]

            report["Baseline_EXG7_mean"] = base_mean[0]
            report["Baseline_EXG8_mean"] = base_mean[1]

            report["Baseline_EXG7_std"] = base_std[0]
            report["Baseline_EXG8_std"] = base_std[1]

            save_report(report, derivatives_dir, N_S, N_B)

    print("EMG Control Done")
