"""
Synthetic recordings and derivatives that follow the Inner Speech protocol.

A recording is an MNE ``RawArray`` shaped like a BioSemi BDF (EEG + EXG1-EXG8 +
Status at 1024 Hz) with the event sequence of the paper (Table 3): baseline,
then five runs (one pronounced, two inner speech, two visualized condition),
each trial tagged 42 / 31-34 / 44 / 45 / 46, and cognitive control questions in
the inner and visualized runs. Events can be removed or added to test the event
correction.
"""

from pathlib import Path

import mne
import numpy as np

SFREQ = 1024
EXG = [f"EXG{i}" for i in range(1, 9)]


def make_event_sequence(
    n_runs: int = 5,
    trials_per_run: int = 40,
    run_types: tuple = (21, 22, 22, 23, 23),
    drop: tuple = (),
    spurious: tuple = (),
    seed: int = 0,
) -> tuple[list[tuple[int, int]], int]:
    """(sample, code) events of one session and the number of samples."""
    rng = np.random.default_rng(seed)
    events = []
    t = 2 * SFREQ
    events.append((t, 11))
    t += 2 * SFREQ
    events += [(t, 13), (t + 15 * SFREQ, 14)]
    t += 17 * SFREQ
    for run in range(n_runs):
        events.append((t, 15))
        t += SFREQ
        events.append((t, run_types[run]))
        t += 3 * SFREQ
        tags = np.repeat([31, 32, 33, 34], trials_per_run // 4)
        rng.shuffle(tags)
        for k, tag in enumerate(tags):
            events += [
                (t, 42),
                (t + 512, int(tag)),
                (t + 1024, 44),
                (t + 3584, 45),
                (t + 4608, 46),
            ]
            t += 4608 + int(rng.integers(1536, 2048))
            if run_types[run] != 21 and k % 8 == 7:  # question every 8 trials
                events.append((t, 17))
                t += 2 * SFREQ
                events.append((t, int(tag) + 30))  # correct answer
                t += SFREQ
        events.append((t, 16))
        t += SFREQ
        if run < n_runs - 1:
            events.append((t, 51))
            t += 5 * SFREQ
    events.append((t, 12))
    t += 2 * SFREQ
    events += [(s, 65536) for s in spurious]
    events.sort()
    events = [e for i, e in enumerate(events) if i not in set(drop)]
    return events, t + 2 * SFREQ


def make_raw(
    n_eeg: int = 8, eeg_names: list[str] | None = None, seed: int = 1, **kw
) -> mne.io.RawArray:
    """Synthetic recording; ``kw`` goes to :func:`make_event_sequence`."""
    events, n_samples = make_event_sequence(seed=seed, **kw)
    eeg_names = eeg_names or [f"A{i}" for i in range(1, n_eeg + 1)]
    names = [*eeg_names, *EXG, "Status"]
    # read_raw_bdf types every non-Status channel as EEG, EXG included
    types = ["eeg"] * (len(names) - 1) + ["stim"]
    rng = np.random.default_rng(seed)
    data = rng.normal(0, 10e-6, (len(names), n_samples))
    data[:-1] += 20e-6 * np.sin(2 * np.pi * 50 * np.arange(n_samples) / SFREQ)
    stim = np.zeros(n_samples)
    stim[:5] = 65536  # the recordings start with a spurious 65536 trigger
    for sample, code in events:
        stim[sample : sample + 8] = code
    data[-1] = stim
    return mne.io.RawArray(data, mne.create_info(names, SFREQ, types), verbose="ERROR")


def write_bdf(raw: mne.io.BaseRaw, path: Path) -> Path:
    """Write ``raw`` as a BDF file whose Status channel keeps the exact codes.

    ``mne.export`` scales the Status channel like the data channels, so the
    trigger codes are written into the file afterwards.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    mne.export.export_raw(path, raw, fmt="bdf", overwrite=True, verbose="ERROR")
    stim = raw.get_data(picks="Status")[0].astype(np.int64)

    content = bytearray(path.read_bytes())
    n_ch = int(content[252:256].decode())
    n_records = int(content[236:244].decode())
    labels = [
        content[256 + 16 * i : 272 + 16 * i].decode().strip() for i in range(n_ch)
    ]
    offset = 256 + n_ch * 216
    per_record = [
        int(content[offset + 8 * i : offset + 8 * i + 8]) for i in range(n_ch)
    ]
    ch = labels.index("Status")
    record_bytes = sum(per_record) * 3
    start = 256 * (n_ch + 1) + sum(per_record[:ch]) * 3
    n = per_record[ch]

    values = np.zeros(n_records * n, np.int64)
    values[: len(stim)] = stim
    values &= 0xFFFFFF
    as_bytes = np.stack([values & 0xFF, (values >> 8) & 0xFF, values >> 16], axis=1)
    as_bytes = as_bytes.astype(np.uint8)
    for r in range(n_records):
        pos = start + r * record_bytes
        content[pos : pos + 3 * n] = as_bytes[r * n : (r + 1) * n].tobytes()
    # Physical range = digital range for Status, so codes read back unchanged
    for field, value in (
        (104, -8388608),
        (112, 8388607),
        (120, -8388608),
        (128, 8388607),
    ):
        pos = 256 + n_ch * field + 8 * ch
        content[pos : pos + 8] = f"{value:<8}".encode()
    path.write_bytes(bytes(content))
    return path


def write_derivatives(
    derivatives_dir: Path,
    subjects: tuple = (1, 2),
    sessions: tuple = (1, 2, 3),
    n_eeg: int = 4,
    seed: int = 0,
) -> None:
    """Small epoch, events and report files in the published layout."""
    from innerspeech.derivatives_io import derivative_path, save_events, save_report

    rng = np.random.default_rng(seed)
    times = np.arange(-0.5 * 256, 4 * 256 + 1) / 256  # 1153 samples
    event_id = {"Arriba": 31, "Abajo": 32, "Derecha": 33, "Izquierda": 34}
    for n_s in subjects:
        for n_b in sessions:
            n = 24
            classes = np.tile([0, 1, 2, 3], n // 4)
            conditions = np.repeat([0, 1, 2], n // 3)
            samples = 30_000 + 6000 * np.arange(n)
            events = np.column_stack([samples, classes, conditions, np.full(n, n_b)])
            save_events(events, derivatives_dir, n_s, n_b)
            mne_events = np.column_stack([samples, np.zeros(n, int), classes + 31])
            for kind, names in (
                ("eeg", [f"A{i}" for i in range(1, n_eeg + 1)]),
                ("exg", EXG),
            ):
                info = mne.create_info(names, 256, "eeg")
                data = rng.normal(0, 10e-6, (n, len(names), len(times)))
                epochs = mne.EpochsArray(
                    data,
                    info,
                    mne_events,
                    tmin=times[0],
                    event_id=event_id,
                    baseline=None,
                    verbose="ERROR",
                )
                epochs.save(
                    derivative_path(derivatives_dir, n_s, n_b, f"{kind}-epo.fif"),
                    overwrite=True,
                    verbose="ERROR",
                )
            baseline_names = [f"A{i}" for i in range(1, n_eeg + 1)] + EXG
            baseline = mne.EpochsArray(
                rng.normal(0, 10e-6, (1, len(baseline_names), 15 * 256 + 1)),
                mne.create_info(baseline_names, 256, "eeg"),
                np.array([[0, 0, 13]]),
                tmin=0,
                event_id={"Baseline": 13},
                baseline=None,
                verbose="ERROR",
            )
            baseline.save(
                derivative_path(derivatives_dir, n_s, n_b, "baseline-epo.fif"),
                overwrite=True,
                verbose="ERROR",
            )
            save_report({"Age": 30, "Gender": "F"}, derivatives_dir, n_s, n_b)
