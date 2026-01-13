# Inner Speech Dataset

![GitHub](https://img.shields.io/badge/GitHub-InnerSpeech-blue?logo=github) 
![Datalad](https://img.shields.io/badge/Datalad-Dataset-orange?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAnFBMVEUAAAD///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////8AAAD////7+/v6+vrx8fHw8PDw7Ozs6Ojo5OTk4ODg3Nzc2NjY1NTU0NDQzMzMyMjIxMTEwMDAvLy8uLi4tLS0rKysqKioqKioqJiYmHh4eGhoaFhYVEREQAAAAAAABkZGRnZ2dnZ2dnZ2d0dHRycnJubm5sbGxqamptbW1paWlpYWFhXV1dTU1NTU0NDQzMzMyMjIxMTEwMDAvLy8uLi4tLS0rKysqKioqJiYmHh4eGhoaFhYVEREQAAAAAAABkZGRnZ2dnZ2dnZ2d0dHRycnJubm5sbGxqamptbW1paWlpYWFhXV1dTU1NTU0NDQzMzMyMjIxMTEwMDAvLy8uLi4tLS0rKysqKioqJiYmHh4eGhoaFhYVEREQAAAAv7MHSAAAAQHRSTlMAAQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTEyMzQ1Njc4OTo7PD0+P0BCQ0RFRkdISEpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CGiAAABdRJREFUGBltwQdOgjAUQNH4w2mCE7X7f//mJQMbSYrMMS6srm0O9NbHVYLyJRRA9/jPOb8zB5BDgCqAcAJ8B5IkgeKa6EniF2EXsH1tM7W8BjaqA0dAH4bJA8Swh3yFp+ZwqNxo1KPaK9wP9qzPtqJrG+y/KcF6TD/YhzPXew+g9+FZqlmrA/ggpg9qF+m2MG3h7V5vCPxG1D6aIbr5t+KmfXGvVWr+8O8LXhxK7H2fpvHGprWqkHNl2L+9Y+yI8/B1/qKQZV7GnkP+ns3TvdXh+mYjX1ncF0AAAAASUVORK5CYII=)  
![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![MNE](https://img.shields.io/badge/MNE-python-blueviolet)
![Colab](https://img.shields.io/badge/Colab-Notebook-red?logo=googlecolab)

---

## Overview

The **Inner Speech Dataset** is an **EEG-based open-access dataset** for inner speech recognition.  
This repository provides scripts to **download, preprocess, explore, and analyze** the dataset.  

- Dataset: [OpenNeuro](https://openneuro.org/datasets/ds003626)  
- Publication: [Nieto et al., Scientific Data, 2022](https://www.nature.com/articles/s41597-022-01147-2)  

**New:** Helper scripts for easy downloading:  
- Raw EEG data: `Raw_data_download_tutorial.py`  
- Preprocessed derivatives: `Derivatives_download_tutorial.py`

> **Note:** A major refactor on **29/11/2025** improved `InnerSpeech_preprocessing.py`. Please report any issues if encountered.

---

# Get Started

## 1. Environment Setup

Create an environment with all dependencies:

```bash
conda env create -f environment.yml
conda activate inner_speech
```

## 2. Download the Data

### Raw Data
Using the provided `Raw_data_download_tutorial.py`, you can partially or fully download the raw `.bdf` data.

> **Note:**  Useful for re-running custom preprocessing

## 3. Data Processing

Preprocessing is implemented in Python using MNE. The main script `InnerSpeech_preprocessing.py` allows flexible adaptation for new processing.

> **Note:** Adjust preprocessing variables at the top of the script.

## Preprocessed Derivatives

If you prefer to use a already preprocessed data, you can partially or fully download `Derivatives_download_tutorial.py`. 

The script allows to flexible download only parts of the data, subjects or sessions.

> **Note:** This data was obtained after running the `InnerSpeech_preprocessing.py` with the current settings.


## Exploration tutorial. 

**Notebook:** [`Database_exploration_tutorial.ipynb`](notebooks/Database_exploration_tutorial.ipynb)  

- Can also run **directly in Google Colab** (no installation needed).  
- Includes examples for:  
  - Downloading raw or derivatives  
  - Preprocessing EEG data  
  - Visualizing EEG signals  
  - Basic machine learning analysis  

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/your-repo/InnerSpeech-Dataset/blob/main/notebooks/Database_exploration_tutorial.ipynb)

---


## 4. Dataset main structure

``` lua
Project Folder
└─ ds003626 [Data is expected to be download here]
│   └─ sub-01/
│   │ ├─ ses-01/
│   │ │     └─ eeg/
│   │ │        └─ sub-01_ses-01_task-innerspeech_eeg.bdf
│   │ ├─ ses-02/...
│   │ └─ ses-03/...
│   ├─ sub-02/
│    .....
│   └─ sub-10/
├─ derivatives/
│  └─ sub-01/
│    └─ ses-01/
│    │       ├─ sub-01_ses-01_baseline-epo.fif
│    │       ├─ sub-01_ses-01_eeg-epo.fif
│    │       ├─ sub-01_ses-01_events.dat
│    │       ├─ sub-01_ses-01_exg-epo.fif
│    │       └─ sub-01_ses-01_report.pkl
│    └─ ses-02/...
│    └─ ses-03/...
```

## 5. Repository main structure

``` lua
Project Folder
└─ ds003626                                      [Data]
├─ Inner_Speech_Dataset                          [This GitHub repository]
│  ├─ Raw_data_download_tutorial.py
│  ├─ Derivatives_download_tutorial.py
│  ├─ Database_exploration_tutorial.ipynb
│  └─  Python_Processing
│        └─  InnerSpeech_preprocessing.py
│        └─  lib                                 [Auxiliar functions]
├─ environment.yml
└─ README.md
```


## 6. If you are curious about the collection process or want to collect your own data: Stimulation Protocol

The stimulation protocol was used for capturing the data and was developed in Matlab using Psychtoolbox.

The script `Stimulation_protocol.m` is the main script and uses the other auxiliary functions.

## Citing this work

Please cite this work.
```bibtex
@article{nieto2022thinking,
  title={Thinking out loud, an open-access EEG-based BCI dataset for inner speech recognition},
  author={Nieto, Nicol{\'a}s and Peterson, Victoria and Rufiner, Hugo Leonardo and Kamienkowski, Juan Esteban and Spies, Ruben},
  journal={Scientific Data},
  volume={9},
  number={1},
  pages={1--17},
  year={2022},
  publisher={Nature Publishing Group}
}

```
```bibtex
@article{nieto2021inner,
  title={Inner Speech},
  author={Nieto, N and Peterson, V and Rufiner, HL and Kamienkowski, JE and Spies, R},
  journal={OpenNeuro},
  volume={29},
  pages={227--236},
  year={2021}
}
```

