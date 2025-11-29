# -*- coding: utf-8 -*-
# %%
"""
@author: Nicolás Nieto

We present the pipeline for processing the Inner Speech dataset,
Convert the raw data into a structured dataset.

A processing is proposed.
The filter cut frequencies could be easily changed with the
variables Low_cut and High_cut.

A proposed ICA processing is implemented using MNE functions
"""

# Imports modules
import mne
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

from lib.events_analysis import (
    event_correction,
    add_condition_tag,
    add_block_tag,
    delete_trigger_column,
    check_baseline_tags,
    cognitive_control_check,
    standardize_labels,
)

from lib.data_extractions import (
    extract_subject_from_bdf,
)
from lib.utils import ensure_dir
from lib.AdHoc_modification import (
    adhoc_subject_3,
)
from lib.EMG_Control import EMG_control_single_th

project_root = Path().resolve().parents[1]
# %%
# Processing Variables

# Root where the raw data are stored (OpenNeuro name)
data_dir = project_root / "ds003626"

# Root where the structured data will be saved
# It can be changed and saved in other direction
save_dir = data_dir / "derivatives"

# Subjects and blacks
N_Subj_arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
N_block_arr = [1, 2, 3]

# #################### Filtering
# Cut-off frequencies
Low_cut = 0.5
High_cut = 100

# Notch filter in 50Hz
Notch_bool = True

# Downsampling rate
DS_rate = 4

# #################### ICA
# If False, ICA is not applyed
ICA_bool = False
ICA_Components = None
ica_random_state = 23
ica_method = "infomax"
max_pca_components = None
fit_params = dict(extended=True)

# #################### EMG Control
low_f = 1
high_f = 20
# Slide window desing
# Window len (time in sec)
window_len = 0.5
# slide window step (time in sec)
window_step = 0.05

# Threshold for EMG control
std_times = 3

# Baseline
t_min_baseline = 0
t_max_baseline = 15

# Trial time
t_min = 1
t_max = 3.5

# In[]: Fixed Variables
# Events ID
# Trials tag for each class.
# 31 = Arriba / Up
# 32 = Abajo / Down
# 33 = Derecha / Right
# 34 = Izquierda / Left
event_id = dict(Arriba=31, Abajo=32, Derecha=33, Izquierda=34)

# Baseline id
baseline_id = dict(Baseline=13)

# Report initialization
report = dict(Age=0, Gender=0, Recording_time=0, Ans_R=0, Ans_W=0)

# Montage
Adquisition_eq = "biosemi128"
# Get montage
montage = mne.channels.make_standard_montage(Adquisition_eq)

# Extern channels
Ref_channels = ["EXG1", "EXG2"]

# Gaze detection
Gaze_channels = ["EXG3", "EXG4"]

# Blinks detection
Blinks_channels = ["EXG5", "EXG6"]

# Mouth Moving detection
Mouth_channels = ["EXG7", "EXG8"]

# Demographic information
Subject_age = [56, 50, 34, 24, 31, 29, 26, 28, 35, 31]

Subject_gender = ["F", "M", "M", "F", "F", "M", "M", "F", "M", "M"]

# In[] = Processing loop

