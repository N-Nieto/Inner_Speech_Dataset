"""bids/convert_derivatives.py adds events.tsv and report.json to legacy files."""

import shutil

import pandas as pd

from conftest import load_script
from innerspeech.derivatives_io import (
    _as_trial_table,
    derivative_path,
    load_events_table,
    load_report,
    save_report,
)

convert = load_script("bids/convert_derivatives.py")


def copy_dataset(pipeline_output, tmp_path):
    data_dir = tmp_path / "ds003626"
    shutil.copytree(pipeline_output.parent, data_dir)
    return data_dir, data_dir / "derivatives"


def test_legacy_derivatives_are_converted(pipeline_output, tmp_path):
    data_dir, deriv = copy_dataset(pipeline_output, tmp_path)
    expected_table = load_events_table(deriv, 3, 1)
    expected_report = load_report(deriv, 3, 1)
    for kind in ("events.tsv", "report.json"):  # as published up to 2.1.2
        derivative_path(deriv, 3, 1, kind).unlink()

    summary, files = convert.convert_session(data_dir, 3, 1, n_jobs=1)
    assert summary["status"] == "ok", summary["problems"]
    table = _as_trial_table(files["events"])
    pd.testing.assert_frame_equal(table, expected_table, check_dtype=False, rtol=1e-12)
    for key in ("Known_issue", "Event_corrections", "Ans_R", "Age"):
        assert files["report"][key] == expected_report[key], key


def test_differences_are_reported(pipeline_output, tmp_path):
    data_dir, deriv = copy_dataset(pipeline_output, tmp_path)
    report = load_report(deriv, 3, 1)
    report["Ans_R"] = 3
    save_report(report, deriv, 3, 1)
    summary, files = convert.convert_session(data_dir, 3, 1, n_jobs=1)
    assert summary["status"] == "differs" and files is None
    assert any("Ans_R" in p for p in summary["problems"])
