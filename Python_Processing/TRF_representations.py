# -*- coding: utf-8 -*-

"""
@author: Nicolás Nieto - nnieto

Time Frecuency Representations
"""
# Imports modules

import mne
import numpy as np

from mne.time_frequency import tfr_multitaper, tfr_morlet
from Data_extractions import extract_block_data_from_subject
from Data_extractions import extract_data_from_subject
from Data_processing import filter_by_condition, filter_by_class
from Utilitys import ensure_dir, unify_names

# Processing Variables

# Root where the data are stored
root_dir = "../"
save_dir = "../"

# Save options
save_bool = True
overwrite = True

# Subjets list
N_S_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Data filtering
datatype = "EEG"
# All - Pron - Inner - Vis
Conditions_list = ["All", "Pron", "Inner", "Vis"]
# All - Up - Down - Right - Left
Classes_list = ["All"]

# Fix all random states
random_state = 23
np.random.seed(random_state)

# Time Frecuency Representation Parameters
TFR_method = "Morlet"             # Multitaper - Morlet
fmin = 0.5
fmax = 100
n_steps = 300
average = True
return_itc = True
use_fft = False
decim = 1
n_jobs = 1
picks = "all"

freqs = np.logspace(*np.log10([fmin, fmax]), num=n_steps)
n_cycles = freqs

# Only used in Morlet
zero_mean = True

# In[]: Main Loop

# Load a single subject to use the Epoched Object structure
N_B = 1
N_S = 1
X_S, Y = extract_block_data_from_subject(root_dir, N_S, datatype, N_B=N_B)

# Set Montage
Adquisition_eq = "biosemi128"
montage = mne.channels.make_standard_montage(Adquisition_eq)
X_S.set_montage(montage)

for Classes in Classes_list:
    for Cond in Conditions_list:
        count = 1
        for N_S in N_S_list:

            # Load full subject's data
            X_s, Y = extract_data_from_subject(root_dir, N_S, datatype)

            # Filter by condition
            X_cond, Y_cond = filter_by_condition(X_s, Y, Condition=Cond)

            # Filter by class
            X_cond, Y_cond = filter_by_class(X_cond, Y_cond, Class=Classes)

            # Stack trial for every subject
            if count == 1:
                # Inicialiced
                X_data = X_cond
                count = 2
            else:
                # Stack trials
                X_data = np.vstack((X_data, X_cond))

        # Calculated TFR for a particular clase in
        # a particular condition for the selected subjects
        print("Calculated " + TFR_method + " for Class: " + Classes + " in Condition: " + Cond )            # noqa
        print("with the information of Subjects: " + str(N_S_list ))                                        # noqa

        # Create a subject with all trials
        X_S._data = X_data

        if TFR_method == "Multitaper":
            power, itc = tfr_multitaper(X_S, freqs=freqs, n_cycles=n_cycles,
                                        use_fft=use_fft, return_itc=return_itc,
                                        decim=decim, n_jobs=n_jobs,
                                        average=average, picks=picks)

            if save_bool:
                ensure_dir(save_dir)
                file_name = save_dir + TFR_method + "_" + Cond + "_" + Classes + "_power-tfr.h5"            # noqa
                power.save(fname=file_name, overwrite=overwrite)
                if return_itc:
                    file_name = save_dir + TFR_method + "_" + Cond + "_" + Classes + "_itc-tfr.h5"          # noqa
                    itc.save(fname=file_name, overwrite=overwrite)

        elif TFR_method == "Morlet":
            power, itc = tfr_morlet(X_S, freqs=freqs, n_cycles=n_cycles,
                                    use_fft=use_fft, return_itc=return_itc,
                                    decim=decim, n_jobs=n_jobs,
                                    average=average, zero_mean=zero_mean,
                                    picks=picks)
            if save_bool:
                ensure_dir(save_dir)
                Cond, Classes = unify_names(Cond, Class=Classes)
                file_name = save_dir + TFR_method + "_" + Cond + "_" + Classes + "_power-tfr.h5"            # noqa
                power.save(fname=file_name, overwrite=overwrite)

                if return_itc:
                    Cond, Classes = unify_names(Cond, Class=Classes)
                    file_name = save_dir + TFR_method + "_" + Cond + "_" + Classes + "_itc-tfr.h5"          # noqa
                    itc.save(fname=file_name, overwrite=overwrite)

        else:
            print("Invalid TFR_rep")
