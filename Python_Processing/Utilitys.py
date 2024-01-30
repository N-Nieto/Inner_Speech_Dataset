# -*- coding: utf-8 -*-

"""
@author: Nicolás Nieto
@email: nnieto@sinc.unl.edu.ar

Utilitys for Inner speech dataset prossesing
"""
import os


def ensure_dir(dir_name: str) -> None:
    """
    Ensure that the specified directory exists; if not, create it.

    Parameters:
    - dir_name (str): The directory path.

    Returns:
    - None
    """
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


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
        raise Exception("Invalid channels name")

    return picks


def unify_names(Cond: str, Class: str) -> tuple:
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
    if Cond.lower() == "inner" or Cond.lower() == "in":
        Cond = "Inner"
    elif Cond.lower() == "vis" or Cond.lower() == "visualized":
        Cond = "Vis"
    elif Cond.lower() == "pron" or Cond.lower() == "pronounced":
        Cond = "Pron"

    # Unify class names
    if Class.lower() == "all" or Class.lower() == "todo":
        Class = "All"
    elif Class.lower() == "up" or Class.lower() == "arriba":
        Class = "Up"
    elif Class.lower() == "down" or Class.lower() == "abajo":
        Class = "Down"
    elif Class.lower() == "right" or Class.lower() == "derecha":
        Class = "Right"
    elif Class.lower() == "left" or Class.lower() == "izquierda":
        Class = "Left"

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
        raise Exception("Condition is empty!")

    if cnd.upper() in ["A", "ALL"]:
        return "ALL"
    if cnd.upper() in ["P", "PRON", "PRONOUNCED"]:
        return "PRONOUNCED"
    if cnd.upper() in ["I", "IN", "INNER"]:
        return "INNER"
    if cnd.upper() in ["V", "VIS", "VISUALIZED"]:
        return "VISUALIZED"

    raise Exception("Wrong name of condition!")


def map_class(cl: str) -> str:
    """
    Map different representations of class labels to a standard set of labels.

    Parameters:
    - cl (str): The input class label.

    Returns:
    - str: The standardized class label.
    """
    if not cl:
        raise Exception("Class is empty!")

    if cl.upper() in ["ALL", "TODOS"]:
        return "ALL"
    if cl.upper() in ["U", "UP", "AR", "ARRIBA"]:
        return "UP"
    if cl.upper() in ["D", "DOWN", "AB", "ABAJO"]:
        return "DOWN"
    if cl.upper() in ["L", "LEFT", "I", "IZQ", "IZQUIERDA"]:
        return "LEFT"
    if cl.upper() in ["R", "RIGHT", "D", "DER", "DERECHA"]:
        return "RIGHT"

    raise Exception("Wrong name of class!")


def sub_name(N_S: int) -> str:
    """
    Standardize subjects' names based on the input subject number.

    Parameters:
    - N_S (int): The subject number.

    Returns:
    - str: The standardized subject name.
    """
    if N_S < 10:
        Num_s = 'sub-0' + str(N_S)
    else:
        Num_s = 'sub-' + str(N_S)

    return Num_s
