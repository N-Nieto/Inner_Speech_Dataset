"""
Datalad wrapper tutorial for downloading the Raw Inner Speech Dataset.

"""
# %%
from pathlib import Path

from Python_Processing.lib.download_helper import (
    clone_inner_speech,
    get_derivatives,
)

# The script InnerSpeech_preprocessing expects the data be saved in the parent folder of the project.
# Using this path to download the dataset
data_dir = Path().resolve().parent

# Clone just the structure (no files yet). This step is needed to create the
data_dir = clone_inner_speech(target_dir=data_dir, verbose=False)

# Option 1: Download all derivatives
# get_derivatives(
#     dataset_path=data_dir,
#     subjects=None,
#     sessions=None,
#     file_types="report",
#     verbose=True,
#     progress=True,
# )

# %
# Option 2: Download pre-processed EEG and events (ideal for ML analysis)
# get_derivatives(
#     dataset_path=data_dir,
#     subjects=None,
#     sessions=None,
#     file_types=["eeg", "events"],
#     verbose=True,
#     progress=True,
# )


# Option 3: Exploration for 1 subject and one session.
get_derivatives(
    dataset_path=data_dir,
    subjects="01",
    sessions="01",
    file_types=["eeg","events"],
    verbose=True,
    progress=False,
)
# %%
