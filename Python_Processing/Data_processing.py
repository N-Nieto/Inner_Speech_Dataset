# -*- coding: utf-8 -*-

"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Data processing
"""
# Imports
import numpy as np
from typing import Tuple


def calculate_power_windowed(signal_data: np.ndarray, fc: int,
                             window_len: float, window_step: float,
                             t_min: float, t_max: float
                             ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate power in a windowed manner for a given signal.

    Parameters:
    - signal_data (np.ndarray): The input signal data.
    - fc (int): Sampling frequency of the signal.
    - window_len (float): Length of the window in seconds.
    - window_step (float): Step size between windows in seconds.
    - t_min (float): Minimum time for cropping the signal.
    - t_max (float): Maximum time for cropping the signal.

    Returns:
    - tuple: A tuple containing the mean power
             and standard deviation of the power.
    """
    # Signal crop in time
    initial_sample = round(t_min * fc)
    last_sample = round(t_max * fc)

    # Window parameters
    fc_window_len = round(fc * window_len)
    fc_window_step = round(fc * window_step)

    # Initializations
    power = []
    final_sample = 0
    n_vent = 0

    # Main loop
    while final_sample <= last_sample:
        final_sample = initial_sample + fc_window_len

        # Window signal
        signal_cut = signal_data[initial_sample:final_sample]

        # Calculate the energy of the window signal
        pwr = np.sum(signal_cut**2, axis=0) / signal_cut.size

        # Update new initial sample for the next window
        initial_sample = initial_sample + fc_window_step

        power.append(pwr)
        n_vent += 1

    m_power = np.mean(power, axis=0)
    std_power = np.std(power, axis=0)

    return m_power, std_power


def select_time_window(X: np.ndarray, t_start: float = 1,
                       t_end: float = 2.5, fs: int = 256) -> np.ndarray:
    """
    Select a time window from the input data.

    Parameters:
    - X (np.ndarray): The input data.
    - t_start (float): Start time of the window in seconds.
    - t_end (float): End time of the window in seconds.
    - fs (int): Sampling frequency of the data.

    Returns:
    - np.ndarray: The selected time window.
    """
    t_max = X.shape[2]
    start = max(round(t_start * fs), 0)
    end = min(round(t_end * fs), t_max)

    # Copy interval
    X = X[:, :, start:end]
    return X


def filter_by_condition(X: np.ndarray, Y: np.ndarray, condition: str) -> tuple:
    """
    Filter data based on a specified condition.

    Parameters:
    - X (np.ndarray): Input data.
    - Y (np.ndarray): Labels or events corresponding to the input data.
    - condition (str): The condition to filter the data.

    Returns:
    - tuple: A tuple containing the filtered X and Y arrays.
    """
    if not condition:
        raise ValueError("You have to select the conditions!")

    condition_upper = condition.upper()

    if condition_upper == "ALL":
        return X, Y
    else:
        if condition_upper in {"PRON", "PRONOUNCED"}:
            p = 0
        elif condition_upper in {"IN", "INNER"}:
            p = 1
        elif condition_upper in {"VIS", "VISUALIZED"}:
            p = 2
        else:
            raise ValueError(f"The condition '{condition}' doesn't exist!")

        X_r = X[Y[:, 2] == p]
        Y_r = Y[Y[:, 2] == p]

    return X_r, Y_r


def transform_for_classificator(X: np.ndarray, Y: np.ndarray,
                                classes: list, conditions: list) -> tuple:
    """
    Transform data for a classifier based on specified classes and conditions.

    Parameters:
    - X (np.ndarray): Input data.
    - Y (np.ndarray): Labels or events corresponding to the input data.
    - classes (list): List of classes for each condition.
    - conditions (list): List of conditions for each class.

    Returns:
    - tuple: A tuple containing the transformed X and Y arrays.
    """
    n_groups_cnd = len(conditions)
    n_groups_cls = len(classes)

    if n_groups_cnd < 1 or n_groups_cls < 1:
        raise ValueError("You have to select classes and conditions")

    if n_groups_cnd != n_groups_cls:
        raise ValueError("Incorrect number of conditions or classes")

    for n_group in range(n_groups_cnd):
        n_ind_cond = len(conditions[n_group])
        n_ind_cls = len(classes[n_group])

        if n_ind_cond < 1 or n_ind_cls < 1:
            raise ValueError("You have to select classes for each condition")

        if n_ind_cond != n_ind_cls:
            raise ValueError("Incorrect number of conditions or classes")

        for n_ind in range(n_ind_cls):
            condition = conditions[n_group][n_ind]
            class_label = classes[n_group][n_ind]

            try:
                X_aux, Y_aux = filter_by_condition(X, Y, condition)
                X_aux, Y_aux = filter_by_class(X_aux, Y_aux, class_label)
            except Exception as ex:
                raise ex

            if n_ind == 0 and n_group == 0:
                X_final = X_aux
                Y_final = n_group * np.ones(len(Y_aux))
            else:
                X_final = np.vstack([X_final, X_aux])
                Y_final = np.hstack([Y_final, n_group * np.ones(len(Y_aux))])

    return X_final, Y_final


