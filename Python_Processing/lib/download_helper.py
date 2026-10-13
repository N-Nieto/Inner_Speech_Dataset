"""
InnerSpeech dataset downloader (OpenNeuro ds003626) using DataLad.

By default every download uses the **latest** dataset version published on
OpenNeuro. A specific version can be requested with ``version="2.1.2"``
(see ``list_versions()`` for the available ones).

All DataLad operations happen in a hidden cache (``<tmp>/datalad_cache``).
The user-visible directory only receives regular files (no symlinks, no
Git/DataLad metadata). Files already present locally are verified against
the requested version (size, and optionally MD5) and re-downloaded when they
differ, so outdated or truncated copies are repaired automatically.

Requirements: ``git``, ``git-annex`` and the ``datalad`` Python package.
``git-annex`` is available from conda-forge (``conda install git-annex``)
or PyPI (``pip install git-annex``).
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import warnings
from collections.abc import Iterable
from pathlib import Path

DATASET_ID = "ds003626"
OPENNEURO_GIT_URL = "https://github.com/OpenNeuroDatasets/{dataset_id}.git"

# Logical derivative file types -> filename patterns
DERIVATIVE_PATTERNS = {
    "eeg": "*_eeg-epo.fif",
    "baseline": "*_baseline-epo.fif",
    "exg": "*_exg-epo.fif",
    "events": "*_events.dat",
    "report": "*_report.pkl",
    "all": "*",
}

IdSelection = str | int | list[str | int] | None


# ======================================================================
# Public API
# ======================================================================
def list_versions(dataset_id: str = DATASET_ID) -> list[str]:
    """
    Return the dataset versions published on OpenNeuro, oldest first.

    Versions are read from the tags of the OpenNeuro GitHub mirror, so no
    data is downloaded.

    Parameters
    ----------
    dataset_id : str, default="ds003626"
        OpenNeuro dataset accession number.

    Returns
    -------
    list of str
        Version tags sorted from oldest to newest (e.g. ``["1.0.0", ...,
        "2.1.2"]``).
    """
    return _sort_versions(_remote_versions(dataset_id))


def clone_inner_speech(
    target_dir: str | Path,
    verbose: bool = False,
) -> Path:
    """
    Prepare the visible ``ds003626`` directory and return its path.

    No data is downloaded and no folder structure is created; files are
    created lazily by ``get_derivatives`` / ``get_raw_eeg``. Calling it on a
    path that already ends in ``ds003626`` returns that path unchanged
    (no nested ``ds003626/ds003626``).
    """
    return _clone_inner_speech(target_dir, verbose=verbose)


def get_derivatives(
    dataset_path: str | Path,
    file_types: str | list[str] = "all",
    subjects: IdSelection = "all",
    sessions: IdSelection = "all",
    version: str | None = None,
    checksum: bool = False,
    verbose: bool = False,
    progress: bool = False,
) -> dict[str, object]:
    """
    Download derivative files from the Inner Speech OpenNeuro dataset.

    Parameters
    ----------
    dataset_path : str or pathlib.Path
        Folder in which the visible ``ds003626`` directory lives (it is
        created if needed). Passing the ``ds003626`` folder itself also works.

    file_types : str or list of str, default="all"
        Any of ``"eeg"`` (``*_eeg-epo.fif``), ``"baseline"``
        (``*_baseline-epo.fif``), ``"exg"`` (``*_exg-epo.fif``),
        ``"events"`` (``*_events.dat``), ``"report"`` (``*_report.pkl``)
        or ``"all"``.

    subjects, sessions : "all", None, str, int or list, default="all"
        Identifiers without the ``"sub-"`` / ``"ses-"`` prefix. Integers are
        zero-padded (``1`` -> ``"01"``). ``"all"`` or ``None`` selects all.

    version : str or None, default=None
        OpenNeuro dataset version (e.g. ``"2.1.2"``). ``None`` or
        ``"latest"`` uses the most recent published version.

    checksum : bool, default=False
        If True, files already present locally are verified by MD5 (slower)
        instead of by size only.

    verbose : bool, default=False
        Print what is resolved, skipped, downloaded or repaired.

    progress : bool, default=False
        Show a file-level progress bar.

    Returns
    -------
    dict
        ``{"version", "dataset_path", "downloaded", "skipped", "failed"}``
        where the last three are lists of paths relative to ``dataset_path``.

    Raises
    ------
    RuntimeError
        If one or more files could not be downloaded or failed verification.
    """
    file_types, subjects, sessions = _normalize_inputs(
        file_types, subjects, sessions, allowed_file_types=DERIVATIVE_PATTERNS
    )
    dataset_path = _clone_inner_speech(dataset_path, verbose=verbose)
    hidden_path, version = _prepare_hidden_dataset(DATASET_ID, version, verbose)

    root = hidden_path / "derivatives"
    candidates: list[Path] = []
    for ft in file_types:
        for ses_dir in _session_dirs(root, subjects, sessions):
            candidates.extend(
                p
                for p in sorted(ses_dir.glob(DERIVATIVE_PATTERNS[ft]))
                if p.is_symlink() or p.is_file()
            )
    candidates = sorted(set(candidates))

    return _fetch_files(
        hidden_path=hidden_path,
        dataset_path=dataset_path,
        files=candidates,
        version=version,
        checksum=checksum,
        verbose=verbose,
        progress=progress,
        desc="Downloading derivatives",
    )


def get_raw_eeg(
    dataset_path: str | Path,
    subjects: IdSelection = "all",
    sessions: IdSelection = "all",
    version: str | None = None,
    checksum: bool = False,
    verbose: bool = False,
    progress: bool = False,
) -> dict[str, object]:
    """
    Download raw EEG recordings (``.bdf``) from the Inner Speech dataset.

    Files are stored under ``ds003626/sub-XX/ses-YY/eeg/`` following BIDS.
    Parameters and return value are as in ``get_derivatives`` (without
    ``file_types``). By default the latest OpenNeuro version is used.
    """
    _, subjects, sessions = _normalize_inputs("raw", subjects, sessions)
    dataset_path = _clone_inner_speech(dataset_path, verbose=verbose)
    hidden_path, version = _prepare_hidden_dataset(DATASET_ID, version, verbose)

    candidates: list[Path] = []
    for ses_dir in _session_dirs(hidden_path, subjects, sessions):
        eeg_dir = ses_dir / "eeg"
        if eeg_dir.is_dir():
            candidates.extend(
                p
                for p in sorted(eeg_dir.glob("*.bdf"))
                if p.is_symlink() or p.is_file()
            )

    return _fetch_files(
        hidden_path=hidden_path,
        dataset_path=dataset_path,
        files=candidates,
        version=version,
        checksum=checksum,
        verbose=verbose,
        progress=progress,
        desc="Downloading raw EEG",
    )


# ======================================================================
# Version handling
# ======================================================================
def _version_key(tag: str) -> tuple[int, ...] | None:
    """Numeric sort key for tags like '2.1.2'; None for non-version tags."""
    parts = tag.split(".")
    if not parts or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def _sort_versions(tags: Iterable[str]) -> list[str]:
    return sorted({t for t in tags if _version_key(t)}, key=_version_key)


def _remote_versions(dataset_id: str) -> list[str]:
    """Version tags on the OpenNeuro GitHub mirror (needs network + git)."""
    url = OPENNEURO_GIT_URL.format(dataset_id=dataset_id)
    out = _run_git(["ls-remote", "--tags", "--refs", url], timeout=60)
    tags = [
        line.split("refs/tags/", 1)[1]
        for line in out.splitlines()
        if "refs/tags/" in line
    ]
    return _sort_versions(tags)


def _local_versions(repo: Path) -> list[str]:
    return _sort_versions(_run_git(["tag", "--list"], cwd=repo).split())


def _resolve_version(
    requested: str | None, dataset_id: str, repo: Path, verbose: bool
) -> str:
    """
    Turn ``None``/"latest"/"v2.1.2"/"2.1.2" into an existing version tag.
    Falls back to the tags of the cached clone when OpenNeuro is unreachable.
    """
    try:
        available = _remote_versions(dataset_id)
    except Exception as err:  # offline, git missing, ...
        available = _local_versions(repo) if (repo / ".git").exists() else []
        if not available:
            raise RuntimeError(
                f"Could not list the versions of {dataset_id} on OpenNeuro "
                f"({err}). Check your internet connection."
            ) from err
        warnings.warn(
            f"Could not reach OpenNeuro ({err}); using versions known to the "
            f"local cache: latest cached = {available[-1]}.",
            stacklevel=3,
        )

    if not available:
        raise RuntimeError(f"No published versions found for {dataset_id}.")

    if requested is None or str(requested).lower() == "latest":
        version = available[-1]
        if verbose:
            print(f"✓ Using latest {dataset_id} version: {version}")
        return version

    version = str(requested).strip().lstrip("vV")
    if version not in available:
        raise ValueError(
            f"Version '{requested}' of {dataset_id} does not exist. "
            f"Available versions: {', '.join(available)}."
        )
    if verbose:
        latest = available[-1]
        note = "" if version == latest else f" (latest is {latest})"
        print(f"✓ Using requested {dataset_id} version: {version}{note}")
    return version


def _prepare_hidden_dataset(
    dataset_id: str, version: str | None, verbose: bool
) -> tuple[Path, str]:
    """
    Ensure the hidden DataLad clone exists and is checked out at the
    requested version (latest by default). Returns (path, version).
    """
    _check_dependencies()
    hidden_root = Path(tempfile.gettempdir()) / "datalad_cache"
    hidden_root.mkdir(parents=True, exist_ok=True)
    repo = hidden_root / dataset_id

    version = _resolve_version(version, dataset_id, repo, verbose)

    # A folder without .git is a broken/interrupted clone: start over
    if repo.exists() and not (repo / ".git").exists():
        if verbose:
            print(f"Removing incomplete cache at {repo}")
        _rmtree(repo)

    if not repo.exists():
        if verbose:
            print("Cloning DataLad dataset into hidden cache...")
        from datalad import api as dl

        dl.clone(
            source=OPENNEURO_GIT_URL.format(dataset_id=dataset_id),
            path=repo,
            result_renderer="disabled",
        )
    elif verbose:
        print(f"✓ Reusing cached DataLad dataset at {repo}")

    # Cached clone may predate the requested version: fetch new tags
    # (this also updates the git-annex branch with the new file locations)
    if version not in _local_versions(repo):
        if verbose:
            print("Fetching new versions from OpenNeuro...")
        _run_git(["fetch", "--quiet", "--tags", "origin"], cwd=repo, timeout=600)
        if version not in _local_versions(repo):
            raise RuntimeError(
                f"Version {version} could not be fetched into the cache {repo}."
            )

    head = _run_git(["rev-parse", "HEAD"], cwd=repo).strip()
    target = _run_git(["rev-parse", f"{version}^{{commit}}"], cwd=repo).strip()
    if head != target:
        if verbose:
            print(f"Checking out version {version} in the cache")
        _run_git(
            ["-c", "advice.detachedHead=false", "checkout", "--quiet", version],
            cwd=repo,
        )

    return repo, version


# ======================================================================
# Download + verification
# ======================================================================
_ANNEX_KEY_RE = re.compile(
    r"^(?P<backend>[A-Z0-9]+)-s(?P<size>\d+)(?:-[a-zA-Z]\d+)*--(?P<hash>[0-9a-fA-F]+)"
)


def _annex_key(path: Path) -> str | None:
    """git-annex key of a file in the hidden clone (symlink or pointer file)."""
    if path.is_symlink():
        target = str(path.readlink())
        if "annex/objects" in target.replace("\\", "/"):
            return Path(target).name
        return None
    try:
        if path.stat().st_size < 1024:
            text = path.read_text(errors="ignore").strip()
            if text.startswith("/annex/objects/"):
                return Path(text).name
    except OSError:
        pass
    return None


def _expected_content(path: Path) -> tuple[int | None, str | None]:
    """Expected (size, md5) of a file in the requested dataset version."""
    key = _annex_key(path)
    if key:
        m = _ANNEX_KEY_RE.match(key)
        if m:
            md5 = m["hash"][:32].lower() if m["backend"].startswith("MD5") else None
            return int(m["size"]), md5
        return None, None
    if path.is_file():  # small file stored directly in git
        return path.stat().st_size, _md5(path)
    return None, None


def _md5(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _matches(
    path: Path, size: int | None, md5: str | None, checksum: bool
) -> tuple[bool, str]:
    """Does a local file match the expected content? Returns (ok, reason)."""
    actual = path.stat().st_size
    if size is not None and actual != size:
        return False, f"size {actual:,} B, expected {size:,} B"
    if checksum and md5 is not None and _md5(path) != md5:
        return False, "MD5 mismatch"
    return True, ""


def _fetch_files(
    hidden_path: Path,
    dataset_path: Path,
    files: list[Path],
    version: str,
    checksum: bool,
    verbose: bool,
    progress: bool,
    desc: str,
) -> dict[str, object]:
    summary: dict[str, object] = {
        "version": version,
        "dataset_path": dataset_path,
        "downloaded": [],
        "skipped": [],
        "failed": [],
    }
    if not files:
        if verbose:
            print("No matching files found for the requested selection.")
        return summary

    from datalad import api as dl

    ds = dl.Dataset(hidden_path)
    log = verbose and not progress

    iterator: Iterable[Path] = files
    if progress:
        from tqdm import tqdm

        iterator = tqdm(files, desc=desc, unit="file")

    for src in iterator:
        rel = src.relative_to(hidden_path)
        dest = dataset_path / rel
        size, md5 = _expected_content(src)

        # Keep local copies that match this version; repair the others
        if dest.exists():
            ok, reason = _matches(dest, size, md5, checksum)
            if ok:
                summary["skipped"].append(rel)
                if log:
                    print(f"Up to date: {rel}")
                continue
            print(
                f"Re-downloading {rel}: local copy differs from v{version} ({reason})"
            )
        elif log:
            print(f"Getting: {rel}")

        results = ds.get(
            str(src),
            on_failure="ignore",
            result_renderer="disabled",
            return_type="list",
        )
        errors = [r for r in results if r.get("status") not in ("ok", "notneeded")]
        if errors or not src.exists():
            msg = _result_message(errors[0]) if errors else "no content retrieved"
            summary["failed"].append(rel)
            print(f"✗ Could not download {rel}: {msg}")
            continue

        # Copy through a temporary file so an interrupted copy never
        # leaves a truncated file under the final name
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        shutil.copyfile(src, tmp, follow_symlinks=True)
        ok, reason = _matches(tmp, size, md5, checksum)
        if not ok:
            tmp.unlink(missing_ok=True)
            summary["failed"].append(rel)
            print(f"✗ Verification failed for {rel}: {reason}")
        else:
            tmp.replace(dest)
            summary["downloaded"].append(rel)

        # Free the hidden cache right away
        ds.drop(
            str(src),
            reckless="availability",
            on_failure="ignore",
            result_renderer="disabled",
        )

    if verbose:
        print(
            f"\n✓ {dataset_path.name} v{version}: "
            f"{len(summary['downloaded'])} downloaded, "
            f"{len(summary['skipped'])} already up to date, "
            f"{len(summary['failed'])} failed."
        )
    if summary["failed"]:
        listed = "\n  ".join(str(p) for p in summary["failed"])
        raise RuntimeError(
            f"{len(summary['failed'])} file(s) could not be downloaded:\n  {listed}\n"
            "Run the same call again to retry; completed files are kept."
        )
    return summary


# ======================================================================
# Helpers
# ======================================================================
def _result_message(result: dict) -> str:
    """Readable message from a DataLad result record."""
    msg = result.get("message") or result.get("error_message")
    if isinstance(msg, (tuple, list)) and msg:
        try:
            msg = msg[0] % tuple(msg[1:])
        except (TypeError, ValueError):
            msg = " ".join(map(str, msg))
    return (
        f"{result.get('status', 'error')}: {msg}"
        if msg
        else str(result.get("status", "error"))
    )


def _session_dirs(root: Path, subjects, sessions) -> list[Path]:
    """Existing ses-* folders under root for the selected subjects/sessions."""
    if subjects == "all":
        subj_dirs = sorted(p for p in root.glob("sub-*") if p.is_dir())
    else:
        subj_dirs = [root / f"sub-{s}" for s in subjects]
    out = []
    for subj_dir in subj_dirs:
        if not subj_dir.is_dir():
            continue
        if sessions == "all":
            out.extend(sorted(p for p in subj_dir.glob("ses-*") if p.is_dir()))
        else:
            out.extend(
                subj_dir / f"ses-{s}"
                for s in sessions
                if (subj_dir / f"ses-{s}").is_dir()
            )
    return out


def _normalize_inputs(
    file_types: str | list[str],
    subjects: IdSelection,
    sessions: IdSelection,
    *,
    allowed_file_types: Iterable[str] | None = None,
) -> tuple[list[str], list[str] | str, list[str] | str]:
    """
    Normalize user inputs: file types to a list of strings, subject/session
    IDs to zero-padded strings (``1`` -> ``"01"``) or ``"all"``.
    """
    if isinstance(file_types, str):
        file_types = [file_types]
    elif not isinstance(file_types, (list, tuple)):
        raise TypeError("file_types must be a string or a list of strings.")
    file_types = list(file_types)

    if not all(isinstance(ft, str) for ft in file_types):
        raise TypeError("All entries in file_types must be strings.")

    if allowed_file_types is not None:
        invalid = set(file_types) - set(allowed_file_types)
        if invalid:
            raise ValueError(
                f"Invalid file_types requested: {sorted(invalid)}. "
                f"Allowed values are: {sorted(allowed_file_types)}."
            )
        if "all" in file_types:
            file_types = ["all"]

    def _normalize_ids(value: IdSelection, label: str) -> list[str] | str:
        if value is None or (isinstance(value, str) and value.lower() == "all"):
            return "all"
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            value = [value]
        if not isinstance(value, (list, tuple)):
            raise TypeError(
                f"{label} must be 'all', a string, an int, or a list of strings/ints."
            )
        normalized: list[str] = []
        for v in value:
            if isinstance(v, bool):
                raise TypeError(f"{label} IDs must be strings or integers.")
            if isinstance(v, int):
                if v < 1:
                    raise ValueError(f"{label} IDs must be positive integers.")
                normalized.append(f"{v:02d}")
            elif isinstance(v, str):
                v = v.strip()
                for prefix in ("sub-", "ses-"):
                    if v.startswith(prefix):
                        v = v[len(prefix) :]
                if not v.isdigit():
                    raise ValueError(
                        f"{label} IDs must contain only digits (got '{v}')."
                    )
                normalized.append(v.zfill(2))
            else:
                raise TypeError(f"{label} IDs must be strings or integers.")
        return normalized

    return (
        file_types,
        _normalize_ids(subjects, "subjects"),
        _normalize_ids(sessions, "sessions"),
    )


def _check_dependencies() -> None:
    """Fail early with a clear message if git / git-annex / datalad are missing."""
    missing = [tool for tool in ("git", "git-annex") if shutil.which(tool) is None]
    if importlib.util.find_spec("datalad") is None:
        missing.append("datalad (Python package)")
    if missing:
        raise RuntimeError(
            "Missing requirements for downloading: "
            + ", ".join(missing)
            + ". Install them e.g. with "
            "`conda install -c conda-forge datalad git-annex` "
            "or `pip install datalad git-annex`."
        )


def _run_git(args: list[str], cwd: Path | None = None, timeout: int = 120) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def _rmtree(path: Path) -> None:
    """rmtree that also removes git-annex's read-only files/folders."""

    def _retry(func, p, _exc):
        Path(p).chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        func(p)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_retry)
    else:
        shutil.rmtree(path, onerror=_retry)


def _clone_inner_speech(
    target_dir: str | Path,
    verbose: bool = False,
) -> Path:
    """
    Prepare the visible ``ds003626`` directory (no data, no structure).
    ``target_dir`` may be its parent or the ``ds003626`` folder itself.
    """
    target_dir = Path(target_dir).expanduser().resolve()
    dataset_path = (
        target_dir if target_dir.name == DATASET_ID else target_dir / DATASET_ID
    )
    dataset_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"✓ Visible dataset directory ready at {dataset_path}")

    return dataset_path
