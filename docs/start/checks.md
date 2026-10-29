# Check your copy

Downloads can be interrupted, and older versions of the dataset had a few corrupted
recordings. The scripts in `checks/` compare a local copy with the published version and
tell you what to download again. Run them from the repository folder; results are saved
in `results/checks/`.

## Verify the files

```bash
python checks/verify_dataset.py                 # everything
python checks/verify_dataset.py --skip-md5      # sizes only, much faster
python checks/verify_dataset.py --subjects 1 2 --sessions 1
```

The script checks three things:

1. **Integrity**: the size and MD5 checksum of every file against the OpenNeuro
   checksums of the newest version in `checks/` (or `--manifest`). Files that differ or
   are missing are listed for download.
2. **Events**: the trials and the event-based report fields (recording time, answers)
   rebuilt from each raw `.bdf` with the current code, compared with the derivatives.
   Skip with `--skip-events`.
3. **Epochs**: every `*-epo.fif` is opened and its trial count, sampling rate, time
   window, channels and values checked. For the EEG files it also reports the numerical
   rank: 128 − *k* means *k* ICA components were removed. Skip with `--skip-epochs`.

The exit code is 1 if any check fails, so it can be used in scripts.

## Reproduce a session

```bash
python checks/reproduce_session.py --subject 8 --session 3 --no-ica   # minutes
python checks/reproduce_session.py --subject 8 --session 3            # hours, with ICA
```

This runs `InnerSpeech_preprocessing.py` unchanged (except the subject, session and
output folder) on one raw recording and compares every new file with the published one.
The published derivatives are never overwritten. Without ICA every file except
`eeg-epo.fif` should match.

## Noise per session

```bash
python checks/session_noise.py
```

Lists, per session, the median channel standard deviation of the EEG in the baseline and
in the trials and the RMS of the eye and mouth channels. A session whose baseline is much
noisier than its trials has a contaminated baseline.
