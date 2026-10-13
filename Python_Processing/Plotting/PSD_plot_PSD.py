"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

PSD - Plotting

Plot the multitaper power spectral density of one channel for several
conditions (one line per condition, averaged over trials).
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from innerspeech.data_extractions import extract_condition_epochs
from innerspeech.utils import find_project_root

# Folder that contains this repository, the dataset and the results
try:
    _HERE = Path(__file__).resolve().parent
except NameError:  # run cell by cell or in Jupyter: no __file__
    _HERE = Path.cwd()
project_root = find_project_root(_HERE)

# %%
# Root where the data are stored
data_dir = project_root / "ds003626"
# Where the figures are written
save_dir = project_root / "results" / "figures"

# Subjects
N_S_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Data Parameters
datatype = "EEG"
Condition_list = ["Inner", "Vis"]
Classes_list = ["All"]
channel = "A26"
picks = [channel]

save_bool = True
prefix = "Power_Spectral_density_inner_vs_vis_beta"

# Fix all random states
random_state = 23
np.random.seed(random_state)

# Plotting
# Time window in s, relative to the cue onset
tmin = 1
tmax = 3

fmin = 11
fmax = 32

y_min = 19
y_max = 31
bandwidth = 1
fontsize = 23

plt.rcParams.update({"font.size": fontsize})
plt.rcParams.update({"legend.framealpha": 0})
# "midnightblue" - "darkred" - "darkcyan" - "darkgreen"
colors = ["darkred", "midnightblue"]

# %%
# Load data and plot
fig = plt.figure(figsize=[13, 10])
axs = plt.axes()
n_plot = 0
for Classes in Classes_list:
    for Cond in Condition_list:
        epochs = extract_condition_epochs(
            data_dir, N_S_list, datatype, condition=Cond, class_label=Classes
        )

        color = colors[n_plot % len(colors)]
        n_plot += 1

        epochs.compute_psd(
            method="multitaper",
            fmin=fmin,
            fmax=fmax,
            tmin=tmin,
            tmax=tmax,
            picks=picks,
            bandwidth=bandwidth,
        ).plot(
            average=True,
            dB=True,
            amplitude=False,
            color=color,
            picks=picks,
            axes=axs,
            show=False,
        )

# Legend: one entry per plotted mean line (MNE also draws black reference lines)
mean_lines = [line for line in axs.get_lines() if line.get_color() in colors]
axs.legend(
    mean_lines,
    ["Inner Speech", "Visualized"][:n_plot],
    loc="upper right",
    borderaxespad=0.9,
    fontsize=fontsize,
    shadow=False,
)
axs.set_title(" ", fontsize=fontsize)
axs.set_ylim(bottom=y_min, top=y_max)

title = "Power Spectral Density"
fig.suptitle(title)

# Save Figure
if save_bool:
    save_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_dir / f"{prefix}_{channel}_.png", transparent=True)
