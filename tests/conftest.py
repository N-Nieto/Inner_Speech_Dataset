"""Shared fixtures: synthetic recordings, derivatives and one pipeline run."""

import importlib.util
import sys
from pathlib import Path

import mne
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))  # tests/synthetic.py

from synthetic import make_raw, write_bdf, write_derivatives  # noqa: E402

mne.set_log_level("ERROR")


def load_script(relative_path: str):
    """Import one of the repository scripts (checks/, bids/) as a module."""
    path = REPO / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def pipeline_output(tmp_path_factory) -> Path:
    """Run InnerSpeech_preprocessing.py (ICA off) on a synthetic sub-03 ses-01.

    Subject 3, session 1 also exercises the ad hoc condition correction.
    Returns the derivatives folder.
    """
    data_dir = tmp_path_factory.mktemp("pipeline") / "ds003626"
    bdf = data_dir / "sub-03/ses-01/eeg/sub-03_ses-01_task-innerspeech_eeg.bdf"
    write_bdf(make_raw(n_eeg=8), bdf)
    save_dir = data_dir / "derivatives"
    reproduce = load_script("checks/reproduce_session.py")
    reproduce.run_pipeline(3, 1, data_dir, save_dir, ica=False)
    return save_dir


@pytest.fixture(scope="session")
def derivatives(tmp_path_factory) -> Path:
    """Small synthetic derivatives (2 subjects x 3 sessions, 24 trials each).

    Returns the dataset folder that contains ``derivatives``.
    """
    root = tmp_path_factory.mktemp("synthetic") / "ds003626"
    write_derivatives(root / "derivatives")
    return root
