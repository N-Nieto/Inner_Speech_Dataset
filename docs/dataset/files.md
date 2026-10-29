# Files and formats

The dataset follows the [BIDS](https://bids.neuroimaging.io/) layout for EEG: raw
recordings per subject and session, metadata (sidecar) files that describe them, and a
`derivatives/` folder with the preprocessed trials. Click a file to see what it holds
and how to read it.

<div class="is-figure" markdown>
<p class="is-figure__title">The dataset folder</p>
<p class="is-figure__sub">One subject and session is shown expanded; all 30 follow the same pattern. File names start with the subject and session (<code>sub-01_ses-01_</code>, shortened to <code>…_</code> here).</p>
<div data-viz="file-explorer"><p>See the sections below for every file.</p></div>
</div>

!!! abstract "Which files do I need?"

    - **Decoding or analysing trials**: `derivatives/…/eeg-epo.fif` and
      `derivatives/…/events.tsv` (download `file_types=["eeg", "events"]`).
    - **Checking for eye or mouth movements**: add `exg-epo.fif` and `report.json`.
    - **Your own preprocessing** (other filters, no ICA, a longer window): the raw
      `.bdf` recordings.

## Top-level files

| File | Content |
| --- | --- |
| `dataset_description.json` | Name, authors, licence (CC0), DOI, how to cite |
| `participants.tsv` / `.json` | Age, gender and handedness of the ten participants |
| `task-innerspeech_eeg.json` | Recording settings shared by all sessions (system, sampling rate, channel counts, reference, power line 50 Hz) |
| `task-innerspeech_events.json` | Meaning of every trigger code and of the columns of the raw events files, see [Event codes](events.md) |
| `README`, `CHANGES` | Dataset description and version history |

??? example "participants.tsv"

    | participant_id | age | gender | handedness |
    | --- | ---: | --- | --- |
    | sub-01 | 56 | F | R |
    | sub-02 | 50 | M | R |
    | sub-03 | 34 | M | R |
    | sub-04 | 24 | F | R |
    | sub-05 | 30 | F | R |
    | sub-06 | 29 | M | R |
    | sub-07 | 26 | M | R |
    | sub-08 | 28 | F | R |
    | sub-09 | 35 | M | R |
    | sub-10 | 31 | M | R |

## Raw recordings

`sub-XX/ses-YY/eeg/` holds one recording per session:

`sub-XX_ses-YY_task-innerspeech_eeg.bdf`
:   The continuous BioSemi recording of the whole session (about 27 minutes and 700 MB
    for a full session): 128 EEG channels, 8 external channels and the Status channel,
    at 1024 Hz, as written by the acquisition software. Read it with
    `mne.io.read_raw_bdf` or `innerspeech.data_extractions.extract_subject_from_bdf`.

`sub-XX_ses-YY_task-innerspeech_events.tsv`
:   Every trigger in the Status channel, as recorded (not corrected): `onset` (s),
    `duration` (0), `sample` (at 1024 Hz, first sample = 0), `value` (the code),
    `trial_type` (its name) and `condition` (of the run).

`sub-XX_ses-YY_task-innerspeech_channels.tsv`
:   Name, type, units and description of every channel, see below.

`sub-XX_ses-YY_task-innerspeech_eeg.json`
:   Duration of this recording; everything else is in the top-level
    `task-innerspeech_eeg.json`.

### Channels

| Name | BIDS type | Description |
| --- | --- | --- |
| A1 … D32 | EEG | Scalp electrodes, BioSemi 128-channel radial layout (MNE montage `biosemi128`) |
| EXG1, EXG2 | REF | Left and right ear lobe; reference |
| EXG3, EXG4 | EOG | Left and right temple; horizontal eye movements |
| EXG5, EXG6 | EOG | Above and below the right eye; vertical eye movements and blinks |
| EXG7, EXG8 | EMG | Above and below the right side of the mouth; mouth movements |
| Status | TRIG | Trigger codes |

## Derivatives

`derivatives/sub-XX/ses-YY/` holds the output of
[`InnerSpeech_preprocessing.py`](../start/preprocessing.md) for every session. All
files of a session describe the same trials **in the same order**: row *i* of
`events.tsv` is epoch *i* of `eeg-epo.fif` and of `exg-epo.fif`.

### Epoch files

| File | Shape | Content |
| --- | --- | --- |
| `eeg-epo.fif` | trials × 128 × 1153 | EEG, fully preprocessed (with ICA) |
| `exg-epo.fif` | trials × 8 × 1153 | EXG1–EXG8, same filtering, no ICA, baseline-corrected with the 0.5 s before the cue |
| `baseline-epo.fif` | 1 × 136 × 3841 | The 15 s baseline, EEG + EXG |

All three are MNE `Epochs` saved in double precision, sampled at **256 Hz** (1024 Hz
decimated by 4). Trials run from −0.5 to 4.0 s around the cue, both ends included, so
they have 1153 samples (see [Notes](notes.md#differences-from-the-paper)). The event
code of each epoch is the cue code (31–34), and the epochs keep the sample of the cue in
the raw recording in `epochs.events[:, 0]`.

```python
import mne

epochs = mne.read_epochs("ds003626/derivatives/sub-01/ses-01/sub-01_ses-01_eeg-epo.fif")
X = epochs.get_data()  # (200, 128, 1153), volts
epochs.times[[0, -1]]  # array([-0.5,  4. ])
```

To read the trials of several sessions or subjects at once, with their labels, use the
[loaders of the package](../start/load.md).

### Trial table (`events.tsv`)

One row per trial, from version 2.2.0 of the dataset. `derivatives/events.json`
describes the columns.

| Column | Type | Meaning |
| --- | --- | --- |
| `sample` | int | Sample of the cue in the **raw 1024 Hz** recording (first sample = 0), not of the 256 Hz epochs; equals `epochs.events[:, 0]` |
| `onset` | float | Same in seconds from the start of the recording (`sample / 1024`) |
| `class` | int | 0 = up, 1 = down, 2 = right, 3 = left |
| `condition` | int | 0 = pronounced speech, 1 = inner speech, 2 = visualized condition |
| `session` | int | 1, 2 or 3 |
| `cue_inferred` | bool | True when the cue trigger was missing and restored by the [event correction](events.md#missing-triggers-and-how-they-are-restored); its class was inferred |
| `emg_power_exg7` | float (V²) | Mean power of EXG7 in the action interval (EMG control) |
| `emg_power_exg8` | float (V²) | Same for EXG8 |
| `emg_tagged` | bool | True when either power exceeds the baseline mean + 3 SD; pronounced speech trials are never tagged |

```text
sample  onset        class  condition  session  cue_inferred  emg_power_exg7  emg_power_exg8  emg_tagged
39869   38.9345703   3      0          1        False         3.83e-08        8.42e-09        False
46491   45.4013672   0      0          1        False         1.98e-08        1.73e-08        False
```

```python
from innerspeech.derivatives_io import load_events_table

trials = load_events_table("ds003626/derivatives", 1, 1)  # subject 1, session 1
clean_inner = trials[(trials.condition == 1) & ~trials.emg_tagged]
```

### Session report (`report.json`)

| Key | Meaning |
| --- | --- |
| `Age`, `Gender` | Of the participant |
| `Recording_time` | Length of the raw recording (s) |
| `Ans_R`, `Ans_W` | Right and wrong answers to the attention questions |
| `EMG_trials` | Indices (0-based, in trial order) of the EMG-tagged trials |
| `Power_EXG7`, `Power_EXG8` | Mean EMG power of those trials |
| `Baseline_EXG7_mean`, `…_std`, `Baseline_EXG8_mean`, `…_std` | Baseline power statistics; the threshold is mean + 3 × std |
| `Event_corrections` | Every event inserted, dropped or ignored by the event correction, with `sample`, `code`, `action` and `reason` |
| `Known_issue` | Only for sessions with a [known exception](notes.md#per-session-exceptions) |

```python
from innerspeech.derivatives_io import load_report

report = load_report("ds003626/derivatives", 2, 1)
report["Ans_R"], report["Ans_W"], len(report["EMG_trials"])  # (11, 0, 38)
```

### Legacy files

Versions up to 2.1.2 stored the trials and the report in two other formats, which are
still published next to the new files for code that reads them:

`events.dat`
:   NumPy array (`np.load(path, allow_pickle=True)`), shape trials × 4, with the columns
    `sample`, `class`, `condition`, `session`: the first four columns of `events.tsv`.

`report.pkl`
:   The report as a pickled `dict`, without `Event_corrections`. Pickles written with
    NumPy 1 raise a warning with NumPy 2; `innerspeech.derivatives_io.read_pickle`
    reads both.

The loaders in `innerspeech.derivatives_io` prefer the new files and fall back to the
legacy ones, so the same code works with every version of the dataset.