for N_S in N_Subj_arr:
    # Get Age and Gender
    report["Age"] = Subject_age[N_S - 1]
    report["Gender"] = Subject_gender[N_S - 1]

    for N_B in N_block_arr:
        print("Subject: " + str(N_S))
        print("Session: " + str(N_B))

        # Load data from BDF file
        rawdata, Num_s = extract_subject_from_bdf(data_dir, N_S, N_B)

        # Referencing
        rawdata.set_eeg_reference(ref_channels=Ref_channels)

        if Notch_bool:
            # Notch filter
            rawdata = mne.io.Raw.notch_filter(rawdata, freqs=50)

        # Filtering raw data
        rawdata.filter(Low_cut, High_cut)

        # Get events
        # Subject 10  on Block 1 have a spureos trigger
        if N_S == 10 and N_B == 1:
            events = mne.find_events(
                rawdata, initial_event=True, consecutive=True, min_duration=0.002
            )
            # The different load of the events delet
            # the spureos trigger but also the Baseline finish mark
        else:
            events = mne.find_events(rawdata, initial_event=True, consecutive=True)

        events = pd.DataFrame(events, columns=["Time", "Trigger", "Code"])

        events = check_baseline_tags(events)

        # Check and Correct event
        events = event_correction(events=events)

        event_array = events.to_numpy()
        event_array = np.array(event_array, dtype=int)
        # replace the raw events with the new corrected events
        rawdata.event = event_array

        report["Recording_time"] = int(
            np.round(rawdata.last_samp / rawdata.info["sfreq"])
        )  # noqa

        # Cognitive Control
        report["Ans_R"], report["Ans_W"] = cognitive_control_check(events)

        # Save report
        file_path = save_dir / (Num_s + "/ses-0" + str(N_B))
        ensure_dir(str(file_path))
        file_name = file_path / (Num_s + "_ses-0" + str(N_B) + "_report.pkl")
        with open(file_name, "wb") as output:
            pickle.dump(report, output, pickle.HIGHEST_PROTOCOL)

        print("Processing EXG")
        # EXG
        #  the EXG Channels for saving
        picks_eog = mne.pick_types(
            rawdata.info,
            eeg=False,
            stim=False,
            include=["EXG1", "EXG2", "EXG3", "EXG4", "EXG5", "EXG6", "EXG7", "EXG8"],
        )
        epochsEOG = mne.Epochs(
            rawdata,
            event_array,
            event_id=event_id,
            tmin=-0.5,
            tmax=4,
            picks=picks_eog,
            preload=True,
            detrend=0,
            decim=DS_rate,
        )

        # Save EOG
        file_name = file_path / (Num_s + "_ses-0" + str(N_B) + "_exg-epo.fif")
        epochsEOG.save(file_name, fmt="double", split_size="2GB", overwrite=True)
        del epochsEOG
        print("EXG Saved")
        print("Processing Baseline")
        # Baseline
        # Extract Baseline
        # Calculate the Baseline time
        t_baseline = (
            event_array[event_array[:, 2] == 14, 0]
            - event_array[event_array[:, 2] == 13, 0]
        ) / rawdata.info["sfreq"]  # noqa
        t_baseline = t_baseline[0]
        Baseline = mne.Epochs(
            rawdata,
            event_array,
            event_id=baseline_id,
            tmin=0,
            tmax=round(t_baseline),
            picks="all",
            preload=True,
            detrend=0,
            decim=DS_rate,
            baseline=None,
        )

        # Save Baseline
        file_name = file_path / (Num_s + "_ses-0" + str(N_B) + "_baseline-epo.fif")
        Baseline.save(file_name, fmt="double", split_size="2GB", overwrite=True)
        del Baseline
        print("Baseline Saved")
        print("Processing EEG")
        # Epoching and decimating EEG
        picks_eeg = mne.pick_types(
            rawdata.info,
            eeg=True,
            exclude=["EXG1", "EXG2", "EXG3", "EXG4", "EXG5", "EXG6", "EXG7", "EXG8"],
            stim=False,
        )

        epochsEEG = mne.Epochs(
            rawdata,
            event_array,
            event_id=event_id,
            tmin=-0.5,
            tmax=4,
            picks=picks_eeg,
            preload=True,
            detrend=0,
            decim=DS_rate,
            baseline=None,
        )

        # ICA Prosessing

        if ICA_bool:
            # Get a full trials including EXG channels
            picks_vir = mne.pick_types(
                rawdata.info,
                eeg=True,
                include=[
                    "EXG1",
                    "EXG2",
                    "EXG3",
                    "EXG4",
                    "EXG5",
                    "EXG6",
                    "EXG7",
                    "EXG8",
                ],
                stim=False,
            )
            epochsEEG_full = mne.Epochs(
                rawdata,
                event_array,
                event_id=event_id,
                tmin=-0.5,
                tmax=4,
                picks=picks_vir,
                preload=True,
                detrend=0,
                decim=DS_rate,
                baseline=None,
            )

            # Liberate Memory for ICA processing
            del rawdata

            # Creating the ICA object
            ica = mne.preprocessing.ICA(
                n_components=ICA_Components,
                random_state=ica_random_state,
                method=ica_method,
                fit_params=fit_params,
            )

            # Fit ICA, calculate components
            ica.fit(epochsEEG)
            ica.exclude = []

            # Detect sources by correlation
            exg_inds_EXG3, scores_ica = ica.find_bads_eog(
                epochsEEG_full, ch_name="EXG3"
            )
            ica.exclude.extend(exg_inds_EXG3)

            # Detect sources by correlation
            exg_inds_EXG4, scores_ica = ica.find_bads_eog(
                epochsEEG_full, ch_name="EXG4"
            )
            ica.exclude.extend(exg_inds_EXG4)

            # Detect sources by correlation
            exg_inds_EXG5, scores_ica = ica.find_bads_eog(
                epochsEEG_full, ch_name="EXG5"
            )
            ica.exclude.extend(exg_inds_EXG5)

            # Detect sources by correlation
            exg_inds_EXG6, scores_ica = ica.find_bads_eog(
                epochsEEG_full, ch_name="EXG6"
            )
            ica.exclude.extend(exg_inds_EXG6)

            # Detect sources by correlation
            exg_inds_EXG7, scores_ica = ica.find_bads_eog(
                epochsEEG_full, ch_name="EXG7"
            )
            ica.exclude.extend(exg_inds_EXG7)

            # Detect sources by correlation
            exg_inds_EXG8, scores_ica = ica.find_bads_eog(
                epochsEEG_full, ch_name="EXG8"
            )
            ica.exclude.extend(exg_inds_EXG8)

            print("Appling ICA")
            ica.apply(epochsEEG)

        # Save EEG
        file_name = file_path / (Num_s + "_ses-0" + str(N_B) + "_eeg-epo.fif")
        epochsEEG.save(file_name, fmt="double", split_size="2GB", overwrite=True)

        # Standarize and save events
        events = add_condition_tag(events)
        events = add_block_tag(events, N_B=N_B)
        events = delete_trigger_column(events)
        events = standardize_labels(events)

        # Save events
        file_name = file_path / (Num_s + "_ses-0" + str(N_B) + "_events.dat")
        events.to_csv(file_name)

if 3 in N_Subj_arr:
    #  Ad Hoc Modifications
    adhoc_subject_3(root_dir=data_dir)

# EMG Control
EMG_control_single_th(
    root_dir=data_dir,
    N_Subj_arr=N_Subj_arr,
    N_block_arr=N_block_arr,
    low_f=low_f,
    high_f=high_f,
    t_min=t_min,
    t_max=t_max,
    window_len=window_len,
    window_step=window_step,
    std_times=std_times,
    t_min_baseline=t_min_baseline,
    t_max_baseline=t_max_baseline,
)

# %%
