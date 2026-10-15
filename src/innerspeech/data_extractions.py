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

from innerspeech import derivatives_io
from innerspeech.data_processing import filter_by_class, filter_by_condition
from innerspeech.derivatives_io import derivative_path, session_label, subject_label
from innerspeech.utils import unify_names

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


def tfr_path(
    tfr_dir: str | Path, cond: str, class_label: str, tfr_method: str, tfr_type: str
) -> Path:
    """
    Path of a time-frequency result written by ``TFR_representations.py``:
    ``<tfr_dir>/<method>_<cond>_<class>_<type>-tfr.h5``.

    Parameters:
    - tfr_dir (Path): Folder with the TFR results.
    - cond (str): Condition (e.g. "all", "pron", "inner", "vis"; aliases accepted).
    - class_label (str): Class (e.g. "all", "up", "down", "right", "left").
    - tfr_method (str): "Morlet" or "Multitaper".
    - tfr_type (str): "power" or "itc".
    """
    cond, class_label = unify_names(cond, class_label)
    return Path(tfr_dir) / f"{tfr_method}_{cond}_{class_label}_{tfr_type}-tfr.h5"


def extract_tfr(
    tfr_dir: str | Path, cond: str, class_label: str, tfr_method: str, tfr_type: str
) -> mne.time_frequency.AverageTFR:
    """
    Load a time-frequency result written by ``TFR_representations.py``.

    Parameters are the same as for ``tfr_path``.

    Returns:
    - mne.time_frequency.AverageTFR: The stored power or ITC.
    """
    tfr = mne.time_frequency.read_tfrs(
        tfr_path(tfr_dir, cond, class_label, tfr_method, tfr_type)
    )
    # Depending on the MNE version a single TFR or a list with one is returned
    return tfr[0] if isinstance(tfr, list) else tfr


def psd_path(psd_dir: str | Path, cond: str, class_label: str) -> Path:
    """Path of a PSD result written by ``PSD_representation.py``."""
    cond, class_label = unify_names(cond, class_label)
    return Path(psd_dir) / f"PSD_{cond}_{class_label}-psd.h5"


def extract_condition_epochs(
    root_dir: str | Path,
    subjects: list[int],
    datatype: str = "eeg",
    condition: str = "all",
    class_label: str = "all",
    montage: str | None = "biosemi128",
) -> mne.EpochsArray:
    """
    Load the trials of one condition and class for several subjects (all three
    sessions each) into a single ``mne.EpochsArray``.

    The channel information, sampling rate and time axis are taken from the
    stored ``*-epo.fif`` files, so the result can be used with any MNE method
    (``compute_psd``, ``compute_tfr``, ``average``, ...).

    Parameters:
    - root_dir (Path): The ``ds003626`` folder (containing ``derivatives``).
    - subjects (list of int): Subject numbers.
    - datatype (str): "eeg", "exg" or "baseline".
    - condition (str): "all", "pron", "inner" or "vis" (aliases accepted).
    - class_label (str): "all", "up", "down", "right" or "left".
    - montage (str or None): Standard montage to attach (EEG only).

    Returns:
    - mne.EpochsArray: The selected trials. ``epochs.metadata`` holds the
      subject, session, class and condition of every trial; the event codes are
      the class (0 = up, 1 = down, 2 = right, 3 = left) plus one.
    """
    if not subjects:
        raise ValueError("Select at least one subject.")

    template = mne.read_epochs(
        _epochs_path(root_dir, subjects[0], 1, datatype),
        preload=False,
        verbose="WARNING",
    )
    info = template.info.copy()
    if montage is not None and datatype.lower() == "eeg":
        info.set_montage(montage, on_missing="ignore")

    data, labels, subject_ids = [], [], []
    for n_s in subjects:
        X, Y = extract_data_from_subject(root_dir, n_s, datatype)
        X, Y = filter_by_condition(X, Y, condition)
        X, Y = filter_by_class(X, Y, class_label)
        data.append(X)
        labels.append(Y)
        subject_ids.append(np.full(len(Y), n_s))

    data = np.concatenate(data)
    labels = np.concatenate(labels).astype(int)
    if len(data) == 0:
        raise ValueError(
            f"No trials for condition={condition!r}, class={class_label!r} "
            f"in subjects {subjects}."
        )

    class_names = ("up", "down", "right", "left")
    events = np.column_stack(
        [np.arange(len(labels)), np.zeros(len(labels), int), labels[:, 1] + 1]
    )
    event_id = {class_names[c]: c + 1 for c in np.unique(labels[:, 1])}
    metadata = pd.DataFrame(
        {
            "subject": np.concatenate(subject_ids),
            "session": labels[:, 3],
            "class": labels[:, 1],
            "condition": labels[:, 2],
        }
    )
    return mne.EpochsArray(
        data,
        info,
        events=events,
        tmin=template.tmin,
        event_id=event_id,
        metadata=metadata,
        baseline=None,
        verbose="WARNING",
    )


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
    Subject_age = [56, 50, 34, 24, 30, 29, 26, 28, 35, 31];
    Subject_gender = ["F", "M", "M", "F", "F", "M", "M", "F", "M", "M"]

    Parameters:
    - N_S (int): The subject number.

    Returns:
    - tuple: A tuple containing the age (int) and gender (str) of the subject.
    """
    # Fixed demographic information
    # Table 1 of the paper (sub-05 is 30; releases up to 2.1.2 stored 31)
    Subject_age = [56, 50, 34, 24, 30, 29, 26, 28, 35, 31]
    Subject_gender = ["F", "M", "M", "F", "F", "M", "M", "F", "M", "M"]
    # Retrieve age and gender for the corresponding subject number
    age = Subject_age[N_S - 1]
    gender = Subject_gender[N_S - 1]
    return age, gender
