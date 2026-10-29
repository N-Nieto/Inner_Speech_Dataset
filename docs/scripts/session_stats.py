"""
Write the per-session summary shown on the "Sessions at a glance" page.

Reads the trial tables and reports of a local copy of the derivatives and writes
``docs/assets/data/sessions.json`` (for the interactive figure) and
``docs/snippets/sessions_table.md`` (the table under it). Re-run it after the
derivatives change:

    python docs/scripts/session_stats.py                 # ../ds003626/derivatives
    python docs/scripts/session_stats.py --derivatives /path/to/ds003626/derivatives
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from innerspeech.derivatives_io import derivative_path, load_events_table, load_report

REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / "docs" / "assets" / "data" / "sessions.json"
TABLE = REPO / "docs" / "snippets" / "sessions_table.md"
CONDITIONS = ("pronounced", "inner", "visualized")
CLASSES = ("up", "down", "right", "left")


def session_summary(derivatives: Path, n_s: int, n_b: int) -> dict:
    """Counts, EMG control, answers and event corrections of one session."""
    trials = load_events_table(derivatives, n_s, n_b)
    report = load_report(derivatives, n_s, n_b)
    new_format = derivative_path(derivatives, n_s, n_b, "report.json").exists()

    by_condition = {}
    for code, name in enumerate(CONDITIONS):
        rows = trials[trials["condition"] == code]
        by_condition[name] = {
            "trials": len(rows),
            "emg_tagged": int(rows["emg_tagged"].fillna(False).sum()),
        }

    corrections = None
    if "Event_corrections" in report:
        corrections = [
            {
                "sample": int(c["sample"]),
                "code": int(c["code"]),
                "action": c["action"],
                "reason": c["reason"],
            }
            for c in report["Event_corrections"]
        ]

    inferred = trials["cue_inferred"]
    return {
        "subject": n_s,
        "session": n_b,
        "format": "json" if new_format else "legacy",
        "age": int(report["Age"]),
        "gender": report["Gender"],
        "recording_time": int(report["Recording_time"]),
        "answers_right": int(report["Ans_R"]),
        "answers_wrong": int(report["Ans_W"]),
        "trials": len(trials),
        "conditions": by_condition,
        "classes": {
            name: int((trials["class"] == code).sum())
            for code, name in enumerate(CLASSES)
        },
        "emg_tagged": int(trials["emg_tagged"].fillna(False).sum()),
        "cue_inferred": None
        if inferred.isna().all()
        else int(inferred.fillna(False).sum()),
        "corrections": corrections,
    }


def markdown_table(sessions: list[dict]) -> str:
    """The summary as a Markdown table, one row per session."""
    lines = [
        "| Subject | Session | Trials | Pronounced | Inner | Visualized | EMG-tagged "
        "| Inserted events | Answers (right/wrong) | Recording |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in sessions:
        c = s["conditions"]
        corrections = s["corrections"]
        inserted = (
            "n/a"
            if corrections is None
            else str(sum(x["action"] != "ignored" for x in corrections))
        )
        minutes, seconds = divmod(s["recording_time"], 60)
        lines.append(
            f"| sub-{s['subject']:02d} | {s['session']} | {s['trials']} "
            f"| {c['pronounced']['trials']} | {c['inner']['trials']} "
            f"| {c['visualized']['trials']} | {s['emg_tagged']} | {inserted} "
            f"| {s['answers_right']} / {s['answers_wrong']} | {minutes}:{seconds:02d} |"
        )
    total = {
        key: sum(s["conditions"][key]["trials"] for s in sessions) for key in CONDITIONS
    }
    lines.append(
        f"| **Total** | | **{sum(s['trials'] for s in sessions):,}** "
        f"| **{total['pronounced']:,}** | **{total['inner']:,}** "
        f"| **{total['visualized']:,}** "
        f"| **{sum(s['emg_tagged'] for s in sessions)}** | | | |"
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument(
        "--derivatives",
        type=Path,
        default=REPO.parent / "ds003626" / "derivatives",
        help="derivatives folder (default: ../ds003626/derivatives)",
    )
    args = parser.parse_args()

    sessions = []
    for n_s in range(1, 11):
        for n_b in (1, 2, 3):
            if derivative_path(
                args.derivatives, n_s, n_b, "eeg-epo.fif"
            ).parent.is_dir():
                sessions.append(session_summary(args.derivatives, n_s, n_b))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"sessions": sessions}, indent=1) + "\n", "utf-8")
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    TABLE.write_text(markdown_table(sessions), "utf-8")
    print(
        f"{len(sessions)} sessions -> "
        f"{OUTPUT.relative_to(REPO)}, {TABLE.relative_to(REPO)}"
    )


if __name__ == "__main__":
    main()
