"""
@author: Nicolás Nieto
@email: nnieto@sinc.unl.edu.ar

Utilitys for Inner speech dataset processing
"""

from pathlib import Path

from lib.exceptions import InvalidSelectionError


def ensure_dir(dir_name: str) -> None:
    """
    Ensure that the specified directory exists; if not, create it.

    Parameters:
    - dir_name (str): The directory path.

    Returns:
    - None
    """
    Path(dir_name).mkdir(parents=True, exist_ok=True)


def picks_from_channels(channels):
    """
    Parameters
    ----------
    channels : str
        Name of the channel or regions.

    Returns
    -------
    picks : list
        List of picks that corresponds with the channels.

    """
    channel_mappings = {
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

    picks = channel_mappings.get(channels, [])

    if not picks:
        raise InvalidSelectionError("Invalid channels name")

    return picks


def unify_names(Cond: str, Class: str) -> tuple[str, str]:
    """
    Unify different representations of conditions and classes
    to a standard set of names.

    Parameters:
    - Cond (str): The input condition label.
    - Class (str): The input class label.

    Returns:
    - tuple: A tuple containing the standardized condition and class labels.
    """

    # Unify condition names
    cond = Cond.lower()
    if cond in ("inner", "in"):
        Cond = "inner"
    elif cond in ("vis", "visualized", "visualizado"):
        Cond = "vis"
    elif cond in ("pron", "pronounced", "pronunciado"):
        Cond = "pron"

    # Unify class names
    cl = Class.lower()
    if cl in ("all", "todo"):
        Class = "all"
    elif cl in ("up", "arriba"):
        Class = "up"
    elif cl in ("down", "abajo"):
        Class = "down"
    elif cl in ("right", "derecha"):
        Class = "right"
    elif cl in ("left", "izquierda"):
        Class = "left"

    return Cond, Class


def map_condition(cnd: str) -> str:
    """
    Map different representations of conditions
    to a standard set of conditions.

    Parameters:
    - cnd (str): The input condition label.

    Returns:
    - str: The standardized condition label.
    """
    if not cnd:
        raise InvalidSelectionError("Condition is empty!")

    if cnd.lower() in ["a", "all", "todos"]:
        Cond = "all"
    elif cnd.lower() in ["p", "pron", "pronounced", "pronunciado"]:
        Cond = "pronounced"
    elif cnd.lower() in ["i", "in", "inner", "interno"]:
        Cond = "inner"
    elif cnd.lower() in ["v", "vis", "visualized", "visualizado"]:
        Cond = "visualized"
    else:
        raise InvalidSelectionError("Wrong name of condition!")
    return Cond


def map_class(cl: str) -> str:
    """
    Map different representations of class labels to a standard set of labels.

    Parameters:
    - cl (str): The input class label.

    Returns:
    - str: The standardized class label.
    """
    if not cl:
        raise InvalidSelectionError("Class is empty!")

    if cl.lower() in ["a", "all", "todos"]:
        Class = "all"
    elif cl.lower() in ["u", "up", "ar", "arriba"]:
        Class = "up"
    elif cl.lower() in ["d", "down", "ab", "abajo"]:
        Class = "down"
    elif cl.lower() in ["l", "left", "i", "izq", "izquierda"]:
        Class = "left"
    elif cl.lower() in ["r", "right", "d", "der", "derecha"]:
        Class = "right"
    else:
        raise InvalidSelectionError("Wrong name of class!")

    return Class


def sub_name(N_S: int) -> str:
    """
    Standardize subjects' names based on the input subject number.

    Parameters:
    - N_S (int): The subject number.

    Returns:
    - str: The standardized subject name.
    """
    return "sub-0" + str(N_S) if N_S < 10 else "sub-" + str(N_S)


def find_project_root(start: str | Path) -> Path:
    """
    Return the folder that contains this repository (and, by default, the
    ``ds003626`` dataset), searching upwards from ``start``.

    The repository is recognised by its ``Python_Processing`` folder, so the
    result is the same whether ``start`` is the repository root,
    ``Python_Processing`` or any folder inside it.

    Raises:
    - FileNotFoundError: If no parent of ``start`` contains ``Python_Processing``.
    """
    start = Path(start).resolve()
    for folder in (start, *start.parents):
        if (folder / "Python_Processing").is_dir():
            return folder.parent
    raise FileNotFoundError(
        f"Could not find the Inner_Speech_Dataset repository above {start}. "
        "Run the script from inside the repository or set data_dir explicitly."
    )
