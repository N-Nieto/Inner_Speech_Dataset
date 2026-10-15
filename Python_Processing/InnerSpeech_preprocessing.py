# %%
"""
@author: Nicolás Nieto

We present a processing pipeline for the Inner Speech dataset that converts raw data
into a structured BIDS-compliant dataset stored in the "derivatives" folder.

Prerequisites:
Ensure you have downloaded the dataset from OpenNeuro.
A helper script (Raw_data_download_tutorial.py) is available to facilitate downloading
the raw data.
If you prefer not to reprocess the data, you can download the preprocessed derivatives
directly using another script (Derivatives_download_tutorial.py).

Preprocessing Steps:
    1. Event extraction and correction
    2. EEG re-referencing
    3. 50 Hz notch filter (Argentina power line frequency)
    4. Bandpass filtering (low-cut and high-cut)
    5. Epoching and decimation
    6. ICA artifact removal (computationally intensive, hours per session)
    7. Ad hoc correction for subjects who performed the tasks in another order
    8. EMG validation using single threshold
    9. Report generation and saving

All processing options are the variables at the top of the script; change them
and re-run to obtain your own derivatives (save them to another folder with
``save_dir`` to keep the published ones).
"""

# Imports modules
import gc
from pathlib import Path

import mne
import numpy as np

from innerspeech.adhoc_modification import (
    adhoc_subject_3,
)
from innerspeech.data_extractions import (
    extract_subject_from_bdf,
    get_age_gender,
    get_events_from_raw,
)
from innerspeech.derivatives_io import derivative_path, save_events, save_report
from innerspeech.emg_control import EMG_control_single_th
from innerspeech.events_analysis import (
    add_block_tag,
    add_condition_tag,
    check_baseline_tags,
    cognitive_control_check,
    delete_trigger_column,
    event_correction,
    standardize_labels,
)
from innerspeech.utils import find_project_root

# Folder that contains this repository and the dataset (ds003626). Resolved from
# this file's location, so it does not depend on the working directory.
try:
    _HERE = Path(__file__).resolve().parent
except NameError:  # run cell by cell or in Jupyter: no __file__
    _HERE = Path.cwd()
project_root = find_project_root(_HERE)
# %%
# Processing Variables

# Root where the raw data are stored (OpenNeuro name)
data_dir = project_root / "ds003626"

# Root where the structured data will be saved
# It can be changed and saved in other direction
save_dir = data_dir / "derivatives"

# Subjects and blocks. Subjects range from 1 to 10 (no subject 0).
# Blocks range from 1 to 3, (no block 0)
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
# If False, ICA is not applied
ICA_BOOL = True
ICA_COMPONENTS = None  # Use None to automatic selection
ICA_METHOD = "infomax"
MAX_PCA_COMPONENTS = None
RANDOM_STATE = 23
fit_params = {"extended": True}

# #################### Parallel processing
# CPU cores used for filtering (-1 = all cores, 1 = a single core).
# The results do not depend on this value.
N_JOBS = -1

# #################### EMG Control
EMG_FILTER_LOW_CUT = 1
EMG_FILTER_HIGH_CUT = 20

# Slide window design
# Window len (time in sec)
WINDOW_LEN = 0.5
# slide window step (time in sec)
WINDOW_STEP = 0.05

# Threshold for EMG control
STD_TIMES = 3  # How many times the std to set the threshold

# %%
# ------------------ Fixed variables from the acquisition process ------------------

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
event_id = {"Arriba": 31, "Abajo": 32, "Derecha": 33, "Izquierda": 34}

# Baseline id
baseline_id = {"Baseline": 13}

# Report initialization
report = {
    "Age": None,
    "Gender": "-",
    "Recording_time": None,
    "Ans_R": None,
    "Ans_W": None,
}

# Montage
ACQUISITION_EQ = "biosemi128"
# Get montage
MONTAGE = mne.channels.make_standard_montage(ACQUISITION_EQ)

# Extern channels
Ref_channels = ["EXG1", "EXG2"]

# Gaze detection
Gaze_channels = ["EXG3", "EXG4"]

# Blinks detection
Blinks_channels = ["EXG5", "EXG6"]

# Mouth Moving detection
Mouth_channels = ["EXG7", "EXG8"]

# All external channels
EXG_channels = Ref_channels + Gaze_channels + Blinks_channels + Mouth_channels

# %%
# ------------------ Processing loop ------------------

