"""
@author: Nicolás Nieto - nnieto

Time-Frequency Representations (TFR) per condition and class.

For every condition/class pair, the trials of the selected subjects are pooled
and the average power (and inter-trial coherence, ITC) is computed with Morlet
wavelets or multitapers. Results are saved as
``<results>/tfr/<method>_<condition>_<class>_<power|itc>-tfr.h5`` and are read
by the plotting scripts with ``innerspeech.data_extractions.extract_tfr``.
"""

# %%
from pathlib import Path

import numpy as np

from innerspeech.data_extractions import extract_condition_epochs, tfr_path
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
# Where the TFR results are written (read by the plotting scripts)
save_dir = project_root / "results" / "tfr"

# Save options
save_bool = True
overwrite = True

# Subjects list
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

# Time Frequency Representation Parameters
TFR_method = "Morlet"  # Multitaper - Morlet
fmin = 0.5
fmax = 100
n_steps = 300
return_itc = True
use_fft = True  # same result as the direct convolution, about 4x faster
decim = 1
n_jobs = -1  # CPU cores (-1 = all); the result does not depend on it
picks = "all"

freqs = np.logspace(*np.log10([fmin, fmax]), num=n_steps)
n_cycles = freqs  # 1 s long wavelets at every frequency

# Only used in Morlet
zero_mean = True

if TFR_method not in ("Morlet", "Multitaper"):
    raise ValueError(f"TFR_method must be 'Morlet' or 'Multitaper', not {TFR_method!r}")

method_kw = {"n_cycles": n_cycles, "use_fft": use_fft}
if TFR_method == "Morlet":
    method_kw["zero_mean"] = zero_mean

# %%
# Main Loop
for Classes in Classes_list:
    for Cond in Conditions_list:
        # Trials of this condition and class for the selected subjects
        epochs = extract_condition_epochs(
            data_dir, N_S_list, datatype, condition=Cond, class_label=Classes
        )

        print(f"Calculating {TFR_method} for Class: {Classes} in Condition: {Cond}")
        print(f"with the information of Subjects: {N_S_list} ({len(epochs)} trials)")

        result = epochs.compute_tfr(
            method=TFR_method.lower(),
            freqs=freqs,
            picks=picks,
            average=True,
            return_itc=return_itc,
            decim=decim,
            n_jobs=n_jobs,
            **method_kw,
        )
        power, itc = result if return_itc else (result, None)

        if save_bool:
            save_dir.mkdir(parents=True, exist_ok=True)
            power.save(
                tfr_path(save_dir, Cond, Classes, TFR_method, "power"),
                overwrite=overwrite,
            )
            if itc is not None:
                itc.save(
                    tfr_path(save_dir, Cond, Classes, TFR_method, "itc"),
                    overwrite=overwrite,
                )
