# Inner Speech Dataset

# Important! on 30 July 2021 several corrupted files were fixed in the data repository.

In the following repository all codes for reproduce and use the Inner speech Dataset are presented.

The dataset are publicy available at https://openneuro.org/datasets/ds003626

The publicatin are available at https://www.nature.com/articles/s41597-022-01147-2


## Stimulation Protocol

The stimulation protocol was used for capturing the data, and was developed in Matlab using Psychtoolbox.

The script `Stimulation_protocol.m` is the main script and uses the other auxiliary functions.

## Processing

The processing was developed in Python, using mainly the MNE library.

### Install the Inner speech processing environment

Create an environment with all the necessary libraries for running all the scripts.

`conda env create -f environment.yml`

Using the `Inner_speech_processing.py` script, you can easily make your own processing, changing the variables at the top of the script.

The `TFR_representation.py`  generates the Time Frequency Representations used addressing the same processing followed in the paper.

By means of the `Plot_TFR_Topomap.py` the same images presented in the paper can be addressed.



## Citing this work

Please cite this work: 

Nieto, N., Peterson, V., Rufiner, H.L. et al. Thinking out loud, an open-access EEG-based BCI dataset for inner speech recognition. Sci Data 9, 52 (2022). https://doi.org/10.1038/s41597-022-01147-2
