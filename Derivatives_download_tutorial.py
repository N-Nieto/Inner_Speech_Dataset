"""
## Downloading the derivatives Inner Speech Dataset

This script provides a simple Python interface to download the
**Inner Speech EEG dataset** from OpenNeuro without requiring any knowledge of DataLad.

All DataLad operations happen **in the background**:
- The dataset is cached in a temporary directory
- Only the requested files are downloaded
- Files are copied as **regular files** (no symbolic links)
- The visible dataset directory contains **no Git or DataLad metadata**
- The **latest OpenNeuro version** is used unless `version="x.y.z"` is given
  (`list_versions()` shows the available ones)
- Files already on disk are checked against that version and re-downloaded
  if they differ (e.g. the truncated EEG files of version 2.0.0)

---

### 📁 Where the data will be stored

# This is the same directions where InnerSpeech_preprocessing.py will store the
# processed data.

parent_directory/
└── ds003626/
    └── derivatives
        └── sub-01/
            └── ses-01/
                └── sub-01_ses-01_baseline-epo.fif
                └── sub-01_ses-01_eeg-epo.fif
                └── sub-01_ses-01_events.dat
                └── sub-01_ses-01_exg-epo.fif
                └── sub-01_ses-01_report.pkl
"""

# %%
from pathlib import Path

from innerspeech.download_helper import (
    get_derivatives,
    list_versions,
)

print("Available OpenNeuro versions:", list_versions())

# The script InnerSpeech_preprocessing expects the data be saved in the parent folder
# of the project.
# Using this path to download the dataset
try:  # folder that contains this repository
    data_dir = Path(__file__).resolve().parent.parent
except NameError:  # run cell by cell or in Jupyter, from the repo root
    data_dir = Path.cwd().parent

# Option 1: Download all derivatives (This might take a while)
get_derivatives(
    dataset_path=data_dir,
    subjects="all",
    sessions="all",
    file_types="all",
    version=None,  # None = latest OpenNeuro version; or e.g. "2.1.2"
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
# %%
