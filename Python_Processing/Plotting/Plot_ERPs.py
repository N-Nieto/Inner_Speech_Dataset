"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Event Related Potentials - Plotting
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from innerspeech.data_extractions import extract_condition_epochs
from innerspeech.utils import find_project_root, picks_from_channels

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
Condition_list = ["Pron"]
Classes_list = ["All"]
channels = "all"

# Saving Parameters
save_bool = True
prefix = "ERPs"

# Fix all random states
random_state = 23
np.random.seed(random_state)

# Plotting
# Time window in s, relative to the cue onset
t_start = -0.5
t_end = 4
spatial_colors = True
plot_cues_bool = True
ylim = {"eeg": [-10, 15]}
fontsize = 20
plt.rcParams.update({"font.size": fontsize})
plt.rcParams.update({"legend.framealpha": 0})

# Get picks for the selected channels
picks = picks_from_channels(channels)

# %%
for Classes in Classes_list:
    for Cond in Condition_list:
        epochs = extract_condition_epochs(
            data_dir, N_S_list, datatype, condition=Cond, class_label=Classes
        )

        print(f"Plotting ERPs for Class: {Classes} in Condition: {Cond}")
        print(f"with the information of Subjects: {N_S_list} ({len(epochs)} trials)")

        evoked = epochs.average(picks=picks)

        fig = plt.figure(figsize=(20, 10))
        axs = fig.add_axes([0.1, 0.1, 0.8, 0.8])

        # Plot cue onset, cue offset and end of the action interval
        if plot_cues_bool:
            for t in (0, 0.5, 3):
                axs.axvline(t, color="black")

        # Plot ERPs
        evoked.plot(
            spatial_colors=spatial_colors,
            ylim=ylim,
            axes=axs,
            xlim=[t_start, t_end],
            show=False,
        )

        title = f"ERPs - Condition: {Cond} in Class {Classes}"
        axs.set_title(title, fontsize=fontsize)

        # Save Figure
        if save_bool:
            save_dir.mkdir(parents=True, exist_ok=True)
            fig.savefig(
                save_dir / f"{prefix}_{Cond}_{Classes}_{channels}_.png",
                transparent=True,
            )
