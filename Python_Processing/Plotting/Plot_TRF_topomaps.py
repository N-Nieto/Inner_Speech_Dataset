# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 16:45:35 2021

@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Plot single TRF
"""


# In[] Imports modules

import matplotlib.pyplot as plt

from Utilitys import ensure_dir
from Data_extractions import extract_tfr

# In[] Imports modules

root_spectrograms = "../"
save_dir = '../'


TRF_method = "Morlet"       # "Multitaper - "Morlet"
# Cue are present at t=0
tmin = 0.5
tmax = 3
TRF_type = "power"
# Baseline options
baseline_bool = False
baseline = [3, 4]

# Plot Options
outlines = "skirt"      # "head" - "skirt"
sensors = True
sphere = None

# Saving
save_bool = False
# Prefix for saving
prefix = "TRF_Topomaps"

# Comparation 1
Condition = "All"
Class = "All"

# Bands
bands = [(0.5, 4, 'Delta (0.5-4 Hz)'),
         (4, 8, 'Theta (4-8 Hz)'),
         (8, 12, 'Alpha (8-12 Hz)'),
         (12, 30, 'Beta (12-30 Hz)'),
         (30, 45, 'Low Gamma (30-45Hz)'),
         (55, 100, 'High Gamma (55-100 Hz)')]

# Plot limit per band - [min_lim, max_lim]
vlim = [(0, 7.5e-9), (0, 9e-10), (0, 2e-9), (0, 5e-10), (0, 3e-10), (0, 3e-10)]

# In[] Load Data
# Load Class and condition
power = extract_tfr(TRF_dir=root_spectrograms, Cond=Condition, Class=Class,
                    TFR_method=TRF_method, TRF_type=TRF_type)

if baseline_bool:
    power.apply_baseline(baseline)

# Plotting

fontsize = 20
plt.rcParams.update({'font.size': fontsize})
plt.rcParams.update({'legend.framealpha': 0})


for band in range(len(bands)):
    bands_loop = bands[band]
    vlim_loop = vlim[band]
    fig = plt.figure(figsize=(20, 10))
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])

    power.plot_topomap(fmin=bands_loop[0], fmax=bands_loop[1], tmin=tmin,
                       tmax=tmax, title=bands_loop[2], show=False, axes=ax,
                       vmin=vlim_loop[0], vmax=vlim_loop[1], outlines=outlines,
                       sensors=sensors, sphere=sphere)

    if save_bool:
        ensure_dir(save_dir)

        if baseline_bool:
            fig.savefig(save_dir + prefix+'_'+Condition+'_'+Class+'_band'+str(band)+'_Baseline.png',            # noqa
                        transparent=True)

        else:
            fig.savefig(save_dir + prefix+'_'+Condition + '_'+Class + '_band'+str(band)+'_NO_Baseline.png',     # noqa
                        transparent=True)
