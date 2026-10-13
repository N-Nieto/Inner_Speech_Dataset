"""
## Downloading the Raw Inner Speech Dataset

This script provides a simple Python interface to download the
**Inner Speech EEG dataset** from OpenNeuro without requiring any knowledge of DataLad.

All DataLad operations happen **in the background**:
- The dataset is cached in a temporary directory
- Only the requested files are downloaded
- Files are copied as **regular files** (no symbolic links)
- The visible dataset directory contains **no Git or DataLad metadata**
- The **latest OpenNeuro version** is used unless `version="x.y.z"` is given
- Files already on disk are checked against that version and re-downloaded
  if they differ

---

### 📁 Where the data will be stored

The preprocessing scripts expect the dataset to be located in the
**parent directory of the project**.
This is where the InnerSpeech_preprocessing.py expects to find the data.

parent_directory/
└── ds003626/
    └── sub-01/
        └── ses-01/
            └── eeg/
                └── sub-01_ses-01_task-innerspeech_eeg.bdf
"""

# %%
from pathlib import Path

from Python_Processing.lib.download_helper import (
    get_raw_eeg,
)

try:  # folder that contains this repository
    data_dir = Path(__file__).resolve().parent.parent
except NameError:  # run cell by cell or in Jupyter, from the repo root
    data_dir = Path.cwd().parent

# OPTION 1: Download the whole raw dataset
# (This takes a while, as 30 big files need to be downloaded)
get_raw_eeg(
    dataset_path=data_dir,
    subjects="all",  # Used to download all subjects
    sessions="all",  # Used to download all sessions
    version=None,  # None = latest OpenNeuro version; or e.g. "2.1.2"
    verbose=True,
    progress=True,
)

# OPTION 2: If you want, you could specify a subject
# get_raw_eeg(
#     dataset_path=data_dir,
#     subjects="01",  # For multi subjects, use a list of strings ["01", "02"]
#     sessions=None,  # Used to download all sessions
#     verbose=False, progress=True
# )

# OPTION 3: Alternatively, you can select a specific session
# get_raw_eeg(
#     dataset_path=data_dir,
#     subjects="01",  # For multi subjects, use a list of strings ["01", "02"]
#     sessions="01",  # For multi sessions, use a list of strings ["01", "02", "03"]
#     verbose=False, progress=True
# )

# %%
