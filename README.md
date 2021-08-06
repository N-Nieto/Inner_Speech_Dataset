# Inner Speech Dataset

# Important! on 30 July 2021 several corrupted files were fixed in the data repository.

In the following repository all codes for reproduce and use the Inner speech Dataset are presented.

The dataset are publicy available at https://openneuro.org/datasets/ds003626

The preprint of the publicatin are available at https://www.biorxiv.org/content/10.1101/2021.04.19.440473v1


## Stimulation Protocol

The stimulation protocol was used for capturing the data, and was developed in Matlab using Psychtoolbox.

The script "Stimulation_protocol.m" is the main script and uses the other auxiliary functions.

## Processing

The processing was developed in Python, using mainly the MNE library.

### Install the Inner speech processing environment

For creating an environment with all the necessary libraries for running all the scripts executed.

conda env create -f inner_speech_environment.yml

Using the "Inner_speech_processing.py" script, you can easily make your own processing, changing the top variables.

The "TFR_representation.py '' generates the Time Frequency Representations used addressing the same processing followed in the paper.

By means of the "Plot_TFR_Topomap.py" the same images presented in the paper can be addressed.