for N_S in N_Subj_arr:
    # Get Age and Gender
    report["Age"], report["Gender"] = get_age_gender(N_S)

    for N_B in N_block_arr:
        print("Subject: " + str(N_S))
        print("Session: " + str(N_B))

        # Load data from BDF file
        rawdata, _ = extract_subject_from_bdf(data_dir, N_S, N_B)

        # Get raw events
        events = get_events_from_raw(rawdata, N_S, N_B)
        print("Checking Events")
        # Check and Correct baseline tags
        events = check_baseline_tags(events)

        # Check and Correct event
        events = event_correction(events=events)

        event_array = events.to_numpy()
        event_array = np.array(event_array, dtype=int)

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
            rawdata.notch_filter(freqs=50, n_jobs=N_JOBS)

        if FILTER_BOOL:
            # Filtering raw data
            rawdata.filter(LOW_CUT, HIGH_CUT, n_jobs=N_JOBS)
        # %%
        # Save report (also creates the session folder)
        save_report(report, save_dir, N_S, N_B)

        # %%
        print("Epoching")
        # Every epoch set is cut from the continuous data here, so the
        # recording can be released before the (slow) ICA.

        # EXG: baseline-corrected with the 0.5 s before the cue. The correction
        # is applied at the original sampling rate, before decimating, so these
        # trials are cut separately from the EEG ones (8 channels, cheap).
        epochsEXG = mne.Epochs(
            rawdata,
            event_array,
            event_id=event_id,
            tmin=-0.5,
            tmax=4,
            picks=EXG_channels,
            preload=True,
            detrend=0,
            decim=DS_RATE,
        )

        # Baseline: the rest period between events 13 and 14, EEG + EXG channels
        # (releases up to 2.1.2 also kept the Status/trigger channel)
        t_baseline = (
            event_array[event_array[:, 2] == 14, 0]
            - event_array[event_array[:, 2] == 13, 0]
        ) / rawdata.info["sfreq"]
        t_baseline = t_baseline[0]
        Baseline = mne.Epochs(
            rawdata,
            event_array,
            event_id=baseline_id,
            tmin=0,
            tmax=round(t_baseline),
            picks=mne.pick_types(
                rawdata.info, eeg=True, stim=False, include=EXG_channels
            ),
            preload=True,
            detrend=0,
            decim=DS_RATE,
            baseline=None,
        )

        # EEG and EXG trials, cut and decimated once, without baseline
        # correction. The EEG derivative is taken from these trials; ICA also
        # uses the EXG channels to find the artifact components.
        epochsAll = mne.Epochs(
            rawdata,
            event_array,
            event_id=event_id,
            tmin=-0.5,
            tmax=4,
            picks=mne.pick_types(
                rawdata.info, eeg=True, stim=False, include=EXG_channels
            ),
            preload=True,
            detrend=0,
            decim=DS_RATE,
            baseline=None,
        )

        # The continuous recording is no longer needed: free its memory
        del rawdata
        gc.collect()

        # Save EXG and Baseline
        epochsEXG.save(
            derivative_path(save_dir, N_S, N_B, "exg-epo.fif"),
            fmt="double",
            split_size="2GB",
            overwrite=True,
        )
        Baseline.save(
            derivative_path(save_dir, N_S, N_B, "baseline-epo.fif"),
            fmt="double",
            split_size="2GB",
            overwrite=True,
        )
        del epochsEXG, Baseline
        print("EXG and Baseline saved")

        # EEG: the trials above without the EXG channels
        print("Processing EEG")
        epochsEEG = epochsAll.copy().drop_channels(EXG_channels)

        # ICA Processing
        if ICA_BOOL:
            # Creating the ICA object
            ica = mne.preprocessing.ICA(
                n_components=ICA_COMPONENTS,
                random_state=RANDOM_STATE,
                method=ICA_METHOD,
                fit_params=fit_params,
            )

            # Fit ICA, calculate components
            ica.fit(epochsEEG)

            # Components correlated with the gaze, blink and mouth channels
            ica.exclude = []
            for ch_name in Gaze_channels + Blinks_channels + Mouth_channels:
                exg_inds, _ = ica.find_bads_eog(epochsAll, ch_name=ch_name)
                ica.exclude.extend(exg_inds)

            print("Applying ICA")
            ica.apply(epochsEEG)
            del ica
        del epochsAll

        # Save EEG
        epochsEEG.save(
            derivative_path(save_dir, N_S, N_B, "eeg-epo.fif"),
            fmt="double",
            split_size="2GB",
            overwrite=True,
        )
        del epochsEEG
        gc.collect()

        # Standardize and save events
        events = add_condition_tag(events)
        events = add_block_tag(events, N_B=N_B)
        events = delete_trigger_column(events)
        events = standardize_labels(events)

        # Save events: (n_trials, 4) array [sample, class, condition, session]
        save_events(events, save_dir, N_S, N_B)

if 3 in N_Subj_arr and 1 in N_block_arr:
    #  Ad Hoc Modifications (sub-03, session 1)
    adhoc_subject_3(derivatives_dir=save_dir)

# EMG Control
EMG_control_single_th(
    derivatives_dir=save_dir,
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
    n_jobs=N_JOBS,
)

# %%
