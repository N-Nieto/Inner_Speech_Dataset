"""
InnerSpeech dataset downloader using DataLad.
Provides functions to clone the dataset, get specific files,
list available files, and explore dataset structure.
"""

import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union, Iterable, Tuple
from datalad import api as dl
from tqdm import tqdm


def get_derivatives(
    dataset_path: Union[str, Path],
    file_types: Union[str, List[str]] = "all",
    subjects: Optional[Union[str, List[str]]] = "all",
    sessions: Optional[Union[str, List[str]]] = "all",
    verbose: bool = False,
    progress: bool = False,
) -> None:
    """
    Download derivative files from the Inner Speech OpenNeuro dataset and
    store them as files in a user-visible directory.

    This function transparently uses a hidden DataLad dataset (stored in
    a temporary location) to retrieve files from OpenNeuro. All DataLad
    operations happen in the background. The user-visible directory
    contains only regular files (no symbolic links, Git metadata, or
    DataLad traces).

    Only the requested files are downloaded. Each file is copied as a
    real file into the visible dataset directory and immediately dropped
    from the hidden DataLad cache to minimize disk usage.

    Parameters
    ----------
    dataset_path : str or pathlib.Path
        Path to the visible dataset directory. This should be the path
        returned by ``clone_inner_speech``.

    file_types : str or list of str, default="all"
        Logical derivative file types to download. These are mapped
        internally to dataset-specific filename patterns.

        Supported values include:
        - "eeg"       : epoched EEG files (``*_eeg-epo.fif``)
        - "baseline"  : baseline epoched files (``*_baseline-epo.fif``)
        - "exg"       : EXG epoched files (``*_exg-epo.fif``)
        - "events"    : event files (``*_events.dat``)
        - "report"    : report files (``*_report.pkl``)
        - "all"       : all derivative files

    subjects : str or list of str or "all", default="all"
        Subject identifiers *without* the ``"sub-"`` prefix (e.g. ``"01"``).
        Use ``"all"`` to download files for all available subjects.

    sessions : str or list of str or "all", default="all"
        Session identifiers *without* the ``"ses-"`` prefix (e.g. ``"01"``).
        Use ``"all"`` to download files for all available sessions.

    verbose : bool, default=False
        If True, print detailed information about which files are being
        resolved, downloaded, and copied.

    progress : bool, default=False
        If True, display a progress bar showing file-level download
        progress. This is recommended when downloading large files.

    Notes
    -----
    - The visible dataset directory will contain only regular files
      following the BIDS derivatives structure.
    - Repeated calls are safe and will only download missing files.
    """

    # ------------------------------------------------------------------
    # Resolve visible and hidden dataset paths
    # ------------------------------------------------------------------
    # Prepare visible directory (empty)
    # ------------------------------------------------------------------
    dataset_path = _clone_inner_speech(dataset_path, verbose=verbose)

    # ------------------------------------------------------------------
    # Ensure hidden DataLad dataset exists
    # ------------------------------------------------------------------
    hidden_dataset_path = _ensure_hidden_dataset(
        dataset_id="ds003626",
        verbose=verbose,
    )
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
    # Normalize inputs
    # ------------------------------------------------------------------
    file_types, subjects, sessions = _normalize_inputes(
        file_types,
        subjects,
        sessions,
        allowed_file_types=type_to_pattern.keys(),
    )

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
    Download raw EEG recordings from the Inner Speech OpenNeuro dataset
    and store them as plain files in a user-visible directory.

    This function retrieves raw EEG data files (``.bdf``) using a hidden
    DataLad dataset stored in a temporary location. All DataLad-related
    operations are fully hidden from the user. The resulting files in
    the visible dataset directory are regular files (not symbolic links)
    with no dependency on DataLad or Git.

    Each requested file is downloaded, copied into the visible dataset
    directory, and then immediately dropped from the hidden DataLad cache
    to reduce disk usage.

    Parameters
    ----------
    dataset_path : str or pathlib.Path
        Path to the visible dataset directory. This should be the path
        returned by ``clone_inner_speech``.

    subjects : str or list of str or "all", default="all"
        Subject identifiers *without* the ``"sub-"`` prefix (e.g. ``"01"``).
        Use ``"all"`` to download raw EEG files for all subjects.

    sessions : str or list of str or "all", default="all"
        Session identifiers *without* the ``"ses-"`` prefix (e.g. ``"01"``).
        Use ``"all"`` to download raw EEG files for all sessions.

    verbose : bool, default=False
        If True, print detailed information about which files are being
        resolved, downloaded, and copied.

    progress : bool, default=False
        If True, display a progress bar showing file-level download
        progress. This is recommended for large raw EEG files.

    Notes
    -----
    - Raw EEG files are stored under the ``eeg/`` directory of each
      subject/session, following the BIDS specification.
    - The visible dataset directory will contain only plain ``.bdf``
      files and standard BIDS folder structure.
    - No DataLad metadata, symbolic links, or Git repositories are
      created in the visible directory.
    """
    # ------------------------------------------------------------------
    # Resolve visible and hidden dataset paths
    # ------------------------------------------------------------------
    # Prepare visible directory (empty)
    # ------------------------------------------------------------------
    dataset_path = _clone_inner_speech(dataset_path, verbose=verbose)

    # ------------------------------------------------------------------
    # Ensure hidden DataLad dataset exists
    # ------------------------------------------------------------------
    hidden_dataset_path = _ensure_hidden_dataset(
        dataset_id="ds003626",
        verbose=verbose,
    )

    # ------------------------------------------------------------------
    # Normalize inputs
    # ------------------------------------------------------------------
    _, subjects, sessions = _normalize_inputes(
        "raw",
        subjects,
        sessions,
    )

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


def _normalize_inputes(
    file_types: Union[str, List[str]],
    subjects: Optional[Union[str, int, List[Union[str, int]]]],
    sessions: Optional[Union[str, int, List[Union[str, int]]]],
    *,
    allowed_file_types: Optional[Iterable[str]] = None,
) -> Tuple[List[str], Union[List[str], str], Union[List[str], str]]:
    """
    Normalize and validate user inputs for file selection.

    This helper function standardizes user-provided inputs into a
    predictable internal representation. It supports flexible input
    types while enforcing dataset-specific constraints.

    Parameters
    ----------
    file_types : str or list of str
        Logical file types requested by the user (e.g. "eeg", "events",
        "all"). Always returned as a list of strings.

    subjects : str, int, list of str or int, "all", or None
        Subject identifiers without the "sub-" prefix. Integers are
        automatically converted to zero-padded strings following the
        BIDS convention (e.g. 1 → "01").

        Accepted values:
        - "all" or None : select all subjects
        - "01", 1, ["01", "02"], [1, 2]

    sessions : str, int, list of str or int, "all", or None
        Session identifiers without the "ses-" prefix. Integers are
        converted to zero-padded strings following the BIDS convention.

        Accepted values:
        - "all" or None : select all sessions
        - "01", 1, ["01", "02"], [1, 2]

    allowed_file_types : iterable of str, optional
        List or set of valid file type identifiers. If provided, all
        requested ``file_types`` must be members of this collection.

    Returns
    -------
    file_types : list of str
        Normalized list of file types.

    subjects : list of str or "all"
        Normalized subject identifiers or the string "all".

    sessions : list of str or "all"
        Normalized session identifiers or the string "all".

    Raises
    ------
    TypeError
        If an input has an unsupported type.

    ValueError
        If a value is invalid or not included in ``allowed_file_types``.
    """

    # ------------------------------------------------------------------
    # Normalize file_types
    # ------------------------------------------------------------------
    if isinstance(file_types, str):
        file_types = [file_types]
    elif not isinstance(file_types, list):
        raise TypeError("file_types must be a string or a list of strings.")

    if not all(isinstance(ft, str) for ft in file_types):
        raise TypeError("All entries in file_types must be strings.")

    if allowed_file_types is not None:
        invalid = set(file_types) - set(allowed_file_types)
        if invalid:
            raise ValueError(
                f"Invalid file_types requested: {sorted(invalid)}. "
                f"Allowed values are: {sorted(allowed_file_types)}."
            )

    # ------------------------------------------------------------------
    # Helper to normalize subject/session IDs
    # ------------------------------------------------------------------
    def _normalize_ids(
        value: Optional[Union[str, int, List[Union[str, int]]]],
        label: str,
    ) -> Union[List[str], str]:
        if value is None or value == "all":
            return "all"

        if isinstance(value, (str, int)):
            value = [value]

        if not isinstance(value, list):
            raise TypeError(
                f"{label} must be 'all', a string, an int, or a list of strings/ints."
            )

        normalized: List[str] = []
        for v in value:
            if isinstance(v, int):
                if v < 0:
                    raise ValueError(f"{label} IDs must be positive integers.")
                normalized.append(f"{v:02d}")
            elif isinstance(v, str):
                if not v.isdigit():
                    raise ValueError(
                        f"{label} IDs must contain only digits (got '{v}')."
                    )
                normalized.append(v.zfill(2))
            else:
                raise TypeError(f"{label} IDs must be strings or integers.")

        return normalized

    # ------------------------------------------------------------------
    # Normalize subjects and sessions
    # ------------------------------------------------------------------
    subjects = _normalize_ids(subjects, "subjects")
    sessions = _normalize_ids(sessions, "sessions")

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


def _ensure_hidden_dataset(
    dataset_id: str,
    verbose: bool = False,
) -> Path:
    """
    Ensure that the hidden DataLad dataset exists in /tmp.

    If the dataset does not exist or is empty, it is cloned.
    If it already exists and contains data, it is reused.

    Returns
    -------
    hidden_dataset_path : Path
        Path to the hidden DataLad dataset.
    """
    hidden_root = Path(tempfile.gettempdir()) / "datalad_cache"
    hidden_root.mkdir(parents=True, exist_ok=True)

    hidden_dataset_path = hidden_root / dataset_id

    # Dataset exists and is non-empty → reuse
    if hidden_dataset_path.exists() and any(hidden_dataset_path.iterdir()):
        if verbose:
            print(f"✓ Reusing cached DataLad dataset at {hidden_dataset_path}")
        return hidden_dataset_path

    # Otherwise clone
    if verbose:
        print("Cloning DataLad dataset into hidden cache...")

    ds = dl.clone(
        source=f"https://github.com/OpenNeuroDatasets/{dataset_id}.git",
        path=hidden_dataset_path,
        result_renderer="disabled",
    )

    return hidden_dataset_path


def _clone_inner_speech(
    target_dir: Union[str, Path],
    verbose: bool = False,
) -> Path:
    """
    Prepare an empty visible directory for the Inner Speech dataset.

    This function does NOT download any data and does NOT create any
    folder structure. Files and directories are created lazily when
    data is requested via get_derivatives or get_raw_eeg.
    """
    target_dir = Path(target_dir).resolve()
    dataset_path = target_dir / "ds003626"

    dataset_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"✓ Visible dataset directory ready at {dataset_path}")

    return dataset_path