# In[]
def average_in_frequency(power: np.ndarray, frequency: np.ndarray,
                         bands: list) -> np.ndarray:
    """
    Calculate the average power within specified frequency bands.

    Parameters:
    - power (np.ndarray): Power data.
    - frequency (np.ndarray): Frequency values.
    - bands (list): List of frequency bands.

    Returns:
    - np.ndarray: The averaged power within each frequency band.
    """
    n_bands = len(bands)

    for n_band in range(n_bands):
        f_min, f_max = bands[n_band]

        index = np.logical_and(frequency > f_min, frequency < f_max)

        pow_select = power[:, index, :]

        power_band = np.average(pow_select, axis=1)
        power_band = np.reshape(power_band,
                                (power_band.shape[0], 1, power_band.shape[1]))

        if n_band == 0:
            power_bands = power_band
        else:
            power_bands = np.hstack((power_bands, power_band))

    return power_bands


def filter_by_class(X: np.ndarray, Y: np.ndarray,
                    class_condition: str) -> tuple:
    """
    Filter data based on a specified class condition.

    Parameters:
    - X (np.ndarray): Input data.
    - Y (np.ndarray): Labels or events corresponding to the input data.
    - class_condition (str): The class condition to filter the data.

    Returns:
    - tuple: A tuple containing the filtered X and Y arrays.
    """
    if not class_condition:
        raise ValueError("You have to select the classes for each condition!")

    class_condition_upper = class_condition.upper()

    if class_condition_upper == "ALL":
        return X, Y
    else:
        if class_condition_upper in {"UP", "ARRIBA"}:
            p = 0
        elif class_condition_upper in {"DOWN", "ABAJO"}:
            p = 1
        elif class_condition_upper in {"RIGHT", "DERECHA"}:
            p = 2
        elif class_condition_upper in {"LEFT", "IZQUIERDA"}:
            p = 3
        else:
            raise ValueError(f"The class '{class_condition}' doesn't exist!")

        X_r = X[Y[:, 1] == p]
        Y_r = Y[Y[:, 1] == p]

    return X_r, Y_r


def split_trial_in_time(X: np.ndarray, Y: np.ndarray, window_len: float,
                        window_step: float, fs: int) -> tuple:
    """
    Split trials in time based on specified window parameters.

    Parameters:
    - X (np.ndarray): Input data.
    - Y (np.ndarray): Labels or events corresponding to the input data.
    - window_len (float): Length of the window in seconds.
    - window_step (float): Step size between windows in seconds.
    - fs (int): Sampling frequency of the data.

    Returns:
    - tuple: A tuple containing the split X and Y arrays.
    """
    print("Input X shape:", X.shape)
    n_trials, _, t_max = X.shape

    # Window parameters
    fc_window_len = round(fs * window_len)

    # Split sections
    split_section = int(t_max // fc_window_len)

    # If there is a remainder, just drop it
    remainder = t_max % split_section

    if remainder != 0:
        X = X[:, :, :-remainder]

    # Initializations
    X_final = []
    # Set labels
    Y_final = np.repeat(Y, split_section, axis=0)

    # Main loop
    for n_tr in range(n_trials):
        x_t = X[n_tr, :, :]
        x_t = np.split(x_t, split_section, axis=1)
        x_t = np.array(x_t)
        if len(X_final) == 0:
            X_final = x_t
        else:
            X_final = np.vstack([X_final, x_t])

    print("Output X shape:", X_final.shape)
    return X_final, Y_final
