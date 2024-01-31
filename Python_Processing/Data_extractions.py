# -*- coding: utf-8 -*-

"""
@author: Nieto Nicolás
@email: nnieto@sinc.unl.edu.ar

Utilitys from extract, read and load data from Inner Speech Dataset
"""

import mne
import gc
import os
import numpy as np
from Inner_Speech_Dataset.Python_Processing.Utilitys import sub_name, unify_names       # noqa
import pickle
from mne.io import Raw


def extract_subject_from_bdf(root_dir: str, n_s:
                             int, n_b: int) -> tuple[Raw, str]:
    """
    Extracts raw EEG data from a BDF file for a specific subject and block.

    Parameters:
    - root_dir (str): The root directory containing the data.
    - n_s (int): The subject number.
    - n_b (int): The block number.

    Returns:
    - tuple: A tuple containing raw EEG data and the corrected subject name.
    """
    # Name correction if N_Subj is less than 10
    num_s = sub_name(n_s)

    # Load data
    file_name = (
        f"{root_dir}/{num_s}/ses-0{n_b}/eeg/{num_s}_ses-0{n_b}_task-innerspeech_eeg.bdf"        # noqa
    )
    raw_data = mne.io.read_raw_bdf(input_fname=file_name, preload=True,
                                   verbose='WARNING')

    return raw_data, num_s


def extract_data_from_subject(root_dir: str, n_s: int, datatype: str) -> tuple:
    """
    Load all blocks for one subject and stack the results in X.

    Parameters:
    - root_dir (str): The root directory containing the data.
    - n_s (int): The subject number.
    - datatype (str): The type of data to extract ("eeg", "exg", or "baseline")

    Returns:
    - tuple: A tuple containing the stacked data (X) and events (Y).
    """
    data = dict()
    y = dict()
    n_b_arr = [1, 2, 3]
    datatype = datatype.lower()

    for n_b in n_b_arr:
        # Name correction if N_Subj is less than 10
        num_s = sub_name(n_s)

        y[n_b] = load_events(root_dir, n_s, n_b)

        if datatype == "eeg":
            # Load data and events
            file_name = (
                f"{root_dir}/derivatives/{num_s}/ses-0{n_b}/{num_s}_ses-0{n_b}_eeg-epo.fif"             # noqa
            )
            X = mne.read_epochs(file_name, verbose='WARNING')
            data[n_b] = X._data

        elif datatype == "exg":
            file_name = (
                f"{root_dir}/derivatives/{num_s}/ses-0{n_b}/{num_s}_ses-0{n_b}_exg-epo.fif"             # noqa
            )
            X = mne.read_epochs(file_name, verbose='WARNING')
            data[n_b] = X._data

        elif datatype == "baseline":
            file_name = (
                f"{root_dir}/derivatives/{num_s}/ses-0{n_b}/{num_s}_ses-0{n_b}_baseline-epo.fif"        # noqa
            )
            X = mne.read_epochs(file_name, verbose='WARNING')
            data[n_b] = X._data

        else:
            raise ValueError("Invalid Datatype")

    X_stacked = np.vstack((data[1], data[2], data[3]))
    Y_stacked = np.vstack((y[1], y[2], y[3]))

    return X_stacked, Y_stacked


def extract_block_data_from_subject(root_dir: str, n_s: int,
                                    datatype: str, n_b: int) -> tuple:
    """
    Load selected block from one subject.

    Parameters:
    - root_dir (str): The root directory containing the data.
    - n_s (int): The subject number.
    - datatype (str): The type of data to extract ("eeg", "exg", or "baseline")
    - n_b (int): The block number.

    Returns:
    - tuple: A tuple containing the loaded data (X) and events (Y).
    """
    # Get subject name
    num_s = sub_name(n_s)

    # Get events
    y = load_events(root_dir, n_s, n_b)

    sub_dir = f"{root_dir}/derivatives/{num_s}/ses-0{n_b}/{num_s}_ses-0{n_b}"

    if datatype == "eeg":
        # Load EEG data
        file_name = f"{sub_dir}_eeg-epo.fif"
        X = mne.read_epochs(file_name, verbose='WARNING')

    elif datatype == "exg":
        # Load EXG data
        file_name = f"{sub_dir}_exg-epo.fif"
        X = mne.read_epochs(file_name, verbose='WARNING')

    elif datatype == "baseline":
        # Load Baseline data
        file_name = f"{sub_dir}_baseline-epo.fif"
        X = mne.read_epochs(file_name, verbose='WARNING')

    else:
        raise ValueError("Invalid Datatype")

    return X, y


