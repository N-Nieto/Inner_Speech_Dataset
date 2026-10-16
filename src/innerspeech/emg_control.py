"""
EMG control: tag trials with mouth movements (single threshold method).

The mouth channels EXG7 and EXG8 are band-pass filtered and rectified. The
power in sliding windows over the session's baseline gives, per channel, a
threshold ``mean + std_times * std``. A trial is tagged when the mean windowed
power of either channel in the action interval exceeds its threshold; trials
of the pronounced speech condition are never tagged (Nieto et al., 2022).

@author: Nicolás Nieto
"""

from pathlib import Path

import mne
import numpy as np

from innerspeech.data_processing import calculate_power_windowed
from innerspeech.derivatives_io import (
    derivative_path,
    load_events_table,
    load_report,
    save_events,
    save_report,
)

EMG_CHANNELS = ["EXG7", "EXG8"]
PRONOUNCED = 0  # condition number of pronounced speech


def emg_control_session(
    derivatives_dir: Path,
    n_s: int,
    n_b: int,
    low_f: float,
    high_f: float,
    t_min: float,
    t_max: float,
    window_len: float,
    window_step: float,
    std_times: float,
    t_min_baseline: float,
    t_max_baseline: float,
    n_jobs: int | None = None,
) -> dict:
    """
    EMG control of one session, without writing anything.

    Parameters
    ----------
    derivatives_dir : Path
        The ``derivatives`` folder (``exg-epo.fif``, ``baseline-epo.fif`` and
        the events of the session are read).
    n_s, n_b : int
        Subject and session numbers.
    low_f, high_f : float
        Band-pass filter of the mouth channels (Hz).
    t_min, t_max : float
        Window of the trials, in seconds from the first sample of the epoch.
    window_len, window_step : float
        Length and step of the sliding windows (s).
    std_times : float
        Standard deviations above the baseline mean for the threshold.
    t_min_baseline, t_max_baseline : float
        Window of the baseline (s from its first sample).
    n_jobs : int or None
        CPU cores for filtering (-1 = all).

    Returns
    -------
    dict
        ``power``: ``(n_trials, 2)`` mean power of EXG7 and EXG8 per trial;
        ``tagged``: boolean ``(n_trials,)``; ``baseline_mean`` and
        ``baseline_std``: per channel; ``threshold``: per channel.
    """
    window = {"window_len": window_len, "window_step": window_step}

    # Filtering acts on each channel separately, so picking the two mouth
    # channels first gives the same values as filtering every channel.
    baseline = mne.read_epochs(
        derivative_path(derivatives_dir, n_s, n_b, "baseline-epo.fif"),
        verbose="WARNING",
    )
    baseline.pick(EMG_CHANNELS).filter(low_f, high_f, n_jobs=n_jobs, verbose="WARNING")
    sfreq = int(baseline.info["sfreq"])
    base_mean, base_std = calculate_power_windowed(
        np.abs(baseline.get_data()[0]),
        sfreq,
        t_min=t_min_baseline,
        t_max=t_max_baseline,
        **window,
    )
    threshold = base_mean + std_times * base_std

    trials = mne.read_epochs(
        derivative_path(derivatives_dir, n_s, n_b, "exg-epo.fif"), verbose="WARNING"
    )
    trials.pick(EMG_CHANNELS).filter(low_f, high_f, n_jobs=n_jobs, verbose="WARNING")
    power, _ = calculate_power_windowed(
        np.abs(trials.get_data()), sfreq, t_min=t_min, t_max=t_max, **window
    )  # (n_trials, 2)

    condition = load_events_table(derivatives_dir, n_s, n_b)["condition"].to_numpy()
    tagged = (power > threshold).any(axis=1) & (condition != PRONOUNCED)
    return {
        "power": power,
        "tagged": tagged,
        "baseline_mean": base_mean,
        "baseline_std": base_std,
        "threshold": threshold,
    }


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
    std_times: float,
    t_min_baseline: float,
    t_max_baseline: float,
    n_jobs: int | None = None,
    legacy: bool = True,
    verbose: bool = False,
) -> None:
    """
    Run the EMG control and store its results with the derivatives.

    For every session, the trial table (``events.tsv``) gets the columns
    ``emg_power_exg7``, ``emg_power_exg8`` and ``emg_tagged``, and the report
    the keys ``EMG_trials``, ``Power_EXG7``, ``Power_EXG8`` (tagged trials)
    and ``Baseline_EXG7_mean``, ``Baseline_EXG8_mean``, ``Baseline_EXG7_std``,
    ``Baseline_EXG8_std``.

    Parameters
    ----------
    derivatives_dir : Path
        The ``derivatives`` folder written by the pipeline (read and updated).
    N_Subj_arr, N_block_arr : list of int
        Subjects and sessions to process.
    low_f, high_f, t_min, t_max, window_len, window_step, std_times, \
t_min_baseline, t_max_baseline, n_jobs
        See :func:`emg_control_session`.
    legacy : bool
        Also update ``report.pkl``.
    verbose : bool
        Print the tagged trials.
    """
    for n_s in N_Subj_arr:
        for n_b in N_block_arr:
            result = emg_control_session(
                derivatives_dir,
                n_s,
                n_b,
                low_f=low_f,
                high_f=high_f,
                t_min=t_min,
                t_max=t_max,
                window_len=window_len,
                window_step=window_step,
                std_times=std_times,
                t_min_baseline=t_min_baseline,
                t_max_baseline=t_max_baseline,
                n_jobs=n_jobs,
            )
            power, tagged = result["power"], result["tagged"]
            tagged_idx = np.flatnonzero(tagged)
            if verbose:
                for n_trial in tagged_idx:
                    print("Warning at trial", n_trial + 1)
            print(
                f"Tagged Trials: {len(tagged_idx)} for Subject {n_s} in Session {n_b}"
            )

            table = load_events_table(derivatives_dir, n_s, n_b)
            table["emg_power_exg7"] = power[:, 0]
            table["emg_power_exg8"] = power[:, 1]
            table["emg_tagged"] = tagged
            save_events(table, derivatives_dir, n_s, n_b, legacy=False)

            report = load_report(derivatives_dir, n_s, n_b)
            report["EMG_trials"] = tagged_idx.astype(float)
            report["Power_EXG7"] = power[tagged, 0]
            report["Power_EXG8"] = power[tagged, 1]
            report["Baseline_EXG7_mean"] = result["baseline_mean"][0]
            report["Baseline_EXG8_mean"] = result["baseline_mean"][1]
            report["Baseline_EXG7_std"] = result["baseline_std"][0]
            report["Baseline_EXG8_std"] = result["baseline_std"][1]
            save_report(report, derivatives_dir, n_s, n_b, legacy=legacy)

    print("EMG Control Done")
