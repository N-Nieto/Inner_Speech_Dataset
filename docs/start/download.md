# Download

The dataset is on [OpenNeuro (ds003626)](https://openneuro.org/datasets/ds003626). The
`innerspeech.download_helper` module downloads any part of it with one function call,
without you having to know DataLad: it keeps a hidden DataLad clone in a cache folder,
fetches only the files you ask for, and copies them as plain files into `ds003626/`.
Install the `download` extra first ([Install](install.md#optional-extras)).

## What to download

| Selection | `file_types` | Size (all subjects) |
| --- | --- | ---: |
| Preprocessed EEG trials | `"eeg"` | 6.7 GB |
| External channels (EOG, EMG) of the trials | `"exg"` | 0.4 GB |
| Baselines | `"baseline"` | 0.1 GB |
| Trial tables (`events.tsv`, `events.dat`) | `"events"` | < 1 MB |
| Reports (`report.json`, `report.pkl`) | `"report"` | < 1 MB |
| Raw recordings (`.bdf`) | use `get_raw_eeg` | 19.6 GB |

One full session of preprocessed EEG is about 236 MB; one raw recording about 700 MB.

## Preprocessed trials

```python
from pathlib import Path

from innerspeech.download_helper import get_derivatives

project = Path("..")  # folder that contains the repository; ds003626/ is created here

# Everything (about 7 GB)
get_derivatives(project, progress=True)

# EEG and trial tables of all subjects: all you need for decoding
get_derivatives(project, file_types=["eeg", "events"], progress=True)

# Two subjects, first session only
get_derivatives(project, subjects=[1, 2], sessions=1, file_types=["eeg", "events"])
```

The same is in the repository as `Derivatives_download_tutorial.py`.

## Raw recordings

```python
from innerspeech.download_helper import get_raw_eeg

get_raw_eeg(project, progress=True)  # all 30 recordings (≈ 20 GB)
get_raw_eeg(project, subjects="01", sessions=["01", "02"])
```

The same is in the repository as `Raw_data_download_tutorial.py`. Only the `.bdf` files
are copied. The code does not need the small BIDS sidecar files (`_events.tsv`,
`_channels.tsv`, `_eeg.json`) and top-level files; get them from OpenNeuro with one of
the [other ways](#other-ways) if you want them.

## Selecting subjects, sessions and versions

- `subjects` and `sessions` accept `"all"` (default), a single id (`1`, `"01"`) or a list.
- `version=None` (default) uses the newest version on OpenNeuro;
  `version="2.1.2"` downloads that version. `list_versions()` lists them.
- Files that are already on disk are checked against the requested version (by size,
  or by MD5 with `checksum=True`) and downloaded again if they differ, so re-running a
  download repairs an outdated or incomplete copy.
- Every function returns a dict with the `version` used and the lists of `downloaded`,
  `skipped` and `failed` files.

## Other ways

If you prefer not to use the package, any OpenNeuro download method works:

=== "Web"

    Download single files or the whole dataset from the
    [OpenNeuro page](https://openneuro.org/datasets/ds003626).

=== "DataLad"

    ```bash
    datalad install https://github.com/OpenNeuroDatasets/ds003626.git
    cd ds003626
    datalad get derivatives/sub-01      # fetch the files you need
    ```

=== "AWS CLI"

    ```bash
    aws s3 sync --no-sign-request s3://openneuro.org/ds003626 ds003626/ \
        --exclude "*" --include "derivatives/*"
    ```

Put the result in a `ds003626` folder next to the repository so that the scripts find it.
