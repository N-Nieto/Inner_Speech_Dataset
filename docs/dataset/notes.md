# Notes and versions

## Differences from the paper

The data files are the reference. A few numbers in Nieto et al. (2022) differ from them:

| Paper | Data files |
| --- | --- |
| Sampling rate of the epochs 254 Hz (Methods) | **256 Hz** (1024 Hz decimated by 4) |
| 1154 samples per trial | **1153** samples: −0.5 to 4.0 s around the cue, both ends included |
| Protocol start code 1 (Table 3) | **11** |
| `baseline-epo.fif` holds 136 channels | Up to version 2.1.2 it also held the Status (trigger) channel; from 2.2.0 it holds the 136 EEG + EXG channels |
| sub-05 is 30 years old (Table 1) | Up to version 2.1.2 the `report.pkl` files of sub-05 said 31; from 2.2.0 they say 30 |

The `sample` column of the events files counts samples of the **raw 1024 Hz** recording
(first sample = 0), not of the 256 Hz epochs. Divide by 1024 for seconds from the start of
the recording.

## Per-session exceptions

sub-03, sessions 1 and 3
:   After session 1 the participant reported having performed the second inner speech
    run (trials 80–119) as visualized condition. The derivatives carry the corrected
    label, so session 1 has 40 inner speech and 120 visualized trials. To balance this,
    session 3 had three inner speech runs and one visualized run (60 and 20 trials). The
    raw `events.tsv` keeps the run type that was *announced* (code 22); the correction is
    `KNOWN_ISSUES[(3, 1)]` in `innerspeech.protocol`.

sub-10, session 1
:   A spurious trigger overlaps the end of the baseline. The events are read ignoring
    pulses shorter than 2 ms, which also drops the baseline-end code 14; the event
    correction re-inserts it 15 s after the baseline start.

sub-01, sub-03, sub-06 and sub-08, session 3
:   Shorter sessions (100 trials, 140 for sub-06), stopped because of tiredness. The
    five runs and the class balance are kept, with fewer trials per run.

sub-01 and sub-10, session 1
:   The participants reported pressing a key by accident at the first two attention
    questions.

sub-01, session 3
:   The `.bdf` file ends with an incomplete one-second data record. Recent MNE versions
    drop it, so the recording reads as 969 s instead of 970 s. The trials are not
    affected.

sub-03 session 3 and sub-08 session 2
:   The paper reports these baselines as highly contaminated. Keep this in mind if you
    normalise trials with the baseline; the EMG control of these sessions uses them too.

All sessions
:   The spurious code 65536 appears at the start of every recording and a few times
    within some sessions. It is not part of the protocol and is ignored by the code.

## Good practice

- **EMG-tagged trials** stay in the data. Leave them out for inner speech analyses
  where mouth movements would confound the result: `trials[~trials.emg_tagged]`.
- **Cross-session and cross-subject splits** matter: sessions differ in noise and
  electrode contact, so random trial splits within a session give optimistic decoding
  accuracies.
- **Pronounced speech** trials contain muscle artefacts by design; ICA removes the
  components correlated with the EMG channels, but some may remain.
- **Inferred cues** (`cue_inferred = True`) are a handful of trials whose class was
  restored from the class balance; drop them if you want only recorded labels.

## Version history

The dataset is versioned on OpenNeuro; `innerspeech.download_helper.list_versions()`
lists the published versions, and every download function takes `version="x.y.z"`.

| Version | Date | Changes |
| --- | --- | --- |
| 2.2.0 | upcoming | New `events.tsv` trial tables and `report.json` reports in `derivatives/` (with event corrections and inferred cues); BIDS sidecars for the raw recordings (`_eeg.json`, `_channels.tsv`, `_events.tsv`); `baseline-epo.fif` without the Status channel; sub-05 age 30 |
| 2.1.2 | 2022-03-14 | Final paper version |
| 2.1.1 | 2022-02-24 | Citation updated |
| 2.1.0 | 2021-11-25 | Corrected EEG files of sub-09 ses-01 and sub-10 ses-03 |
| 2.0.0 | 2021-07-30 | Several corrupted raw files fixed |
| 1.0.3 | 2021-06-02 | Events files corrected |
| 1.0.2 | 2021-04-20 | Preprint available |
| 1.0.1 | 2021-04-17 | README uploaded |
| 1.0.0 | 2021-04-17 | Initial upload |

!!! warning "Old copies"

    Some raw files of versions before 2.1.0 were corrupted or truncated. The download functions
    check the files you already have against the requested version and download them
    again if they differ, and `checks/verify_dataset.py` checks a whole copy, see
    [Check your copy](../start/checks.md).
