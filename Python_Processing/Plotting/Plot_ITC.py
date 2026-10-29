"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Plot Inter Trial Coherence (ITC) computed by TFR_representations.py
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt

from innerspeech.data_extractions import extract_tfr
from innerspeech.utils import find_project_root

# Folder that contains this repository, the dataset and the results
try:
    _HERE = Path(__file__).resolve().parent
except NameError:  # run cell by cell or in Jupyter: no __file__
    _HERE = Path.cwd()
project_root = find_project_root(_HERE)

# %%
# TFR results written by TFR_representations.py
tfr_dir = project_root / "results" / "tfr"
# Where the figures are written
save_dir = project_root / "results" / "figures"

TFR_method = "Morlet"  # "Multitaper" - "Morlet"
# Cues are present at t=0
TFR_type = "itc"

# Baseline
baseline_bool = False
baseline = (3, 4)

# Comparison
Condition = "In"
Class = "All"

# Load Data
itc = extract_tfr(
    tfr_dir=tfr_dir,
    cond=Condition,
    class_label=Class,
    tfr_method=TFR_method,
    tfr_type=TFR_type,
)

if baseline_bool:
    itc.apply_baseline(baseline=baseline)

# Plotting
# Plot Options
combine = "mean"  # "mean" - "rms"
dB = False
vlim = (0, 0.30)
fmin = 0.5
fmax = 100

# Saving
save_bool = True
# Prefix for saving
prefix = "ITC"

fontsize = 20
plt.rcParams.update({"font.size": fontsize})
plt.rcParams.update({"legend.framealpha": 0})
plot_cues_bool = True

# %%
fig = plt.figure(figsize=(20, 10))
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])

itc.plot(combine=combine, dB=dB, axes=ax, vlim=vlim, fmin=fmin, fmax=fmax, show=False)

# Plot cue onset, cue offset and end of the action interval
if plot_cues_bool:
    for t in (0, 0.5, 3):
        ax.axvline(t, color="black")

title = f"ITC - Condition: {Condition} in Class {Class}"
ax.set_title(title, fontsize=fontsize)

if save_bool:
    save_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_dir / f"{prefix}_{Condition}_{Class}.png", transparent=True)
