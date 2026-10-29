"""
Small helpers: names of conditions, classes and subjects, channel groups and
folders.

@author: Nicolás Nieto
"""

from __future__ import annotations

from pathlib import Path

from innerspeech.exceptions import InvalidSelectionError


def ensure_dir(dir_name: str | Path) -> None:
    """Create ``dir_name`` (and its parents) if it does not exist."""
    Path(dir_name).mkdir(parents=True, exist_ok=True)


# Channel groups of the BioSemi 128 cap: the four 32-electrode sets (A-D) and
# small regions of interest
_CHANNEL_GROUPS = {
    "A": [f"A{i}" for i in range(1, 33)],
    "B": [f"B{i}" for i in range(1, 33)],
    "C": [f"C{i}" for i in range(1, 33)],
    "D": [f"D{i}" for i in range(1, 33)],
    "OCC_L": ["A10", "A8", "D30", "A9"],
    "OCC_Z": ["A22", "A23", "A24", "A15", "A28"],
    "OCC_R": ["B12", "B5", "B6", "B7"],
    "FRONT_L": ["D6", "D5", "C32", "C31"],
    "FRONT_Z": ["C18", "C20", "C27", "C14"],
    "FRONT_R": ["C9", "C6", "C10", "C5"],
    "C_L": ["D26", "D21", "D10", "D19"],
    "C_Z": ["D15", "A1", "B1", "A2"],
    "C_R": ["B16", "B24", "B29", "B22"],
    "P_Z": ["A4", "A19", "A20", "A32", "A5"],
    "OP_Z": ["A17", "A30", "A20", "A21", "A22"],
    "all": "all",
}


def picks_from_channels(channels: str) -> list[str] | str:
    """
    Channels of a group, for the ``picks`` argument of MNE.

    Parameters
    ----------
    channels : str
        Group name: ``"A"`` to ``"D"``, a region (``"OCC_L"``, ``"OCC_Z"``,
        ``"OCC_R"``, ``"FRONT_L"``, ``"FRONT_Z"``, ``"FRONT_R"``, ``"C_L"``,
        ``"C_Z"``, ``"C_R"``, ``"P_Z"``, ``"OP_Z"``) or ``"all"``.

    Returns
    -------
    list of str or str
        Channel names, or ``"all"``.
    """
    picks = _CHANNEL_GROUPS.get(channels)
    if not picks:
        raise InvalidSelectionError(
            f"Invalid channels name {channels!r}; use one of {tuple(_CHANNEL_GROUPS)}"
        )
    return picks


def unify_names(Cond: str, Class: str) -> tuple[str, str]:
    """
    Short names of a condition and a class, as used in result file names.

    Conditions become ``"all"``, ``"pron"``, ``"inner"`` or ``"vis"`` and
    classes ``"all"``, ``"up"``, ``"down"``, ``"right"`` or ``"left"``
    (English or Spanish input, any case). Unknown names are returned
    unchanged.
    """
    conditions = {
        "all": "all", "todos": "all",
        "inner": "inner", "in": "inner",
        "vis": "vis", "visualized": "vis", "visualizado": "vis",
        "pron": "pron", "pronounced": "pron", "pronunciado": "pron",
    }  # fmt: skip
    classes = {
        "all": "all", "todo": "all",
        "up": "up", "arriba": "up",
        "down": "down", "abajo": "down",
        "right": "right", "derecha": "right",
        "left": "left", "izquierda": "left",
    }  # fmt: skip
    return conditions.get(Cond.lower(), Cond), classes.get(Class.lower(), Class)


def map_condition(cnd: str) -> str:
    """
    Long name of a condition: ``"all"``, ``"pronounced"``, ``"inner"`` or
    ``"visualized"``.

    Accepts the long and short names, their first letter and the Spanish
    names, in any case.
    """
    names = {
        "all": ("a", "all", "todos"),
        "pronounced": ("p", "pron", "pronounced", "pronunciado"),
        "inner": ("i", "in", "inner", "interno"),
        "visualized": ("v", "vis", "visualized", "visualizado"),
    }
    return _lookup(cnd, names, "condition")


def map_class(cl: str) -> str:
    """
    Name of a class: ``"all"``, ``"up"``, ``"down"``, ``"left"`` or
    ``"right"``.

    Accepts English and Spanish names and abbreviations in any case. ``"d"``
    means down (use ``"r"`` or ``"der"`` for right) and ``"i"`` means left
    (izquierda).
    """
    names = {
        "all": ("a", "all", "todos"),
        "up": ("u", "up", "ar", "arriba"),
        "down": ("d", "down", "ab", "abajo"),
        "left": ("l", "left", "i", "izq", "izquierda"),
        "right": ("r", "right", "der", "derecha"),
    }
    return _lookup(cl, names, "class")


def _lookup(name: str, names: dict[str, tuple[str, ...]], what: str) -> str:
    if not name:
        raise InvalidSelectionError(f"{what.capitalize()} is empty!")
    for standard, aliases in names.items():
        if name.lower() in aliases:
            return standard
    raise InvalidSelectionError(f"Wrong name of {what}: {name!r}")


def sub_name(N_S: int) -> str:
    """Subject label, e.g. ``1 -> "sub-01"``."""
    return f"sub-{int(N_S):02d}"


def find_project_root(start: str | Path) -> Path:
    """
    Folder that contains this repository (and, by default, the ``ds003626``
    dataset), searching upwards from ``start``.

    The repository is recognised by its ``Python_Processing`` folder, so the
    result is the same whether ``start`` is the repository root,
    ``Python_Processing`` or any folder inside it.

    Raises
    ------
    FileNotFoundError
        If no parent of ``start`` contains ``Python_Processing``.
    """
    start = Path(start).resolve()
    for folder in (start, *start.parents):
        if (folder / "Python_Processing").is_dir():
            return folder.parent
    raise FileNotFoundError(
        f"Could not find the Inner_Speech_Dataset repository above {start}. "
        "Run the script from inside the repository or set data_dir explicitly."
    )
