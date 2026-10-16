"""
Re-run InnerSpeech_preprocessing.py on one session's raw data and compare the
result with the published derivatives.

The preprocessing script is executed as it is in the repository, except for
the subject/session lists, the output folder (the published derivatives are
never touched) and, with ``--no-ica``, ICA_BOOL. The new files are written to
``<project>/results/checks/rerun[_no_ica]/derivatives``.

Usage (from the repository folder, in the project environment):

    python checks/reproduce_session.py --subject 8 --session 3            # hours (ICA)
    python checks/reproduce_session.py --subject 8 --session 3 --no-ica   # minutes

Without ICA every file except ``eeg-epo.fif`` should match the published one.

For every file the maximum absolute difference is given relative to the
standard deviation of the published data (0 = identical; ~1 = unrelated
signals), plus the median channel-wise correlation. A summary is printed and
saved next to the new files as ``comparison_sub-XX_ses-YY.json``.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import mne
import numpy as np

from innerspeech.derivatives_io import derivative_path, load_events, load_report
from innerspeech.utils import find_project_root

HERE = Path(__file__).resolve().parent
SCRIPT = "InnerSpeech_preprocessing.py"


def run_pipeline(n_s: int, n_b: int, data_dir: Path, save_dir: Path, ica: bool) -> None:
    script = HERE.parent / "Python_Processing" / SCRIPT
    src = script.read_text(encoding="utf-8")
    overrides = {
        "N_Subj_arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]": f"N_Subj_arr = [{n_s}]",
        "N_block_arr = [1, 2, 3]": f"N_block_arr = [{n_b}]",
        'data_dir = project_root / "ds003626"': f"data_dir = Path({str(data_dir)!r})",
        'save_dir = data_dir / "derivatives"': f"save_dir = Path({str(save_dir)!r})",
    }
    for old, new in overrides.items():
        if old not in src:
            raise RuntimeError(f"{SCRIPT} changed: could not find {old!r}")
        src = src.replace(old, new)
    src, n = re.subn(r"^ICA_BOOL = \w+", f"ICA_BOOL = {ica}", src, flags=re.MULTILINE)
    if n != 1:
        raise RuntimeError(f"{SCRIPT} changed: could not find ICA_BOOL")
    exec(
        compile(src, str(script), "exec"),
        {"__name__": "__main__", "__file__": str(script)},
    )


def compare_epochs(new_path: Path, pub_path: Path) -> dict:
    try:
        pub = mne.read_epochs(pub_path, preload=True, verbose="ERROR")
    except Exception as err:
        return {"status": f"published file unreadable ({type(err).__name__})"}
    new = mne.read_epochs(new_path, preload=True, verbose="ERROR")
    out = {
        "n_epochs": [len(new), len(pub)],
        "n_channels": [len(new.ch_names), len(pub.ch_names)],
    }
    if new.get_data(copy=False).shape != pub.get_data(copy=False).shape:
        out["status"] = "different shape"
        return out
    a, b = new.get_data(copy=False), pub.get_data(copy=False)
    out["max_abs_diff_over_std"] = float(np.abs(a - b).max() / b.std())
    a2 = a.transpose(1, 0, 2).reshape(a.shape[1], -1)
    b2 = b.transpose(1, 0, 2).reshape(b.shape[1], -1)
    a2 = a2 - a2.mean(1, keepdims=True)
    b2 = b2 - b2.mean(1, keepdims=True)
    corr = (a2 * b2).sum(1) / np.sqrt((a2**2).sum(1) * (b2**2).sum(1))
    out["median_channel_corr"] = float(np.median(corr))
    out["min_channel_corr"] = float(np.min(corr))
    out["identical"] = bool(np.array_equal(a, b))
    out["status"] = (
        "identical"
        if out["identical"]
        else ("equal within 1e-6" if out["max_abs_diff_over_std"] < 1e-6 else "differs")
    )
    return out


def compare_report(new: dict, pub: dict) -> dict:
    out = {}
    for key in pub:
        if key not in new:
            out[key] = "missing in rerun"
            continue
        a, b = np.asarray(new[key]), np.asarray(pub[key])
        if a.dtype.kind in "fc" or b.dtype.kind in "fc":
            same = a.shape == b.shape and np.allclose(a, b, rtol=1e-9, atol=0)
        else:
            same = a.shape == b.shape and np.array_equal(a, b)
        out[key] = "same" if same else f"rerun {new[key]!r} / published {pub[key]!r}"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--subject", type=int, required=True)
    parser.add_argument("--session", type=int, required=True)
    parser.add_argument(
        "--no-ica", action="store_true", help="run with ICA_BOOL = False (fast)"
    )
    parser.add_argument("--data-dir", type=Path, default=None, help="ds003626 folder")
    args = parser.parse_args()

    project_root = find_project_root(HERE)
    data_dir = args.data_dir or project_root / "ds003626"
    published = data_dir / "derivatives"
    out_root = (
        project_root
        / "results"
        / "checks"
        / ("rerun_no_ica" if args.no_ica else "rerun")
    )
    rerun = out_root / "derivatives"
    n_s, n_b = args.subject, args.session

    mne.set_log_level("WARNING")
    run_pipeline(n_s, n_b, data_dir, rerun, ica=not args.no_ica)

    result = {
        "subject": n_s,
        "session": n_b,
        "ica": not args.no_ica,
        "mne": mne.__version__,
    }
    for kind in ("eeg-epo.fif", "exg-epo.fif", "baseline-epo.fif"):
        result[kind] = compare_epochs(
            derivative_path(rerun, n_s, n_b, kind),
            derivative_path(published, n_s, n_b, kind),
        )
    new_ev, pub_ev = load_events(rerun, n_s, n_b), load_events(published, n_s, n_b)
    result["events"] = (
        "identical"
        if np.array_equal(new_ev, pub_ev)
        else (f"differs ({len(new_ev)} vs {len(pub_ev)} rows)")
    )
    result["report"] = compare_report(
        load_report(rerun, n_s, n_b), load_report(published, n_s, n_b)
    )

    ica = "off" if args.no_ica else "on"
    print(f"\nsub-{n_s:02d} ses-{n_b:02d}, ICA {ica}, MNE {mne.__version__}")
    for key, val in result.items():
        if isinstance(val, dict):
            diffs = ", ".join(f"{k}={v}" for k, v in val.items() if v != "same")
            print(f"  {key}: {diffs or 'all fields same'}")
        elif key.endswith(".fif") or key == "events":
            print(f"  {key}: {val}")
    out = out_root / f"comparison_sub-{n_s:02d}_ses-{n_b:02d}.json"
    out.write_text(json.dumps(result, indent=1, default=str))
    print(f"Saved {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
