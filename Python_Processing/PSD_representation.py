"""
@author: Nicolás Nieto - nnieto

Power Spectral Density (PSD) per condition and class.

For every condition/class pair, the trials of the selected subjects are pooled,
the Welch PSD is computed per trial and averaged, and the result is saved as
``<results>/psd/PSD_<condition>_<class>-psd.h5``. Read it back with
``mne.time_frequency.read_spectrum(innerspeech.data_extractions.psd_path(...))``.
"""

# %%
from pathlib import Path

import numpy as np

from innerspeech.data_extractions import extract_condition_epochs, psd_path
from innerspeech.utils import find_project_root

# Folder that contains this repository, the dataset and the results
try:
    _HERE = Path(__file__).resolve().parent
except NameError:  # run cell by cell or in Jupyter: no __file__
    _HERE = Path.cwd()
project_root = find_project_root(_HERE)

# %%
# Processing Variables

# Root where the data are stored (OpenNeuro name)
data_dir = project_root / "ds003626"
# Where the PSD results are written
save_dir = project_root / "results" / "psd"

# Save options
save_bool = False
overwrite = True

# Subjects list
N_S_list = [1]

# Data filtering
datatype = "EEG"
Conditions_list = ["Pron"]  # All - Pron - Inner - Vis
Classes_list = ["Left"]  # All - Up - Down - Right - Left

# Fix all random states
random_state = 23
np.random.seed(random_state)

# Time window in s, relative to the cue onset (trials span -0.5 to 4 s;
# 0.5-3 s is the action interval)
tmin = 0.5
tmax = 3

# PSD Parameters
fmin = 0.5
fmax = 100
n_overlap = 0
n_fft = 256
picks = "all"
average = "mean"

# %%
# Main Loop
spectra = {}
for Classes in Classes_list:
    for Cond in Conditions_list:
        # Trials of this condition and class for the selected subjects
        epochs = extract_condition_epochs(
            data_dir, N_S_list, datatype, condition=Cond, class_label=Classes
        )

        print(f"Calculating PSD for Class: {Classes} in Condition: {Cond}")
        print(f"with the information of Subjects: {N_S_list} ({len(epochs)} trials)")

        # Welch PSD per trial, averaged over trials
        spectrum = epochs.compute_psd(
            method="welch",
            fmin=fmin,
            fmax=fmax,
            tmin=tmin,
            tmax=tmax,
            picks=picks,
            n_fft=n_fft,
            n_overlap=n_overlap,
        ).average(method=average)
        spectra[Cond, Classes] = spectrum

        if save_bool:
            save_dir.mkdir(parents=True, exist_ok=True)
            spectrum.save(psd_path(save_dir, Cond, Classes), overwrite=overwrite)
