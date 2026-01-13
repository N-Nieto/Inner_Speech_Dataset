"""
InnerSpeech dataset downloader using DataLad.
Provides functions to clone the dataset, get specific files,
list available files, and explore dataset structure.
"""

import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union
from datalad import api as dl
from tqdm import tqdm


def clone_inner_speech(
    target_dir: str,
    verbose: bool = False,
) -> Path:
    """
    Clone InnerSpeech dataset into a hidden DataLad cache and create a
    visible directory structure without files.

    Parameters
    ----------
    target_dir : str
        User-visible directory.
    verbose : bool
        Print progress messages.

    Returns
    -------
    visible_dataset_path : Path
        Path to visible dataset directory.
    """
    if not _check_datalad_installed():
        raise RuntimeError(
            "DataLad is not installed. Install with: pip install datalad"
        )

    dataset_id = "ds003626"

    # Ensure is a string
    target_dir = str(target_dir)
    visible_dataset_path = Path(target_dir).resolve() / dataset_id
    visible_dataset_path.mkdir(parents=True, exist_ok=True)

    # Hidden DataLad cache
    cache_root = Path(tempfile.gettempdir()) / "datalad_cache"
    cache_root.mkdir(exist_ok=True)
    hidden_dataset_path = cache_root / dataset_id

    if not hidden_dataset_path.exists():
        if verbose:
            print(f"Cloning dataset into hidden cache: {hidden_dataset_path}")

        subprocess.run(
            [
                "datalad",
                "clone",
                f"https://github.com/OpenNeuroDatasets/{dataset_id}.git",
                str(hidden_dataset_path),
            ],
            check=True,
        )
    else:
        if verbose:
            print(f"✓ Hidden dataset already exists: {hidden_dataset_path}")

    # Create directory structure without files
    if verbose:
        print("Creating visible directory structure (no files)...")

    for path in hidden_dataset_path.rglob("*"):
        if path.is_dir() and not any(p.startswith(".") for p in path.parts):
            rel = path.relative_to(hidden_dataset_path)
            (visible_dataset_path / rel).mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"✓ Visible dataset ready at: {visible_dataset_path}")

    return visible_dataset_path


def get_derivatives(
    dataset_path: Union[str, Path],
    file_types: Union[str, List[str]] = "all",
    subjects: Optional[Union[str, List[str]]] = "all",
    sessions: Optional[Union[str, List[str]]] = "all",
    verbose: bool = False,
    progress: bool = False,
) -> None:
    """
    Download derivative files from the Inner Speech OpenNeuro dataset
    using a hidden DataLad dataset and copy them as real files into
    a visible directory.
    """

    # ------------------------------------------------------------------
    # Resolve visible and hidden dataset paths
    # ------------------------------------------------------------------
    dataset_path = Path(dataset_path).resolve()
    dataset_id = dataset_path.name
    print("DATASET DIR")
    print(dataset_path)
    hidden_dataset_path = Path(tempfile.gettempdir()) / "datalad_cache" / dataset_id

    if not hidden_dataset_path.exists():
        raise RuntimeError(
            "Hidden DataLad dataset not found. Run clone_inner_speech() first."
        )

    # ------------------------------------------------------------------
    # Normalize inputs
    # ------------------------------------------------------------------
    file_types, subjects, sessions = _normalize_inputes(file_types, subjects, sessions)

    # ------------------------------------------------------------------
    # File type → filename pattern mapping
    # ------------------------------------------------------------------
    type_to_pattern = {
        "eeg": "*_eeg-epo.fif",
        "baseline": "*_baseline-epo.fif",
        "exg": "*_exg-epo.fif",
        "events": "*_events.dat",
        "report": "*_report.pkl",
        "all": "*",
    }

    # ------------------------------------------------------------------
    # Initialize DataLad dataset
    # ------------------------------------------------------------------
    ds = dl.Dataset(hidden_dataset_path)

    # Ensure derivative subdataset metadata is installed
    ds.get(
        "derivatives",
        recursive=True,
        get_data=False,
        on_failure="ignore",
        result_renderer="disabled",
    )

    derivatives_root = hidden_dataset_path / "derivatives"

    # ------------------------------------------------------------------
    # Collect candidate files first (for progress bar support)
    # ------------------------------------------------------------------
    candidate_files = []

    for ft in file_types:
        if ft not in type_to_pattern:
            raise ValueError(f"Unknown file type: {ft}")

        fname_pattern = type_to_pattern[ft]

        subj_dirs = (
            list(derivatives_root.glob("sub-*"))
            if subjects == "all"
            else [derivatives_root / f"sub-{s}" for s in subjects]
        )

        for subj_dir in subj_dirs:
            if not subj_dir.exists():
                continue

            ses_dirs = (
                list(subj_dir.glob("ses-*"))
                if sessions == "all"
                else [subj_dir / f"ses-{s}" for s in sessions]
            )

            for ses_dir in ses_dirs:
                if not ses_dir.exists():
                    continue

                candidate_files.extend(ses_dir.glob(fname_pattern))

    if not candidate_files and verbose:
        print("No matching derivative files found.")
        return

    # ------------------------------------------------------------------
    # Download + copy files
    # ------------------------------------------------------------------
    iterator = candidate_files
    if progress:
        iterator = tqdm(iterator, desc="Downloading derivatives", unit="file")

    for file in iterator:
        rel = file.relative_to(hidden_dataset_path)
        dest = dataset_path / rel

        # Skip if file already exists in destination
        if dest.exists():
            if verbose and not progress:
                print(f"Skipping, file already in destination: {rel}")
            continue

        if verbose and not progress:
            print(f"Getting: {rel}")

        # Materialize file
        ds.get(str(rel), on_failure="ignore", result_renderer="disabled")

        # Copy real file (dereference symlink)
        dest = dataset_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        real_file = hidden_dataset_path / rel

        shutil.copyfile(real_file, dest, follow_symlinks=True)

        # Drop content from hidden dataset
        ds.drop(
            str(rel),
            reckless="availability",
            on_failure="ignore",
            result_renderer="disabled",
        )

    if verbose:
        print("\n✓ Derivative files downloaded.")


