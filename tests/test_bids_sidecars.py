"""BIDS sidecar files written by bids/make_bids_sidecars.py."""

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import load_script
from synthetic import make_raw, write_bdf

STEM = "sub-01_ses-01_task-innerspeech"


@pytest.fixture(scope="module")
def bids_dataset(tmp_path_factory):
    root = tmp_path_factory.mktemp("bids") / "ds003626"
    write_bdf(
        make_raw(n_eeg=4, trials_per_run=4), root / f"sub-01/ses-01/eeg/{STEM}_eeg.bdf"
    )
    (root / "README").write_text("Synthetic copy of the Inner Speech dataset\n")
    (root / "derivatives").mkdir()
    sidecars = load_script("bids/make_bids_sidecars.py")
    argv, sys.argv = sys.argv, ["make_bids_sidecars.py", "--data-dir", str(root)]
    try:
        sidecars.main()
    finally:
        sys.argv = argv
    return root


def read_tsv(path):
    with path.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def test_top_level_files(bids_dataset):
    description = json.loads((bids_dataset / "dataset_description.json").read_text())
    assert description["DatasetType"] == "raw" and description["HowToAcknowledge"]
    participants = read_tsv(bids_dataset / "participants.tsv")
    assert len(participants) == 10 and participants[4]["age"] == "30"
    eeg = json.loads((bids_dataset / "task-innerspeech_eeg.json").read_text())
    assert eeg["TaskName"] == "innerspeech" and eeg["PowerLineFrequency"] == 50
    derivatives = json.loads(
        (bids_dataset / "derivatives/dataset_description.json").read_text()
    )
    assert derivatives["DatasetType"] == "derivative"
    columns = json.loads((bids_dataset / "derivatives/events.json").read_text())
    assert {"sample", "class", "condition", "emg_tagged"} <= set(columns)


def test_channels(bids_dataset):
    rows = read_tsv(bids_dataset / f"sub-01/ses-01/eeg/{STEM}_channels.tsv")
    types = {r["name"]: r["type"] for r in rows}
    assert types["A1"] == "EEG" and types["EXG1"] == "REF" and types["EXG3"] == "EOG"
    assert types["EXG7"] == "EMG" and types["Status"] == "TRIG"


def test_events(bids_dataset):
    rows = read_tsv(bids_dataset / f"sub-01/ses-01/eeg/{STEM}_events.tsv")
    assert rows[0]["trial_type"] == "spurious" and rows[1]["value"] == "11"
    cues = [r for r in rows if r["trial_type"].startswith("cue_")]
    assert len(cues) == 20
    assert {r["condition"] for r in cues} == {"pronounced", "inner", "visualized"}
    for r in rows:
        assert float(r["onset"]) == pytest.approx(int(r["sample"]) / 1024)


def test_existing_files_are_kept(bids_dataset, capsys):
    sidecars = load_script("bids/make_bids_sidecars.py")
    argv, sys.argv = sys.argv, ["x", "--data-dir", str(bids_dataset)]
    try:
        sidecars.main()
    finally:
        sys.argv = argv
    assert "kept" in capsys.readouterr().out


# The validator is installed next to the Python of the test environment
VALIDATOR = shutil.which(
    "bids-validator-deno",
    path=os.pathsep.join(
        [str(Path(sys.executable).parent), os.environ.get("PATH", "")]
    ),
)


@pytest.mark.skipif(VALIDATOR is None, reason="bids-validator-deno not installed")
def test_bids_validator_reports_no_errors(bids_dataset):
    result = subprocess.run(
        [VALIDATOR, str(bids_dataset), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    issues = json.loads(result.stdout)["issues"]["issues"]
    errors = [i for i in issues if i["severity"] == "error"]
    assert not errors, errors
