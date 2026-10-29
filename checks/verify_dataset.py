"""
Check a local copy of OpenNeuro ds003626 against the published version.

1. Integrity: size and MD5 of every file against the OpenNeuro checksums
   (``ds003626_<version>_manifest.json``, from the dataset's git-annex keys;
   the newest version is used unless ``--manifest`` is given).
2. Events: rebuild ``events.dat`` and the report fields that come from the
   events (recording time, right/wrong answers) from each raw ``.bdf`` file
   with the current code and compare them with the published derivatives.
3. Derivatives: open every ``*-epo.fif`` and check trial counts, sampling rate,
   time window, channels and finite values. For the EEG files the numerical
   rank is reported: 128 means no ICA components were removed, 128 - k means k
   components were removed.

Usage (from the repository folder, in the project environment):

    python checks/verify_dataset.py                  # everything
    python checks/verify_dataset.py --skip-md5       # faster, sizes only
    python checks/verify_dataset.py --data-dir /path/to/ds003626

A summary is printed and saved to ``<project>/results/checks/verify_dataset.json``.
The exit code is 1 if any check fails.
"""

import argparse
import contextlib
import hashlib
import io
import json
import sys
from pathlib import Path

import mne
import numpy as np
from packaging.version import Version

from innerspeech.derivatives_io import (
    EVENTS_COLUMNS,
    _as_events_array,
    load_events,
    load_report,
)
from innerspeech.events_analysis import process_session_events
from innerspeech.utils import find_project_root

HERE = Path(__file__).resolve().parent
SUBJECTS = list(range(1, 11))
SESSIONS = [1, 2, 3]
EVENT_CODES = {31: 0, 32: 1, 33: 2, 34: 3}
EXG_CHANNELS = [f"EXG{i}" for i in range(1, 9)]


def newest_manifest() -> Path:
    """The manifest of the most recent dataset version in this folder."""
    manifests = HERE.glob("ds003626_*_manifest.json")
    return max(manifests, key=lambda p: Version(p.name.split("_")[1]))


