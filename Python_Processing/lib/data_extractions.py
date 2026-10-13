"""
@author: Nieto Nicolás
@email: nnieto@sinc.unl.edu.ar

Utilities from extract, read and load data from Inner Speech Dataset
"""

import gc
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from mne.io import Raw

from lib import derivatives_io
from lib.derivatives_io import derivative_path, session_label, subject_label
from lib.utils import unify_names

# datatype -> derivative file kind
_EPOCH_KINDS = {
    "eeg": "eeg-epo.fif",
    "exg": "exg-epo.fif",
    "baseline": "baseline-epo.fif",
}


def _derivatives_dir(root_dir: str | Path) -> Path:
    """``<root_dir>/derivatives`` (root_dir is the ``ds003626`` folder)."""
    return Path(root_dir) / "derivatives"


def _epochs_path(root_dir: str | Path, n_s: int, n_b: int, datatype: str) -> Path:
    kind = _EPOCH_KINDS.get(datatype.lower())
    if kind is None:
        raise ValueError("Invalid Datatype")
    return derivative_path(_derivatives_dir(root_dir), n_s, n_b, kind)


def extract_subject_from_bdf(data_dir: Path, n_s: int, n_b: int) -> tuple[Raw, str]:
    """
    Extracts raw EEG data from a BDF file for a specific subject and block.

    Parameters:
    - data_dir (Path): The ``ds003626`` folder containing the raw data.
    - n_s (int): The subject number.
    - n_b (int): The block number.

    Returns:
    - tuple: A tuple containing raw EEG data and the corrected subject name.
    """
    num_s = subject_label(n_s)
    ses = session_label(n_b)

    # Load data
    file_name = (
        Path(data_dir) / num_s / ses / "eeg" / f"{num_s}_{ses}_task-innerspeech_eeg.bdf"
    )
    raw_data = mne.io.read_raw_bdf(
        input_fname=file_name, preload=True, verbose="WARNING"
    )

    return raw_data, num_s


def extract_data_from_subject(root_dir: Path, n_s: int, datatype: str) -> tuple:
    """
    Load all blocks for one subject and stack the results in X.

    Parameters:
    - root_dir (Path): The ``ds003626`` folder (containing ``derivatives``).
    - n_s (int): The subject number.
    - datatype (str): The type of data to extract ("eeg", "exg", or "baseline")

    Returns:
    - tuple: A tuple containing the stacked data (X) and events (Y).
    """
    data = {}
    y = {}
    n_b_arr = [1, 2, 3]

    for n_b in n_b_arr:
        y[n_b] = load_events(root_dir, n_s, n_b)
        X = mne.read_epochs(
            _epochs_path(root_dir, n_s, n_b, datatype), verbose="WARNING"
        )
        data[n_b] = X._data

    X_stacked = np.vstack((data[1], data[2], data[3]))
    Y_stacked = np.vstack((y[1], y[2], y[3]))

    return X_stacked, Y_stacked


def extract_block_data_from_subject(
    root_dir: Path, n_s: int, datatype: str, n_b: int
) -> tuple:
    """
    Load selected block from one subject.

    Parameters:
    - root_dir (Path): The ``ds003626`` folder (containing ``derivatives``).
    - n_s (int): The subject number.
    - datatype (str): The type of data to extract ("eeg", "exg", or "baseline")
    - n_b (int): The block number.

    Returns:
    - tuple: A tuple containing the loaded data (X) and events (Y).
    """
    file_name = _epochs_path(root_dir, n_s, n_b, datatype)
    y = load_events(root_dir, n_s, n_b)
    X = mne.read_epochs(file_name, verbose="WARNING")
    return X, y


def extract_report(root_dir: Path, n_b: int, n_s: int) -> dict:
    """
    Extract a report for a specific block and subject.

    Parameters:
    - root_dir (Path): The ``ds003626`` folder (containing ``derivatives``).
    - n_b (int): The block number.
    - n_s (int): The subject number.

    Returns:
    - dict: The loaded report.
    """
    return derivatives_io.load_report(_derivatives_dir(root_dir), n_s, n_b)


def extract_tfr(
    trf_dir: Path, cond: str, class_label: str, tfr_method: str, trf_type: str
) -> mne.time_frequency:
    """
    Extract Time-Frequency Representation (TFR) data.

    Parameters:
    - trf_dir (str): The directory containing the TFR data.
    - cond (str): The condition.
    - class_label (str): The class label.
    - tfr_method (str): The TFR method used.
    - trf_type (str): The type of TRF.

    Returns:
    - mne.time_frequency.tfr.TFR: The extracted TFR data.
    """
    # Unify names as stored
    cond, class_label = unify_names(cond, class_label)

    fname = trf_dir / f"{tfr_method}_{cond}_{class_label}_{trf_type}-tfr.h5"

    return mne.time_frequency.read_tfrs(fname)[0]


