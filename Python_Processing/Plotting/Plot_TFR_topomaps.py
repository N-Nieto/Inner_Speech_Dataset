"""
Created on Mon Feb 15 16:45:35 2021

@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Plot single TFR (power topomaps per frequency band), using the TFRs computed by
TFR_representations.py.
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
# Time window in s, relative to the cue onset (cues are present at t=0)
tmin = 0.5
tmax = 3
TFR_type = "power"
# Baseline options
baseline_bool = False
baseline = (3, 4)

# Plot Options
outlines = "head"  # "head" or None ("skirt" was removed from MNE)
sensors = True
sphere = None

# Saving
save_bool = False
# Prefix for saving
prefix = "TFR_Topomaps"

# Comparison 1
Condition = "All"
Class = "All"

# Bands
bands = [
    (0.5, 4, "Delta (0.5-4 Hz)"),
    (4, 8, "Theta (4-8 Hz)"),
    (8, 12, "Alpha (8-12 Hz)"),
    (12, 30, "Beta (12-30 Hz)"),
    (30, 45, "Low Gamma (30-45Hz)"),
    (55, 100, "High Gamma (55-100 Hz)"),
]

# Plot limit per band - (min_lim, max_lim)
vlim = [(0, 7.5e-9), (0, 9e-10), (0, 2e-9), (0, 5e-10), (0, 3e-10), (0, 3e-10)]

# %%
# Load Data
power = extract_tfr(
    tfr_dir=tfr_dir,
    cond=Condition,
    class_label=Class,
    tfr_method=TFR_method,
    tfr_type=TFR_type,
)

if baseline_bool:
    power.apply_baseline(baseline)

# Plotting
fontsize = 20
plt.rcParams.update({"font.size": fontsize})
plt.rcParams.update({"legend.framealpha": 0})

# %%
baseline_tag = "Baseline" if baseline_bool else "NO_Baseline"
for band, ((f_low, f_high, band_name), band_vlim) in enumerate(
    zip(bands, vlim, strict=True)
):
    fig = plt.figure(figsize=(20, 10))
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])

    power.plot_topomap(
        fmin=f_low,
        fmax=f_high,
        tmin=tmin,
        tmax=tmax,
        show=False,
        axes=ax,
        vlim=band_vlim,
        outlines=outlines,
        sensors=sensors,
        sphere=sphere,
    )
    ax.set_title(band_name)

    if save_bool:
        save_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            save_dir / f"{prefix}_{Condition}_{Class}_band{band}_{baseline_tag}.png",
            transparent=True,
        )
