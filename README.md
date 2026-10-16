# Inner Speech Dataset

![GitHub](https://img.shields.io/badge/GitHub-InnerSpeech-blue?logo=github) 
![Datalad](https://img.shields.io/badge/Datalad-Dataset-orange?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAnFBMVEUAAAD///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////8AAAD////7+/v6+vrx8fHw8PDw7Ozs6Ojo5OTk4ODg3Nzc2NjY1NTU0NDQzMzMyMjIxMTEwMDAvLy8uLi4tLS0rKysqKioqKioqJiYmHh4eGhoaFhYVEREQAAAAAAABkZGRnZ2dnZ2dnZ2d0dHRycnJubm5sbGxqamptbW1paWlpYWFhXV1dTU1NTU0NDQzMzMyMjIxMTEwMDAvLy8uLi4tLS0rKysqKioqJiYmHh4eGhoaFhYVEREQAAAAAAABkZGRnZ2dnZ2dnZ2d0dHRycnJubm5sbGxqamptbW1paWlpYWFhXV1dTU1NTU0NDQzMzMyMjIxMTEwMDAvLy8uLi4tLS0rKysqKioqJiYmHh4eGhoaFhYVEREQAAAAv7MHSAAAAQHRSTlMAAQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTEyMzQ1Njc4OTo7PD0+P0BCQ0RFRkdISEpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CGiAAABdRJREFUGBltwQdOgjAUQNH4w2mCE7X7f//mJQMbSYrMMS6srm0O9NbHVYLyJRRA9/jPOb8zB5BDgCqAcAJ8B5IkgeKa6EniF2EXsH1tM7W8BjaqA0dAH4bJA8Swh3yFp+ZwqNxo1KPaK9wP9qzPtqJrG+y/KcF6TD/YhzPXew+g9+FZqlmrA/ggpg9qF+m2MG3h7V5vCPxG1D6aIbr5t+KmfXGvVWr+8O8LXhxK7H2fpvHGprWqkHNl2L+9Y+yI8/B1/qKQZV7GnkP+ns3TvdXh+mYjX1ncF0AAAAASUVORK5CYII=)  
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
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

Dependencies are declared in `pyproject.toml` (Python 3.11 or newer) and pinned in
`uv.lock`. Optional parts:

| Extra | Adds | Needed for |
| --- | --- | --- |
| `download` | `datalad`, `git-annex`, `tqdm` | `Raw_data_download_tutorial.py`, `Derivatives_download_tutorial.py` |
| `notebook` | `scikit-learn`, `ipykernel` | `Database_exploration_tutorial.ipynb` |

### With [uv](https://docs.astral.sh/uv/) (recommended)

```bash
uv sync --all-extras          # creates .venv with the exact versions in uv.lock
uv run python Python_Processing/InnerSpeech_preprocessing.py
```

`uv.lock` covers CPython on Linux (x86_64, aarch64), macOS and Windows (x64); on other
platforms use pip. Use `uv sync --extra download` (or `--extra notebook`) for only one extra, and
`uv sync -p 3.11` to use another Python version. `uv sync` also installs the
development tools (`ruff`); add `--no-dev` to skip them.

### With pip (any virtual environment, including conda)

```bash
python -m venv .venv && source .venv/bin/activate   # or: conda create -n inner_speech python=3.13 && conda activate inner_speech
pip install -e ".[download,notebook]"
```

Both install the shared code as the `innerspeech` package (from `src/innerspeech`,
in editable mode, so your changes are used immediately) together with its
dependencies. The scripts and tutorials import it, e.g.
`from innerspeech.data_extractions import extract_data_from_subject`.

> **Note:** `git-annex` is installed from PyPI (wheels for Linux with glibc >= 2.34,
> macOS and Windows). On older Linux systems install it with
> `conda install -c conda-forge git-annex` or your system package manager.

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

> **Note:** The published derivatives were made with the script's default settings, including ICA artifact removal as described in the paper (`ICA_BOOL = True`). ICA takes hours per session, which is why the derivatives are published. To make your own version, change the variables at the top of `InnerSpeech_preprocessing.py` (filters, decimation, ICA, EMG threshold, `N_JOBS` for the number of CPU cores) and set `save_dir` to a new folder so the published files are kept.

## Checking your copy

Two scripts in `checks/` compare a local copy of the dataset with the published version (run them from the repository folder):

```bash
python checks/verify_dataset.py                          # checksums, events rebuilt from raw, epochs files
python checks/reproduce_session.py --subject 8 --session 3 --no-ica   # re-run one session without ICA (minutes) and compare;
                                                                      # drop --no-ica for the full run (hours)
```

`verify_dataset.py` checks every file against the OpenNeuro checksums of the newest version listed in `checks/` (or `--manifest`) and reports which files to download again. Add `--skip-md5` for a quick size-only check. Results are saved in `results/checks/`.


## Exploration tutorial. 

**Notebook:** [`Database_exploration_tutorial.ipynb`](Database_exploration_tutorial.ipynb)  

- Can also run **directly in Google Colab** (no installation needed).  
- Includes examples for:  
  - Downloading raw or derivatives  
  - Preprocessing EEG data  
  - Visualizing EEG signals  
  - Basic machine learning analysis  

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/N-Nieto/Inner_Speech_Dataset/blob/main/Database_exploration_tutorial.ipynb)

---


## 4. Dataset main structure

``` lua
Project Folder
└─ ds003626 [Data is expected to be download here]
│   └─ sub-01/
│   │ ├─ ses-01/
│   │ │     └─ eeg/
│   │ │        ├─ sub-01_ses-01_task-innerspeech_eeg.bdf
│   │ │        ├─ sub-01_ses-01_task-innerspeech_eeg.json       [BIDS sidecars]
│   │ │        ├─ sub-01_ses-01_task-innerspeech_channels.tsv
│   │ │        └─ sub-01_ses-01_task-innerspeech_events.tsv
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
│    │       ├─ sub-01_ses-01_exg-epo.fif
│    │       ├─ sub-01_ses-01_events.tsv    [one row per trial]
│    │       ├─ sub-01_ses-01_report.json   [session information]
│    │       ├─ sub-01_ses-01_events.dat    [same trials, format up to 2.1.2]
│    │       └─ sub-01_ses-01_report.pkl    [same report, format up to 2.1.2]
│    └─ ses-02/...
│    └─ ses-03/...
```

`events.tsv` (from version 2.2.0) has the columns `sample`, `onset`, `class` (0 = up, 1 = down, 2 = right, 3 = left), `condition` (0 = pronounced, 1 = inner, 2 = visualized), `session`, `cue_inferred` (cue trigger missing and restored by the event correction) and the EMG control results `emg_power_exg7`, `emg_power_exg8` and `emg_tagged`; `derivatives/events.json` describes them. `report.json` holds age, gender, recording time, right and wrong answers to the control questions, the EMG control results and the list of event corrections. Read them with `innerspeech.derivatives_io` (`load_events_table`, `load_events`, `load_report`), which falls back to `events.dat` and `report.pkl` for older copies.

The top level also holds `dataset_description.json`, `participants.tsv`, `task-innerspeech_eeg.json` and `task-innerspeech_events.json` (event codes).

### Notes on the paper and the data files

- The epoch files are sampled at **256 Hz** (1024 Hz decimated by 4); the Methods section of the paper says 254 Hz.
- EEG and EXG trials have **1153 samples** (−0.5 to 4.0 s around the cue, both ends included); the paper says 1154.
- The protocol start event code is **11**; Table 3 of the paper says 1.
- The `sample` column of the events files counts samples of the **raw 1024 Hz** recording (first sample = 0), not of the 256 Hz epoch files. Divide by 1024 for seconds from the start of the recording; it equals `epochs.events[:, 0]` of the matching `.fif` files.
- Since the dataset version after 2.1.2, `baseline-epo.fif` holds the 136 EEG + EXG channels (earlier versions also included the Status trigger channel), and the age of sub-05 is 30, as in Table 1 (earlier `report.pkl` files said 31).

## 5. Repository main structure

``` lua
Project Folder
├─ ds003626                                      [Data]
├─ results                                       [Created by the analysis scripts]
│  ├─ psd/   tfr/                                [PSD and TFR results (.h5)]
│  ├─ figures/
│  └─ checks/                                    [Output of checks/]
└─ Inner_Speech_Dataset                          [This GitHub repository]
   ├─ Raw_data_download_tutorial.py
   ├─ Derivatives_download_tutorial.py
   ├─ Database_exploration_tutorial.ipynb
   ├─ src/innerspeech/                           [Shared code, installed as a package]
   ├─ Python_Processing/
   │  ├─ InnerSpeech_preprocessing.py            [Raw data -> derivatives]
   │  ├─ PSD_representation.py                   [PSD per condition/class -> results/psd]
   │  ├─ TFR_representations.py                  [Power/ITC -> results/tfr]
   │  └─ Plotting/                               [ERPs, PSD, ITC and TFR topomaps -> results/figures]
   ├─ checks/                                    [Compare a local copy with the published dataset]
   ├─ bids/                                      [BIDS sidecar files; events.tsv/report.json for published derivatives]
   ├─ tests/                                     [Automated tests on synthetic data]
   ├─ pyproject.toml                             [Dependencies and tool settings]
   ├─ uv.lock                                    [Pinned versions for uv]
   └─ README.md
```

Run `TFR_representations.py` before the ITC and TFR plotting scripts; they read its results.


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

