# -*- coding: utf-8 -*-
# %%
"""
@author: Nicolás Nieto

We present a processing pipeline for the Inner Speech dataset that converts raw data into a
structured BIDS-compliant dataset stored in the "derivatives" folder.

Prerequisites:
Ensure you have downloaded the dataset from OpenNeuro.
A helper script (Raw_data_download_tutorial.py) is available to facilitate downloading the raw data.
If you prefer not to reprocess the data, you can download the preprocessed derivatives directly using another script (Derivatives_download_tutorial.py).

Preprocessing Steps:
    1. Event extraction and correction
    2. EEG re-referencing
    3. 50 Hz notch filter (Argentina power line frequency)
    4. Bandpass filtering (low-cut and high-cut)
    5. ICA-FIX processing using all components (computationally intensive)
    6. Ad hoc correction for subjects who performed the tasks in another order
    7. EMG validation using single threshold
    8. Report generation and saving
"""

# Imports modules
import mne
import pickle
import numpy as np
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
    get_age_gender,
    get_events_from_raw,
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

# Subjects and blacks. Subjects range from 1 to 10 (no subject 0). Blocks range from 1 to 3, (no block 0)
N_Subj_arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
N_block_arr = [1, 2, 3]

# #################### Filtering
# Cut-off frequencies
FILTER_BOOL = True
LOW_CUT = 0.5
HIGH_CUT = 100

# Notch filter in 50Hz
NOTCH_BOOL = True

# Downsampling rate
DS_RATE = 4

# #################### ICA
# If False, ICA is not applyed
ICA_BOOL = False
ICA_COMPONENTS = None  # Use None to automatic selection
ICA_METHOD = "infomax"
MAX_PCA_COMPONENTS = None
RANDOM_STATE = 23
fit_params = dict(extended=True)

# #################### EMG Control
EMG_FILTER_LOW_CUT = 1
EMG_FILTER_HIGH_CUT = 20

# Slide window desing
# Window len (time in sec)
WINDOW_LEN = 0.5
# slide window step (time in sec)
WINDOW_STEP = 0.05

# Threshold for EMG control
STD_TIMES = 3  # How many times the std to set the threshold

# %%
# ------------------ Fixed variables from the adquisition process ------------------

# Baseline
T_MIN_BASELINE = 0
T_MAX_BASELINE = 15

# Trial time
T_MIN = 1
T_MAX = 3.5

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
report = dict(Age=None, Gender="-", Recording_time=None, Ans_R=None, Ans_W=None)

# Montage
ADQUISITION_EQ = "biosemi128"
# Get montage
MONTAGE = mne.channels.make_standard_montage(ADQUISITION_EQ)

# Extern channels
Ref_channels = ["EXG1", "EXG2"]

# Gaze detection
Gaze_channels = ["EXG3", "EXG4"]

# Blinks detection
Blinks_channels = ["EXG5", "EXG6"]

# Mouth Moving detection
Mouth_channels = ["EXG7", "EXG8"]

# %%
# ------------------ Processing loop ------------------

for N_S in N_Subj_arr:
    # Get Age and Gender
    report["Age"], report["Gender"] = get_age_gender(N_S)

    for N_B in N_block_arr:
        print("Subject: " + str(N_S))
        print("Session: " + str(N_B))

        # Load data from BDF file
        rawdata, Num_s = extract_subject_from_bdf(data_dir, N_S, N_B)

        # Get raw events
        events = get_events_from_raw(rawdata, N_S, N_B)
        print("Checking Events")
        # Check and Correct baseline tags
        events = check_baseline_tags(events)

        # Check and Correct event
        events = event_correction(events=events)

        event_array = events.to_numpy()
        event_array = np.array(event_array, dtype=int)
        # replace the raw events with the new corrected events
        rawdata.event = event_array

        report["Recording_time"] = int(
            np.round(rawdata.last_samp / rawdata.info["sfreq"])
        )

        # Cognitive Control
        report["Ans_R"], report["Ans_W"] = cognitive_control_check(events)
        print("Check done")
        # %%
        # Referencing
        rawdata.set_eeg_reference(ref_channels=Ref_channels)
        if NOTCH_BOOL:
            # Notch filter
            rawdata = mne.io.Raw.notch_filter(rawdata, freqs=50)

        if FILTER_BOOL:
            # Filtering raw data
            rawdata.filter(LOW_CUT, HIGH_CUT)
        # %%
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
            decim=DS_RATE,
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
            decim=DS_RATE,
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
            decim=DS_RATE,
            baseline=None,
        )

        # ICA Prosessing

        if ICA_BOOL:
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
                decim=DS_RATE,
                baseline=None,
            )

            # Liberate Memory for ICA processing
            del rawdata

            # Creating the ICA object
            ica = mne.preprocessing.ICA(
                n_components=ICA_COMPONENTS,
                random_state=RANDOM_STATE,
                method=ICA_METHOD,
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
    low_f=EMG_FILTER_LOW_CUT,
    high_f=EMG_FILTER_HIGH_CUT,
    t_min=T_MIN,
    t_max=T_MAX,
    window_len=WINDOW_LEN,
    window_step=WINDOW_STEP,
    std_times=STD_TIMES,
    t_min_baseline=T_MIN_BASELINE,
    t_max_baseline=T_MAX_BASELINE,
)

# %%