def extract_report(root_dir: str, n_b: int, n_s: int):
    """
    Extract a report for a specific block and subject.

    Parameters:
    - root_dir (str): The root directory containing the data.
    - n_b (int): The block number.
    - n_s (int): The subject number.

    Returns:
    - dict: The loaded report.
    """
    # Get subject name
    num_s = sub_name(n_s)

    # Save report
    sub_dir = f"{root_dir}/derivatives/{num_s}/ses-0{n_b}/{num_s}_ses-0{n_b}"
    file_name = f"{sub_dir}_report.pkl"

    with open(file_name, 'rb') as input_file:
        report = pickle.load(input_file)

    return report


def extract_tfr(trf_dir: str, cond: str, class_label: str,
                tfr_method: str, trf_type: str) -> mne.time_frequency:
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

    fname = f"{trf_dir}{tfr_method}_{cond}_{class_label}_{trf_type}-tfr.h5"

    trf = mne.time_frequency.read_tfrs(fname)[0]

    return trf


def extract_data_multisubject(root_dir: str, n_s_list: list,
                              datatype: str = 'eeg') -> tuple:
    """
    Load all blocks for a list of subjects and stack the results.

    Parameters:
    - root_dir (str): The root directory containing the data.
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
    s = 0
    datatype = datatype.lower()

    for n_s in n_s_list:
        print("Iteration ", s)
        print("Subject ", n_s)
        for n_b in n_b_arr:
            num_s = sub_name(n_s)

            base_file_name = f"{root_dir}/derivatives/{num_s}/ses-0{n_b}/{num_s}_ses-0{n_b}"            # noqa
            events_file_name = f"{base_file_name}_events.dat"
            data_tmp_Y = np.load(events_file_name, allow_pickle=True)
            tmp_list_Y.append(data_tmp_Y)
            print("Inner iteration ", n_b)

            if datatype == "eeg" or datatype == "exg" or datatype == "baseline":                        # noqa
                # Load data and events
                data_tmp_X = None

                if datatype == "eeg":
                    eeg_file_name = f"{base_file_name}_eeg-epo.fif"
                    data_tmp_X = mne.read_epochs(eeg_file_name, verbose='WARNING')._data                # noqa
                elif datatype == "exg":
                    exg_file_name = f"{base_file_name}_exg-epo.fif"
                    data_tmp_X = mne.read_epochs(exg_file_name, verbose='WARNING')._data                # noqa
                elif datatype == "baseline":
                    baseline_file_name = f"{base_file_name}_baseline-epo.fif"
                    data_tmp_X = mne.read_epochs(baseline_file_name, verbose='WARNING')._data           # noqa

                if data_tmp_X is not None:
                    rows.append(data_tmp_X.shape[0])
                    # assume same number of channels, time steps, and column
                    # labels in every subject and session
                    if s == 0 and n_b == 1:
                        chann = data_tmp_X.shape[1]
                        steps = data_tmp_X.shape[2]
                        columns = data_tmp_Y.shape[1]

                    tmp_list_X.append(data_tmp_X)
                else:
                    raise ValueError("Invalid Datatype")
                    return None, None

        s += 1

    x = np.empty((sum(rows), chann, steps))
    y = np.empty((sum(rows), columns))
    offset = 0

    # Put elements of the list into numpy array
    for i in range(total_elem):
        print("Saving element {} into array ".format(i))
        x[offset:offset + rows[i], :, :] = tmp_list_X[0]

        if datatype == "eeg" or datatype == "exg":
            # only build Y for the datatypes that use it
            y[offset:offset + rows[i], :] = tmp_list_Y[0]

        offset += rows[i]
        del tmp_list_X[0]
        del tmp_list_Y[0]
        gc.collect()

    print("X shape", x.shape)
    print("Y shape", y.shape)

    if datatype == "eeg" or datatype == "exg":
        # For eeg and exg types, there is a predefined label that is returned
        return x, y
    else:
        # For baseline datatypes, there's no such label (rest phase)
        return x


def load_events(root_dir: str, n_s: int, n_b: int):
    """
    Load events data for a specific subject and block.

    Parameters:
    - root_dir (str): The root directory containing the data.
    - n_s (int): The subject number.
    - n_b (int): The block number.

    Returns:
    - np.ndarray: The loaded events.
    """
    num_s = sub_name(n_s)

    # Create file name
    file_name = os.path.join(root_dir, "derivatives", num_s, f"ses-0{n_b}", f"{num_s}_ses-0{n_b}_events.dat")       # noqa

    # Load events
    events = np.load(file_name, allow_pickle=True)

    return events