def extract_data_multisubject(
    root_dir: Path, n_s_list: list, datatype: str = "eeg"
) -> tuple:
    """
    Load all blocks for a list of subjects and stack the results.

    Parameters:
    - root_dir (Path): The ``ds003626`` folder (containing ``derivatives``).
    - n_s_list (list): List of subject numbers.
    - datatype (str): The type of data to extract ("eeg", "exg", or "baseline")

    Returns:
    - tuple: Tuple containing the stacked data (X) and events (Y) if applicable
    """
    n_b_arr = [1, 2, 3]
    tmp_list_X = []
    tmp_list_Y = []
    rows = []
    total_elem = len(n_s_list) * 3  # assume 3 sessions per subject
    datatype = datatype.lower()

    for s, n_s in enumerate(n_s_list):
        print("Iteration ", s)
        print("Subject ", n_s)
        for n_b in n_b_arr:
            data_tmp_Y = load_events(root_dir, n_s, n_b)
            tmp_list_Y.append(data_tmp_Y)
            print("Inner iteration ", n_b)

            # Load data
            file_name = _epochs_path(root_dir, n_s, n_b, datatype)
            data_tmp_X = mne.read_epochs(file_name, verbose="WARNING")._data

            rows.append(data_tmp_X.shape[0])
            # assume same number of channels, time steps, and column
            # labels in every subject and session
            if s == 0 and n_b == 1:
                chann = data_tmp_X.shape[1]
                steps = data_tmp_X.shape[2]
                columns = data_tmp_Y.shape[1]

            tmp_list_X.append(data_tmp_X)

    x = np.empty((sum(rows), chann, steps))
    y = np.empty((sum(rows), columns))
    offset = 0

    # Put elements of the list into numpy array
    for i in range(total_elem):
        print(f"Saving element {i} into array ")
        x[offset : offset + rows[i], :, :] = tmp_list_X[0]

        if datatype == "eeg" or datatype == "exg":
            # only build Y for the datatypes that use it
            y[offset : offset + rows[i], :] = tmp_list_Y[0]

        offset += rows[i]
        del tmp_list_X[0]
        del tmp_list_Y[0]
        gc.collect()

    print("X shape", x.shape)
    print("Y shape", y.shape)

    if datatype == "eeg" or datatype == "exg":
        # For eeg and exg types, there is a predefined label that is returned
        return x, y
    # For baseline datatypes, there's no such label (rest phase)
    return x


def get_events_from_raw(rawdata, N_S, N_B):
    # Subject 10  on Block 1 have a spurious trigger
    if N_S == 10 and N_B == 1:
        events = mne.find_events(
            rawdata, initial_event=True, consecutive=True, min_duration=0.002
        )
        # The different load of the events deletes
        # the spurious trigger but also the Baseline finish mark
    else:
        events = mne.find_events(rawdata, initial_event=True, consecutive=True)

    return pd.DataFrame(events, columns=["Time", "Trigger", "Code"])


def load_events(root_dir: Path, n_s: int, n_b: int) -> np.ndarray:
    """
    Load events data for a specific subject and block.

    Parameters:
    - root_dir (Path): The ``ds003626`` folder (containing ``derivatives``).
    - n_s (int): The subject number.
    - n_b (int): The block number.

    Returns:
    - np.ndarray: ``(n_trials, 4)`` int array with columns
      ``[sample, class, condition, session]``.
    """
    return derivatives_io.load_events(_derivatives_dir(root_dir), n_s, n_b)


def get_age_gender(N_S: int) -> tuple[int, str]:
    """
    Retrieve the age and gender of a subject based on their subject number.

    Demographic information
    Subject_age = [56, 50, 34, 24, 31, 29, 26, 28, 35, 31];
    Subject_gender = ["F", "M", "M", "F", "F", "M", "M", "F", "M", "M"]

    Parameters:
    - N_S (int): The subject number.

    Returns:
    - tuple: A tuple containing the age (int) and gender (str) of the subject.
    """
    # Fixed demographic information
    Subject_age = [56, 50, 34, 24, 31, 29, 26, 28, 35, 31]
    Subject_gender = ["F", "M", "M", "F", "F", "M", "M", "F", "M", "M"]
    # Retrieve age and gender for the corresponding subject number
    age = Subject_age[N_S - 1]
    gender = Subject_gender[N_S - 1]
    return age, gender
