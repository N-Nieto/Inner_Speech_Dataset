# -*- coding: utf-8 -*-

"""
@author: Nicolás Nieto - nnieto@sinc.unl.edu.ar

Plot Inter Trial Coherence
"""
# In[] Imports modules

import matplotlib.pyplot as plt

from Utilitys         import Ensure_dir
from Data_extractions import Extract_TFR

# In[] Imports modules

root_spectrograms = "/media/nnieto/50e793fa-4717-4997-b590-b4167be63ee7/home/nnieto/Escritorio/Nico/Doctorado/Tesis/LIAA - sinc(i)/Toma de datos/Analisis/Espectrales/Dataset final/Spectograms/"
save_dir='/media/nnieto/50e793fa-4717-4997-b590-b4167be63ee7/home/nnieto/Escritorio/Nico/Doctorado/Tesis/LIAA - sinc(i)/Toma de datos/Analisis/Espectrales/Dataset final/ITC/'


TRF_method= "Morlet" # "Multitaper - "Morlet"
# Cue are present at t=0
TRF_type = "itc"

# Baseline
baseline_bool = False
baseline = [3,4]

# Comparation
Condition = "In"
Class = "All"

# In[] Load Data
# Load Class and condition
itc = Extract_TFR(TRF_dir = root_spectrograms, Cond = Condition, Class = Class, TFR_method = TRF_method, TRF_type = TRF_type)
  
if baseline_bool:
    itc.apply_baseline(baseline = baseline)
    
 # In[]: Plotting   
# Plot Options
combine = "mean"      # "mean" - "rms"
dB = False
vmin = 0
vmax = 0.30
fmin = 0.5
fmax = 100

# Saving 
save_bool= True
# Prefix for saving
prefix="ITC"

fontsize=20
plt.rcParams.update({'font.size': fontsize})
plt.rcParams.update({'legend.framealpha':0})
plot_cues_bool = True

fig = plt.figure(figsize=(20,10))
ax =  fig.add_axes([0.1,0.1,0.8,0.8])
if plot_cues_bool:
    plt.plot([0,0],[-15,150],axes=ax,color='black')
    plt.plot([0.5,0.5],[-15,150],axes=ax,color='black')
    plt.plot([3,3],[-15,150],axes=ax,color='black')
    
itc.plot(combine = combine, dB = dB, axes=ax, vmin=vmin , vmax=vmax, fmin = fmin, fmax = fmax)

title = "ITC - Condition: " + Condition + " in Class " + Class
ax.set_title(title, fontsize=fontsize)
ax.set_title(title, fontsize=fontsize)


if save_bool:
    Ensure_dir(save_dir)    
    fig.savefig(save_dir + prefix+'_'+Condition+'_'+Class+'.png', transparent = True )  





