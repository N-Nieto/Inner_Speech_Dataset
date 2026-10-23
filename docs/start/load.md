# Load and analyse

Once the derivatives are on disk (at least `file_types=["eeg", "events"]`), the package
gives you the trials in two forms: **NumPy arrays** for machine learning, or **MNE
Epochs** for the usual EEG analyses. In the examples, `root` is the `ds003626` folder.

```python
from pathlib import Path

root = Path("../ds003626")
```

## NumPy arrays

`extract_data_from_subject` stacks the three sessions of a subject:

```python
from innerspeech.data_extractions import extract_data_from_subject

X, Y = extract_data_from_subject(root, 1, "eeg")
X.shape  # (500, 128, 1153): trials × channels × samples, in volts
Y.shape  # (500, 4): sample, class, condition, session
```

`Y` has one row per trial with the columns of the trial table:

| Column | Values |
| --- | --- |
| `Y[:, 0]` | sample of the cue in the raw recording |
| `Y[:, 1]` | class: 0 up, 1 down, 2 right, 3 left |
| `Y[:, 2]` | condition: 0 pronounced, 1 inner, 2 visualized |
| `Y[:, 3]` | session: 1, 2, 3 |

For several subjects use `extract_data_multisubject(root, [1, 2, 3], "eeg")`. For a
single session, `extract_block_data_from_subject(root, n_s, "eeg", n_b)` returns the MNE
`Epochs` and the `Y` array of that session.

### Select trials and time

```python
from innerspeech.data_processing import (
    filter_by_class,
    filter_by_condition,
    select_time_window,
    transform_for_classifier,
)

# Only inner speech
X_in, Y_in = filter_by_condition(X, Y, "inner")

# Only the action interval: 1.0 to 3.5 s from the start of the trial
X_act = select_time_window(X_in, t_start=1.0, t_end=3.5, fs=256)

# Data and labels for a classifier: up vs down in inner speech
X_cls, y = transform_for_classifier(
    X_act, Y_in, classes=[["up"], ["down"]], conditions=[["inner"], ["inner"]]
)
```

Condition and class names accept short and Spanish aliases (`"in"`, `"interno"`,
`"arriba"`, …). `transform_for_classifier` can also pool pairs into one label, e.g.
`classes=[["up", "down"], ["right", "left"]]` for vertical vs horizontal.

!!! tip "Time in `select_time_window`"

    `t_start` and `t_end` count from the first sample of the epoch, i.e. from the start
    of the trial (concentration interval), not from the cue. See
    [The experiment](../dataset/experiment.md#a-trial).

### Leave out EMG-tagged trials

The trial table of each session has the EMG control result; its rows are in the same
order as the trials:

```python
import pandas as pd

from innerspeech.derivatives_io import load_events_table

table = pd.concat(
    [load_events_table(root / "derivatives", 1, ses) for ses in (1, 2, 3)],
    ignore_index=True,
)
keep = ~table["emg_tagged"].fillna(False).to_numpy(dtype=bool)
X_clean, Y_clean = X[keep], Y[keep]
```

## A first classifier

A small, honest baseline: log-variance features of the action interval, logistic
regression, and **sessions as folds**, so the model is always tested on a session it has
not seen. Expect accuracies not far above chance (25 % for four classes): inner speech
is hard to decode, which is what makes the dataset interesting.

```python
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

X_in, Y_in = filter_by_condition(X_clean, Y_clean, "inner")
X_act = select_time_window(X_in, 1.0, 3.5)

features = np.log(X_act.var(axis=2))  # trials × 128
labels, sessions = Y_in[:, 1], Y_in[:, 3]

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
scores = cross_val_score(
    model, features, labels, groups=sessions, cv=LeaveOneGroupOut()
)
print(scores.round(2), scores.mean().round(3))
```

The [tutorial notebook](https://colab.research.google.com/github/N-Nieto/Inner_Speech_Dataset/blob/main/Database_exploration_tutorial.ipynb)
walks through a similar example step by step, with plots.

## MNE Epochs

`extract_condition_epochs` reads only the trials you select, from any number of
subjects, into one `mne.EpochsArray` with the channel positions, the time axis and the
trial information as metadata:

```python
from innerspeech.data_extractions import extract_condition_epochs

epochs = extract_condition_epochs(root, subjects=[1, 2, 3], condition="inner")
epochs.metadata.head()  # subject, session, class, condition
epochs["up"].average().plot_joint()
epochs.compute_psd(fmax=40).plot()
```

Event names are `up`, `down`, `right` and `left`, and the metadata can be queried, e.g.
`epochs["session == 1 and subject == 2"]`.

Channel groups for `picks` (occipital, frontal, central, parietal regions of the BioSemi
layout) are in `innerspeech.utils.picks_from_channels`:

```python
from innerspeech.utils import picks_from_channels

epochs.copy().pick(picks_from_channels("OCC_Z"))
```

## Analysis scripts

`Python_Processing/` has the scripts behind the figures of the paper. They write to the
`results/` folder next to the repository.

| Script | Output |
| --- | --- |
| `PSD_representation.py` | Power spectral density per condition and class → `results/psd/` |
| `TFR_representations.py` | Time-frequency power and inter-trial coherence → `results/tfr/` |
| `Plotting/Plot_ERPs.py` | Event-related potentials |
| `Plotting/PSD_plot_PSD.py` | PSD figures (needs `PSD_representation.py`) |
| `Plotting/Plot_ITC.py`, `Plot_TFR_topomaps.py`, `Plot_TFR_differences.py` | ITC and TFR figures (need `TFR_representations.py`) |

Settings (subjects, condition, class, frequency bands, …) are variables at the top of
each script.
