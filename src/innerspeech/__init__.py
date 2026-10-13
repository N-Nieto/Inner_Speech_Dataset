"""
innerspeech: tools for the Inner Speech EEG dataset (OpenNeuro ds003626).

Modules
-------
- ``download_helper``   download raw data and derivatives from OpenNeuro
- ``events_analysis``   check and correct the recorded event sequences
- ``derivatives_io``    paths and file formats of the ``derivatives`` folder
- ``data_extractions``  load raw recordings and derivatives
- ``data_processing``   select conditions, classes and time windows
- ``emg_control``       tag trials contaminated by mouth movements (EMG)
- ``adhoc_modification`` dataset-specific label corrections
- ``utils``             small helpers (names, paths, channel groups)

Nieto et al. (2022), Scientific Data 9:52, https://doi.org/10.1038/s41597-022-01147-2
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("inner-speech-dataset")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "unknown"