def get_raw_eeg(
    dataset_path: Union[str, Path],
    subjects: Optional[Union[str, List[str]]] = "all",
    sessions: Optional[Union[str, List[str]]] = "all",
    verbose: bool = False,
    progress: bool = False,
) -> None:
    """
    Download raw EEG (.bdf) files from the Inner Speech OpenNeuro dataset
    using a hidden DataLad dataset and copy them as real files into
    a visible directory.
    """

    # ------------------------------------------------------------------
    # Resolve visible and hidden dataset paths
    # ------------------------------------------------------------------
    dataset_path = Path(dataset_path).resolve()
    dataset_id = dataset_path.name

    hidden_dataset_path = Path(tempfile.gettempdir()) / "datalad_cache" / dataset_id

    if not hidden_dataset_path.exists():
        raise RuntimeError(
            "Hidden DataLad dataset not found. Run clone_inner_speech() first."
        )

    # ------------------------------------------------------------------
    # Normalize inputs
    # ------------------------------------------------------------------
    _, subjects, sessions = _normalize_inputes("raw", subjects, sessions)

    # ------------------------------------------------------------------
    # Initialize DataLad dataset
    # ------------------------------------------------------------------
    ds = dl.Dataset(hidden_dataset_path)

    # ------------------------------------------------------------------
    # Collect candidate files
    # ------------------------------------------------------------------
    candidate_files = []

    subj_dirs = (
        list(hidden_dataset_path.glob("sub-*"))
        if subjects == "all"
        else [hidden_dataset_path / f"sub-{s}" for s in subjects]
    )

    for subj_dir in subj_dirs:
        if not subj_dir.exists():
            continue

        ses_dirs = (
            list(subj_dir.glob("ses-*"))
            if sessions == "all"
            else [subj_dir / f"ses-{s}" for s in sessions]
        )

        for ses_dir in ses_dirs:
            eeg_dir = ses_dir / "eeg"
            if not eeg_dir.exists():
                continue

            candidate_files.extend(eeg_dir.glob("*.bdf"))

    if not candidate_files and verbose:
        print("No raw EEG files found.")
        return

    # ------------------------------------------------------------------
    # Download + copy files
    # ------------------------------------------------------------------
    iterator = candidate_files
    if progress:
        iterator = tqdm(iterator, desc="Downloading raw EEG", unit="file")

    for file in iterator:
        rel = file.relative_to(hidden_dataset_path)

        dest = dataset_path / rel

        # Skip if file already exists in destination
        if dest.exists():
            if verbose and not progress:
                print(f"Skipping, file already in destination: {rel}")
            continue

        if verbose and not progress:
            print(f"Getting: {rel}")

        ds.get(str(rel), on_failure="ignore", result_renderer="disabled")

        dest = dataset_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        real_file = hidden_dataset_path / rel

        shutil.copyfile(real_file, dest, follow_symlinks=True)

        ds.drop(
            str(rel),
            reckless="availability",
            on_failure="ignore",
            result_renderer="disabled",
        )

    if verbose:
        print("\n✓ Raw EEG files downloaded.")


def _normalize_inputes(file_types, subjects, sessions) -> tuple:
    # Normalize inputs
    if isinstance(file_types, str):
        file_types = [file_types]

    if subjects is not None and isinstance(subjects, str):
        subjects = [subjects]

    if sessions is not None and isinstance(sessions, str):
        sessions = [sessions]
    return file_types, subjects, sessions


def _check_datalad_installed() -> bool:
    try:
        subprocess.run(
            ["datalad", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False
