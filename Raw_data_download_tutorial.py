# %%
from pathlib import Path

from Python_Processing.lib.download_helper import (
    clone_inner_speech,
    get_raw_eeg,
)

# The script InnerSpeech_preprocessing expects the data be saved in the parent folder of the project.
# Using this path to download the dataset
data_dir = Path().resolve().parent

# Clone just the structure (no files yet). This step is needed to create the
data_dir = clone_inner_speech(target_dir=str(data_dir), verbose=True)

# OPTION 1: download the whole raw dataset (This takes a while, as 30 big files need to be downloaded)
get_raw_eeg(
    dataset_path=data_dir,
    subjects=None,  # Used to download all subjects
    sessions=None,  # Used to download all sessions
    verbose=True, progress=False
)

# %%
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
