"""
Noise level of the baseline and of the trials, per session.

For every session the script reports the median channel standard deviation of
the EEG in the baseline (15 s rest, no ICA) and in the trials (after ICA), and
the RMS of the eye (EXG3-EXG6) and mouth (EXG7-EXG8) channels in both. Sessions
whose baseline is much noisier than usual, while their trials are not, have a
contaminated baseline only.

Usage (from the repository folder, in the project environment):

    python checks/session_noise.py
    python checks/session_noise.py --data-dir /path/to/ds003626

The table is printed and saved to ``<project>/results/checks/session_noise.csv``.
"""

import argparse
import csv
from pathlib import Path

import mne
import numpy as np

from innerspeech.derivatives_io import derivative_path
from innerspeech.utils import find_project_root

HERE = Path(__file__).resolve().parent
EOG = ["EXG3", "EXG4", "EXG5", "EXG6"]
EMG = ["EXG7", "EXG8"]


def centred(x: np.ndarray) -> np.ndarray:
    """Remove the mean of every channel of every epoch."""
    return x - x.mean(axis=-1, keepdims=True)


def session_row(deriv: Path, n_s: int, n_b: int) -> dict:
    def read(kind: str) -> mne.BaseEpochs:
        path = derivative_path(deriv, n_s, n_b, kind)
        return mne.read_epochs(path, preload=True, verbose="ERROR")

    baseline, exg, eeg = (
        read("baseline-epo.fif"),
        read("exg-epo.fif"),
        read("eeg-epo.fif"),
    )
    eeg_names = [ch for ch in baseline.ch_names if not ch.startswith(("EXG", "Status"))]
    base_eeg = centred(baseline.get_data(picks=eeg_names))[0]
    trial_eeg = centred(eeg.get_data())
    base_exg = centred(baseline.get_data(picks=EOG + EMG))[0]
    trial_exg = centred(exg.get_data(picks=EOG + EMG))

    def rms(x: np.ndarray) -> float:
        return float(np.sqrt(np.mean(x**2)) * 1e6)

    return {
        "session": f"sub-{n_s:02d} ses-{n_b:02d}",
        "baseline_eeg_uV": float(np.median(base_eeg.std(axis=-1)) * 1e6),
        "trials_eeg_uV": float(np.median(trial_eeg.std(axis=-1)) * 1e6),
        "baseline_eog_uV": rms(base_exg[:4]),
        "trials_eog_uV": rms(trial_exg[:, :4]),
        "baseline_emg_uV": rms(base_exg[4:]),
        "trials_emg_uV": rms(trial_exg[:, 4:]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-dir", type=Path, default=None, help="ds003626 folder")
    args = parser.parse_args()
    project_root = find_project_root(HERE)
    deriv = (args.data_dir or project_root / "ds003626") / "derivatives"

    rows = []
    for n_s in range(1, 11):
        for n_b in range(1, 4):
            rows.append(session_row(deriv, n_s, n_b))
            print(f"\r  {rows[-1]['session']}", end="", flush=True)
    print()

    medians = {k: np.median([r[k] for r in rows]) for k in rows[0] if k != "session"}
    print("session         EEG base/trials   EOG base/trials   EMG base/trials  (uV)")
    for r in rows:
        flag = (
            "  <- baseline"
            if r["baseline_eeg_uV"] > 2 * medians["baseline_eeg_uV"]
            else ""
        )
        if r["trials_eeg_uV"] > 2 * medians["trials_eeg_uV"]:
            flag += "  <- trials"
        print(
            f"{r['session']}  {r['baseline_eeg_uV']:6.1f} / {r['trials_eeg_uV']:5.1f}"
            f"    {r['baseline_eog_uV']:6.1f} / {r['trials_eog_uV']:5.1f}"
            f"    {r['baseline_emg_uV']:6.1f} / {r['trials_emg_uV']:5.1f}{flag}"
        )
    print(
        "median          "
        + "    ".join(
            f"{medians['baseline_' + k]:6.1f} / {medians['trials_' + k]:5.1f}"
            for k in ("eeg_uV", "eog_uV", "emg_uV")
        )
    )

    out = project_root / "results" / "checks" / "session_noise.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
