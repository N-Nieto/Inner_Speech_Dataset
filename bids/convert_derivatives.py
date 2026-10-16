"""
Add ``events.tsv`` and ``report.json`` to the published derivatives (ds003626
2.2.0), after checking that the current code reproduces the published files.

For every session the script

1. rebuilds the events from the raw ``.bdf`` file with the current event
   correction (:func:`innerspeech.events_analysis.process_session_events`) and
   compares the trials with the published ``events.dat`` and the recording
   time and answers with the published ``report.pkl``;
2. recomputes the EMG control from the published ``exg-epo.fif`` and
   ``baseline-epo.fif`` (parameters of the paper) and compares the tagged
   trials, their powers and the baseline statistics with ``report.pkl``;
3. if everything matches, writes ``events.tsv`` (trial table with the EMG
   power of every trial) and ``report.json`` (the published report plus the
   list of event corrections). ``events.dat``, ``report.pkl`` and the epoch
   files are not modified.

Sessions that differ are reported and left unchanged.

Usage (from the repository folder, in the project environment):

    python bids/convert_derivatives.py --dry-run     # compare only
    python bids/convert_derivatives.py               # compare and write
    python bids/convert_derivatives.py --data-dir /path/to/ds003626

A summary is printed and saved to
``<project>/results/checks/convert_derivatives.json``. The exit code is 1 if
any session differs.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import mne
import numpy as np

from innerspeech.derivatives_io import (
    EVENTS_COLUMNS,
    RAW_SFREQ,
    _as_events_array,
    derivative_path,
    save_events,
    save_report,
)
from innerspeech.emg_control import emg_control_session
from innerspeech.events_analysis import process_session_events
from innerspeech.utils import find_project_root

HERE = Path(__file__).resolve().parent

# EMG control parameters of the published derivatives (InnerSpeech_preprocessing.py)
EMG_PARAMS = {
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
RTOL = 1e-6  # relative tolerance for the EMG powers (other MNE/SciPy versions)


def published(deriv: Path, n_s: int, n_b: int) -> tuple[np.ndarray, dict]:
    """``events.dat`` and ``report.pkl`` as published (ignoring new files)."""
    events = np.load(derivative_path(deriv, n_s, n_b, "events.dat"), allow_pickle=True)
    with derivative_path(deriv, n_s, n_b, "report.pkl").open("rb") as f:
        report = pickle.load(f)
    return _as_events_array(events), report


def close(a, b) -> bool:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return a.shape == b.shape and np.allclose(a, b, rtol=RTOL, atol=0)


def convert_session(
    data_dir: Path, n_s: int, n_b: int, n_jobs: int | None
) -> tuple[dict, dict | None]:
    """Checks of one session and, if they pass, the files to write."""
    deriv = data_dir / "derivatives"
    sub, ses = f"sub-{n_s:02d}", f"ses-{n_b:02d}"
    bdf = data_dir / sub / ses / "eeg" / f"{sub}_{ses}_task-innerspeech_eeg.bdf"
    raw = mne.io.read_raw_bdf(bdf, preload=False, verbose="ERROR")
    _, trials, rebuilt = process_session_events(raw, n_s, n_b)
    pub_events, pub_report = published(deriv, n_s, n_b)

    problems = []
    new_events = _as_events_array(trials[list(EVENTS_COLUMNS)])
    if new_events.shape != pub_events.shape:
        problems.append(
            f"{len(new_events)} trials rebuilt, {len(pub_events)} published"
        )
    elif not np.array_equal(new_events, pub_events):
        rows = np.flatnonzero((new_events != pub_events).any(axis=1))
        cols = [
            c
            for k, c in enumerate(EVENTS_COLUMNS)
            if (new_events[:, k] != pub_events[:, k]).any()
        ]
        problems.append(
            f"{len(rows)} trials differ in {cols} (first rows {rows[:5].tolist()})"
        )
    for key in ("Recording_time", "Ans_R", "Ans_W"):
        if rebuilt[key] != pub_report.get(key):
            problems.append(
                f"{key}: rebuilt {rebuilt[key]}, published {pub_report.get(key)}"
            )

    emg = None
    if not problems:  # the EMG control reads the conditions of the trials
        emg = emg_control_session(deriv, n_s, n_b, n_jobs=n_jobs, **EMG_PARAMS)
        tagged = np.flatnonzero(emg["tagged"])
        if tagged.tolist() != np.asarray(pub_report["EMG_trials"], int).tolist():
            problems.append(
                f"EMG tagged trials: {tagged.tolist()} rebuilt, "
                f"{np.asarray(pub_report['EMG_trials'], int).tolist()} published"
            )
        else:
            for k, ch in enumerate(("EXG7", "EXG8")):
                if not close(emg["power"][tagged, k], pub_report[f"Power_{ch}"]):
                    problems.append(f"Power_{ch} differs")
                for stat in ("mean", "std"):
                    key = f"Baseline_{ch}_{stat}"
                    if not close(emg[f"baseline_{stat}"][k], pub_report[key]):
                        problems.append(f"{key} differs")

    corrections = [c for c in rebuilt["Event_corrections"] if c["action"] != "ignored"]
    summary = {
        "session": f"{sub} {ses}",
        "status": "differs" if problems else "ok",
        "problems": problems,
        "n_trials": len(trials),
        "corrections": [
            f"{c['action']} {c['code']} at {c['sample']} ({c['reason']})"
            for c in corrections
        ],
    }
    if emg is None:
        return summary, None

    table = trials.copy()
    table["onset"] = table["sample"] / RAW_SFREQ
    table["emg_power_exg7"] = emg["power"][:, 0]
    table["emg_power_exg8"] = emg["power"][:, 1]
    table["emg_tagged"] = emg["tagged"]
    report = dict(pub_report)  # published values, unchanged
    report["Event_corrections"] = rebuilt["Event_corrections"]
    if "Known_issue" in rebuilt:
        report["Known_issue"] = rebuilt["Known_issue"]
    return summary, {"events": table, "report": report}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-dir", type=Path, default=None, help="ds003626 folder")
    parser.add_argument("--subjects", type=int, nargs="+", default=list(range(1, 11)))
    parser.add_argument("--sessions", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--dry-run", action="store_true", help="compare only")
    parser.add_argument("--n-jobs", type=int, default=-1, help="cores for filtering")
    parser.add_argument(
        "--overwrite", action="store_true", help="replace existing events.tsv/.json"
    )
    args = parser.parse_args()

    project_root = find_project_root(HERE)
    data_dir = args.data_dir or project_root / "ds003626"
    deriv = data_dir / "derivatives"
    mne.set_log_level("WARNING")

    rows, failed = [], False
    for n_s in args.subjects:
        for n_b in args.sessions:
            tag = f"sub-{n_s:02d} ses-{n_b:02d}"
            print(f"{tag} ...", end=" ", flush=True)
            try:
                summary, files = convert_session(data_dir, n_s, n_b, args.n_jobs)
            except Exception as err:  # report and continue
                summary, files = (
                    {"session": tag, "status": "error", "problems": [repr(err)]},
                    None,
                )
            ok = summary["status"] == "ok"
            failed |= not ok
            written = False
            targets = [
                derivative_path(deriv, n_s, n_b, k)
                for k in ("events.tsv", "report.json")
            ]
            exists = any(p.exists() for p in targets)
            if files and ok and not args.dry_run:
                if exists and not args.overwrite:
                    summary["note"] = "events.tsv/report.json exist (use --overwrite)"
                else:
                    save_events(files["events"], deriv, n_s, n_b, legacy=False)
                    save_report(files["report"], deriv, n_s, n_b, legacy=False)
                    written = True
            summary["written"] = written
            rows.append(summary)
            print(summary["status"], "(written)" if written else "")
            for line in summary["problems"]:
                print("    problem:", line)
            for line in summary.get("corrections", []):
                print("    correction:", line)

    n_ok = sum(r["status"] == "ok" for r in rows)
    print(
        f"\n{n_ok}/{len(rows)} sessions reproduced; "
        f"{sum(r['written'] for r in rows)} written"
    )
    out = project_root / "results" / "checks" / "convert_derivatives.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1, default=str))
    print(f"Saved {out}")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