def md5sum(path: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def check_integrity(
    data_dir: Path, manifest: dict, skip_md5: bool, subjects: list, sessions: list
) -> list[dict]:
    rows = []
    wanted = {f"sub-{s:02d}/ses-{b:02d}/" for s in subjects for b in sessions}
    files = {k: v for k, v in manifest["files"].items() if any(w in k for w in wanted)}
    for i, (rel, ref) in enumerate(sorted(files.items()), 1):
        path = data_dir / rel
        row = {"file": rel, "status": "ok"}
        if not path.exists():
            row["status"] = "missing"
        elif path.stat().st_size != ref["size"]:
            row.update(
                status="wrong size", size=path.stat().st_size, expected=ref["size"]
            )
        elif not skip_md5 and md5sum(path) != ref["md5"]:
            row["status"] = "wrong md5"
        rows.append(row)
        print(f"\r  integrity {i}/{len(files)}", end="", flush=True)
    print()
    return rows


def rebuild_events(data_dir: Path, n_s: int, n_b: int) -> tuple[np.ndarray, dict]:
    """Events and event-derived report fields, as InnerSpeech_preprocessing.py does."""
    sub, ses = f"sub-{n_s:02d}", f"ses-{n_b:02d}"
    bdf = data_dir / sub / ses / "eeg" / f"{sub}_{ses}_task-innerspeech_eeg.bdf"
    raw = mne.io.read_raw_bdf(bdf, preload=False, verbose="ERROR")
    _, trials, report = process_session_events(raw, n_s, n_b)
    fields = {
        "Recording_time": report["Recording_time"],
        "Ans_R": report["Ans_R"],
        "Ans_W": report["Ans_W"],
        "n_channels": len(raw.ch_names),
        "sfreq": raw.info["sfreq"],
        "corrections": [
            f"{c['action']} {c['code']} at {c['sample']} ({c['reason']})"
            for c in report["Event_corrections"]
            if c["action"] != "ignored"
        ],
    }
    return _as_events_array(trials[list(EVENTS_COLUMNS)]), fields


def check_events(
    data_dir: Path, deriv: Path, subjects: list, sessions: list
) -> list[dict]:
    rows = []
    for n_s in subjects:
        for n_b in sessions:
            tag = f"sub-{n_s:02d} ses-{n_b:02d}"
            print(f"\r  events {tag}", end="", flush=True)
            row = {"session": tag, "status": "ok", "problems": []}
            try:
                with contextlib.redirect_stdout(
                    io.StringIO()
                ):  # the event code is verbose
                    new, fields = rebuild_events(data_dir, n_s, n_b)
                pub = load_events(deriv, n_s, n_b)
                rep = load_report(deriv, n_s, n_b)
            except Exception as err:  # report and continue with the other sessions
                rows.append(
                    {"session": tag, "status": "error", "problems": [repr(err)]}
                )
                continue
            row.update(fields, n_trials=len(new))
            if new.shape != pub.shape:
                row["problems"].append(
                    f"{len(new)} trials rebuilt, {len(pub)} published"
                )
            elif not np.array_equal(new, pub):
                bad = np.nonzero((new != pub).any(axis=1))[0]
                row["problems"].append(
                    f"{len(bad)} event rows differ (first: {bad[:5].tolist()})"
                )
            for key in ("Recording_time", "Ans_R", "Ans_W"):
                if fields[key] != rep[key]:
                    row["problems"].append(
                        f"{key}: rebuilt {fields[key]}, published {rep[key]}"
                    )
            if fields["n_channels"] != 137 or fields["sfreq"] != 1024:
                row["problems"].append(
                    f"raw has {fields['n_channels']} channels at {fields['sfreq']} Hz"
                )
            if row["problems"]:
                row["status"] = "differs"
            rows.append(row)
    print()
    return rows


def eeg_rank(epochs: mne.BaseEpochs) -> int:
    x = epochs.get_data(copy=False)
    x = x.transpose(1, 0, 2).reshape(x.shape[1], -1)
    eig = np.linalg.eigvalsh(x @ x.T)[::-1]
    return int((eig > eig[0] * 1e-14).sum())


def check_epochs(deriv: Path, subjects: list, sessions: list) -> list[dict]:
    rows = []
    for n_s in subjects:
        for n_b in sessions:
            tag = f"sub-{n_s:02d} ses-{n_b:02d}"
            print(f"\r  epochs {tag}", end="", flush=True)
            row = {"session": tag, "status": "ok", "problems": []}
            try:
                events = load_events(deriv, n_s, n_b)
            except Exception as err:
                rows.append(
                    {"session": tag, "status": "error", "problems": [repr(err)]}
                )
                continue
            stem = deriv / f"sub-{n_s:02d}/ses-{n_b:02d}/sub-{n_s:02d}_ses-{n_b:02d}"
            # Baselines have 136 channels (137 with Status up to version 2.1.2)
            for kind, n_ch in (
                ("eeg", (128,)),
                ("exg", (8,)),
                ("baseline", (136, 137)),
            ):
                try:
                    ep = mne.read_epochs(
                        f"{stem}_{kind}-epo.fif", preload=True, verbose="ERROR"
                    )
                except Exception as err:
                    row["problems"].append(
                        f"{kind}-epo.fif unreadable: {type(err).__name__}"
                    )
                    continue
                if len(ep.ch_names) not in n_ch:
                    row["problems"].append(f"{kind}: {len(ep.ch_names)} channels")
                if ep.info["sfreq"] != 256:
                    row["problems"].append(f"{kind}: sfreq {ep.info['sfreq']}")
                if not np.isfinite(ep.get_data(copy=False)).all():
                    row["problems"].append(f"{kind}: non-finite values")
                if kind == "baseline":
                    continue
                classes = np.array([EVENT_CODES[c] for c in ep.events[:, 2]])
                if len(ep) != len(events) or not np.array_equal(classes, events[:, 1]):
                    row["problems"].append(f"{kind}: trials do not match events.dat")
                if abs(ep.tmin + 0.5) > 1e-3 or abs(ep.tmax - 4) > 1e-2:
                    row["problems"].append(f"{kind}: window {ep.tmin}..{ep.tmax} s")
                if kind == "exg" and ep.ch_names != EXG_CHANNELS:
                    row["problems"].append("exg: unexpected channel names")
                if kind == "eeg":
                    row["eeg_rank"] = eeg_rank(ep)
                del ep
            if row["problems"]:
                row["status"] = "differs"
            rows.append(row)
    print()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-dir", type=Path, default=None, help="ds003626 folder")
    parser.add_argument("--manifest", type=Path, default=newest_manifest())
    parser.add_argument("--subjects", type=int, nargs="+", default=SUBJECTS)
    parser.add_argument("--sessions", type=int, nargs="+", default=SESSIONS)
    parser.add_argument("--skip-md5", action="store_true", help="compare sizes only")
    parser.add_argument(
        "--skip-events", action="store_true", help="do not read the raw files"
    )
    parser.add_argument(
        "--skip-epochs", action="store_true", help="do not open the epochs files"
    )
    args = parser.parse_args()

    project_root = find_project_root(HERE)
    data_dir = args.data_dir or project_root / "ds003626"
    deriv = data_dir / "derivatives"
    manifest = json.loads(args.manifest.read_text())
    print(f"Checking {data_dir} against ds003626 {manifest['version']}")

    summary = {"data_dir": str(data_dir), "version": manifest["version"]}
    summary["integrity"] = check_integrity(
        data_dir, manifest, args.skip_md5, args.subjects, args.sessions
    )
    if not args.skip_events:
        summary["events"] = check_events(data_dir, deriv, args.subjects, args.sessions)
    if not args.skip_epochs:
        summary["epochs"] = check_epochs(deriv, args.subjects, args.sessions)

    failed = False
    rows = summary["integrity"]
    bad = [r for r in rows if r["status"] != "ok"]
    print(f"\nIntegrity: {len(rows) - len(bad)}/{len(rows)} files ok")
    for r in bad:
        print(f"  {r['status']:10s} {r['file']}")
    failed |= bool(bad)
    for part in ("events", "epochs"):
        if part not in summary:
            continue
        rows = summary[part]
        bad = [r for r in rows if r["status"] != "ok"]
        print(f"{part.capitalize()}: {len(rows) - len(bad)}/{len(rows)} sessions ok")
        for r in bad:
            print(f"  {r['session']}: {'; '.join(r['problems'])}")
        failed |= bool(bad)
    if "epochs" in summary:
        ranks = {
            r["session"]: r["eeg_rank"] for r in summary["epochs"] if "eeg_rank" in r
        }
        removed = {s: 128 - k for s, k in ranks.items()}
        print(
            "EEG rank (128 - removed ICA components):",
            f"min {min(ranks.values())}, max {max(ranks.values())}" if ranks else "n/a",
        )
        summary["ica_components_removed"] = removed

    out = project_root / "results" / "checks" / "verify_dataset.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1, default=str))
    print(f"\nSaved {out}")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
