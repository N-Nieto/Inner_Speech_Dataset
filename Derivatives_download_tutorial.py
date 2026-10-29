"""
## Downloading the derivatives Inner Speech Dataset

This scripts provides a simple Python interface to download the **Inner Speech EEG dataset**
from OpenNeuro without requiring any knowledge of DataLad.

All DataLad operations happen **in the background**:
- The dataset is cached in a temporary directory
- Only the requested files are downloaded
- Files are copied as **regular files** (no symbolic links)
- The visible dataset directory contains **no Git or DataLad metadata**

---

### 📁 Where the data will be stored

# This is the same directions where InnerSpeech_preprocessing.py will store the processed data.

parent_directory/
└── ds003626/
    └── derivatives
        └── sub-01/
            └── ses-01/
                └── sub-01_ses-01_baseline-epo.bdf
                └── sub-01_ses-01_eeg-epo.bdf
                └── sub-01_ses-01_events.dat
                └── sub-01_ses-01_exg-epo.bdf
                └── sub-01_ses-01_report.pkl 
"""

# %%
from pathlib import Path

from Python_Processing.lib.download_helper import (
    get_derivatives,
    get_raw_eeg,
)

# The script InnerSpeech_preprocessing expects the data be saved in the parent folder of the project.
# Using this path to download the dataset
data_dir = Path().resolve().parent

# Option 1: Download all derivatives (This might take a while)
get_derivatives(
    dataset_path=data_dir,
    subjects="all",
    sessions="all",
    file_types="all",
    verbose=True,
    progress=True,
)

# Option 2: Download pre-processed EEG and events (ideal for ML analysis)
# get_derivatives(
#     dataset_path=data_dir,
#     subjects="all",
#     sessions="all",
#     file_types=["eeg", "events"],
#     verbose=True,
#     progress=True,
# )


# # Option 3: Fast test. If you want to test the function
# get_derivatives(
#     dataset_path=data_dir,
#     subjects="01",
#     sessions="01",
#     file_types="report",
#     verbose=True,
#     progress=False,
# )

# Option 3: Download 1 subject of raw eeg data.
get_raw_eeg(
    dataset_path=data_dir,
    subjects="01",
    sessions="01",
    verbose=True,
    progress=True,
)

# Option 4: Exploration for 1 subject and one session.
get_derivatives(
    dataset_path=data_dir,
    subjects="01",
    sessions="01",
    file_types=["eeg","events"],
    verbose=True,
    progress=False,
)


# %%
