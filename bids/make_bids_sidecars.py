"""
Write the BIDS sidecar files of the Inner Speech dataset (OpenNeuro ds003626).

The raw ``.bdf`` files and the ``derivatives`` folder are not modified. The
script reads each ``.bdf`` header and its Status (trigger) channel and writes:

Top level (inherited by every recording):
    dataset_description.json        updated BIDSVersion and HowToAcknowledge
    participants.tsv / .json        age, self-declared gender, handedness (Table 1)
    task-innerspeech_eeg.json       acquisition metadata shared by all recordings
    task-innerspeech_events.json    meaning of the events.tsv columns and codes

Per recording (sub-XX/ses-YY/eeg/):
    *_eeg.json                      recording duration and hardware filter
    *_channels.tsv                  name, type and units of the 137 channels
    *_events.tsv                    every trigger of the Status channel, as recorded

derivatives/dataset_description.json   describes the preprocessed files
derivatives/events.json                 meaning of the derivatives' events.tsv columns

Usage (from the repository folder, in the project environment):

    python bids/make_bids_sidecars.py                  # writes into <project>/ds003626
    python bids/make_bids_sidecars.py --data-dir /path/to/ds003626 --overwrite

Existing files are kept unless ``--overwrite`` is given. Check the result with
the BIDS validator (``pip install bids-validator-deno``)::

    bids - validator - deno / path / to / ds003626
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import mne

from innerspeech.derivatives_io import TRIAL_COLUMNS_JSON
from innerspeech.utils import find_project_root

HERE = Path(__file__).resolve().parent
TASK = "innerspeech"
BIDS_VERSION = "1.10.1"
CODE_URL = "https://github.com/N-Nieto/Inner_Speech_Dataset"
PAPER = (
    "Nieto, N., Peterson, V., Rufiner, H. L., Kamienkowski, J. E., & Spies, R. "
    "(2022). Thinking out loud, an open-access EEG-based BCI dataset for inner "
    "speech recognition. Scientific Data, 9, 52. "
    "https://doi.org/10.1038/s41597-022-01147-2"
)

# ----------------------------------------------------------------------------
# Participants (Table 1 of the paper)
# ----------------------------------------------------------------------------
PARTICIPANTS = [
    # participant_id, age, gender, handedness
    ("sub-01", 56, "F", "R"),
    ("sub-02", 50, "M", "R"),
    ("sub-03", 34, "M", "R"),
    ("sub-04", 24, "F", "R"),
    ("sub-05", 30, "F", "R"),
    ("sub-06", 29, "M", "R"),
    ("sub-07", 26, "M", "R"),
    ("sub-08", 28, "F", "R"),
    ("sub-09", 35, "M", "R"),
    ("sub-10", 31, "M", "R"),
]

PARTICIPANTS_JSON = {
    "participant_id": {"Description": "Participant identifier"},
    "age": {"Description": "Age at the time of the recording", "Units": "year"},
    "gender": {
        "Description": "Self-declared gender",
        "Levels": {"F": "female", "M": "male"},
    },
    "handedness": {"Description": "Dominant hand", "Levels": {"R": "right"}},
}

# ----------------------------------------------------------------------------
# Channels
# ----------------------------------------------------------------------------
EXTERNAL_CHANNELS = {
    # name: (BIDS type, description)
    "EXG1": ("REF", "Left ear lobe; reference (no neural activity)"),
    "EXG2": ("REF", "Right ear lobe; reference (no neural activity)"),
    "EXG3": ("EOG", "Left temple; horizontal eye movements"),
    "EXG4": ("EOG", "Right temple; horizontal eye movements"),
    "EXG5": ("EOG", "Above the right eye; vertical eye movements and blinks"),
    "EXG6": ("EOG", "Below the right eye; vertical eye movements and blinks"),
    "EXG7": ("EMG", "Superior right orbicularis oris; mouth movements"),
    "EXG8": ("EMG", "Inferior right orbicularis oris; mouth movements"),
}
TRIGGER_CHANNEL = "Status"

# ----------------------------------------------------------------------------
# Events (Table 3 of the paper; the protocol start is 11, not 1)
# ----------------------------------------------------------------------------
EVENT_CODES = {
    11: ("protocol_start", "Start of protocol"),
    12: ("protocol_end", "End of protocol"),
    13: ("baseline_start", "Start of baseline (15 s rest)"),
    14: ("baseline_end", "End of baseline"),
    15: ("run_start", "Start of run"),
    16: ("run_end", "End of run"),
    17: ("question", "Cognitive control: question posing"),
    21: ("run_pronounced", "Start of pronounced speech run"),
    22: ("run_inner", "Start of inner speech run"),
    23: ("run_visualized", "Start of visualized condition run"),
    31: ("cue_up", "'Arriba' (up) trial: start of the cue interval"),
    32: ("cue_down", "'Abajo' (down) trial: start of the cue interval"),
    33: ("cue_right", "'Derecha' (right) trial: start of the cue interval"),
    34: ("cue_left", "'Izquierda' (left) trial: start of the cue interval"),
    42: ("concentration", "Start of the concentration interval"),
    44: ("action", "Start of the action interval"),
    45: ("relax", "Start of the relax interval"),
    46: ("rest", "Start of the rest interval"),
    51: ("inter_run_rest", "Start of the rest between runs"),
    61: ("answer_up", "Answer to the cognitive control: 'Arriba' (up)"),
    62: ("answer_down", "Answer to the cognitive control: 'Abajo' (down)"),
    63: ("answer_right", "Answer to the cognitive control: 'Derecha' (right)"),
    64: ("answer_left", "Answer to the cognitive control: 'Izquierda' (left)"),
    65536: (
        "spurious",
        "Spurious trigger of unknown origin (start of the recording and a few "
        "within sessions); not related to the protocol",
    ),
}
RUN_CONDITIONS = {21: "pronounced", 22: "inner", 23: "visualized"}
RUN_END = 16

EVENTS_JSON = {
    "StimulusPresentation": {
        "SoftwareName": "Psychtoolbox-3 (MATLAB)",
        "SoftwareRRID": "RRID:SCR_002881",
        "Code": CODE_URL + "/tree/main/Stimulation%20Protocol%20-%20MatLab",
    },
    "onset": {
        "Description": "Time of the trigger from the start of the recording",
        "Units": "s",
    },
    "duration": {"Description": "Triggers are instantaneous", "Units": "s"},
    "sample": {
        "Description": "Sample number of the trigger in the recording (1024 Hz, "
        "first sample = 0). Same numbering as the 'sample' column of the "
        "derivatives' events.tsv and events.dat files."
    },
    "value": {
        "Description": "Trigger code as recorded in the Status channel",
        "Levels": {str(code): text for code, (_, text) in EVENT_CODES.items()},
    },
    "trial_type": {
        "Description": "Name of the trigger code",
        "Levels": dict(EVENT_CODES.values()),
    },
    "condition": {
        "Description": "Condition of the run the trigger belongs to, from the "
        "run start code (21, 22, 23); n/a outside runs. In sub-03 ses-01 the "
        "second inner speech run (trials 80-119) was performed as visualized "
        "condition; the derivatives' events files carry the corrected label.",
        "Levels": {
            "pronounced": "Pronounced speech",
            "inner": "Inner speech",
            "visualized": "Visualized condition",
        },
    },
}

# ----------------------------------------------------------------------------
# EEG sidecar (shared by all recordings)
# ----------------------------------------------------------------------------
EEG_JSON = {
    "TaskName": TASK,
    "TaskDescription": (
        "Ten participants performed four mental tasks (the Spanish words "
        "'arriba', 'abajo', 'derecha', 'izquierda': up, down, right, left) in "
        "three conditions: pronounced speech, inner speech and visualized "
        "condition. Each session has a 15 s baseline and five runs (one "
        "pronounced speech, two inner speech, two visualized condition)."
    ),
    "Instructions": (
        "Inner speech: imagine your own voice repeating the word shown by the "
        "cue. Pronounced speech: repeat the word aloud. Visualized condition: "
        "mentally move the central circle in the direction of the cue. Start "
        "when the cue disappears and stop when the circle turns blue."
    ),
    "InstitutionName": (
        "Instituto de Investigación en Señales, Sistemas e Inteligencia "
        "Computacional, sinc(i), FICH-UNL/CONICET"
    ),
    "InstitutionalDepartmentName": "sinc(i)",
    "InstitutionAddress": "Santa Fe, Argentina",
    "Manufacturer": "BioSemi",
    "ManufacturersModelName": "ActiveTwo",
    "CapManufacturer": "BioSemi",
    "CapManufacturersModelName": "128-channel head cap (A1-D32 layout)",
    "EEGPlacementScheme": "BioSemi 128-channel radial layout (A1-D32)",
    "EEGReference": (
        "CMS/DRL of the BioSemi active electrode system. The derivatives are "
        "re-referenced to the mean of EXG1 and EXG2 (ear lobes)."
    ),
    "EEGGround": "DRL",
    "SamplingFrequency": 1024,
    "PowerLineFrequency": 50,
    "SoftwareFilters": "n/a",
    "EEGChannelCount": 128,
    "EOGChannelCount": 4,
    "EMGChannelCount": 2,
    "ECGChannelCount": 0,
    "MISCChannelCount": 0,
    "TriggerChannelCount": 1,
    "RecordingType": "continuous",
}

# Hardware low-pass reported in the paper; used when the BDF header has none
PAPER_HARDWARE_FILTER = {
    "Digital low-pass (ActiView, from the paper)": {"HighCutoff": 208}
}

# Per-recording notes (SubjectArtefactDescription), from inspection of the data
ARTEFACT_NOTES = {
    ("sub-08", "ses-02"): (
        "The 15 s baseline at the start of the session is strongly contaminated "
        "(EEG and EXG amplitudes about 3 times the median of all sessions); the "
        "trials of the session are not."
    ),
    ("sub-08", "ses-03"): (
        "The 15 s baseline at the start of the session is strongly contaminated "
        "(EEG amplitude about 3 times and EXG7/EXG8 about 10 times the median of "
        "all sessions); the trials of the session are not."
    ),
}

DERIVATIVES_DESCRIPTION = {
    "Name": "Inner Speech dataset: preprocessed epochs",
    "BIDSVersion": BIDS_VERSION,
    "DatasetType": "derivative",
    "GeneratedBy": [
        {
            "Name": "InnerSpeech_preprocessing.py",
            "Description": (
                "Event check and correction; re-reference to the mean of EXG1 "
                "and EXG2; 50 Hz notch; 0.5-100 Hz band-pass; epochs from 0.5 s "
                "before to 4 s after the cue, decimated to 256 Hz; ICA (extended "
                "infomax) on the EEG, removing components correlated with "
                "EXG3-EXG8; EMG control of inner speech and visualized trials. "
                "Files per session: eeg-epo.fif, exg-epo.fif, baseline-epo.fif, "
                "events.tsv (one row per trial, columns described in events.json) "
                "and report.json; events.dat and report.pkl hold the same trials "
                "and report in the format of releases up to 2.1.2."
            ),
            "CodeURL": CODE_URL,
        }
    ],
    "SourceDatasets": [{"URL": "https://openneuro.org/datasets/ds003626"}],
    "HowToAcknowledge": f"Please cite: {PAPER}",
}

# Used only when the dataset folder has no dataset_description.json
DATASET_DESCRIPTION = {
    "Name": "Inner Speech",
    "BIDSVersion": BIDS_VERSION,
    "DatasetType": "raw",
    "License": "CC0",
    "Authors": [
        "Nicolas Nieto",
        "Victoria Peterson",
        "Hugo Rufiner",
        "Juan Kamienkowski",
        "Ruben Spies",
    ],
    "HowToAcknowledge": f"Please cite: {PAPER}",
    "ReferencesAndLinks": [
        "https://www.nature.com/articles/s41597-022-01147-2",
        CODE_URL,
    ],
    "EthicsApprovals": [
        "Comite Asesor de Etica y Seguridad en el Trabajo Experimental (CEySTE), "
        "CCT-CONICET, Santa Fe, Argentina"
    ],
}


# ----------------------------------------------------------------------------
# Writers
# ----------------------------------------------------------------------------
def write_json(path: Path, content: dict, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=4, ensure_ascii=False) + "\n", "utf-8")
    return True


def write_tsv(path: Path, header: list[str], rows: list, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return True


def fmt(value: float) -> str:
    """Number for a TSV cell, without trailing zeros."""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def dataset_description(data_dir: Path) -> dict:
    path = data_dir / "dataset_description.json"
    content = json.loads(path.read_text("utf-8")) if path.exists() else {}
    if not content:
        content = dict(DATASET_DESCRIPTION)
    content["BIDSVersion"] = BIDS_VERSION
    # Complete the ethics statement, cut short in releases up to 2.1.2
    content["EthicsApprovals"] = [
        e + " Argentina" if e.rstrip().endswith("Santa Fe,") else e
        for e in content.get("EthicsApprovals", [])
    ]
    content.setdefault(
        "GeneratedBy",
        [
            {
                "Name": "BioSemi ActiView",
                "Description": "Acquisition. BIDS sidecar files written with "
                "bids/make_bids_sidecars.py of the code repository.",
                "CodeURL": CODE_URL,
            }
        ],
    )
    if not content.get("HowToAcknowledge"):
        content["HowToAcknowledge"] = f"Please cite: {PAPER}"
    return content


def channel_rows(raw: mne.io.BaseRaw) -> list:
    low = raw.info["highpass"]
    high = raw.info["lowpass"]
    low_cut = fmt(low) if low and low > 0 else "n/a"
    high_cut = fmt(high) if high and high < raw.info["sfreq"] / 2 else "n/a"
    units = getattr(raw, "_orig_units", {}) or {}
    rows = []
    for name in raw.ch_names:
        if name == TRIGGER_CHANNEL:
            rows.append([name, "TRIG", "n/a", "n/a", "n/a", "Trigger codes", "good"])
            continue
        ch_type, description = EXTERNAL_CHANNELS.get(name, ("EEG", "Scalp electrode"))
        unit = units.get(name, "uV").replace("uV", "µV")
        rows.append([name, ch_type, unit, low_cut, high_cut, description, "good"])
    return rows


def event_rows(raw: mne.io.BaseRaw) -> list:
    events = mne.find_events(
        raw,
        stim_channel=TRIGGER_CHANNEL,
        initial_event=True,
        consecutive=True,
        verbose="ERROR",
    )
    sfreq = raw.info["sfreq"]
    rows, condition = [], "n/a"
    for sample, _, value in events:
        value = int(value)
        if value in RUN_CONDITIONS:
            condition = RUN_CONDITIONS[value]
        trial_type = EVENT_CODES.get(value, ("unknown", ""))[0]
        rows.append(
            [
                fmt((sample - raw.first_samp) / sfreq),
                "0",
                int(sample - raw.first_samp),
                value,
                trial_type,
                condition,
            ]
        )
        if value == RUN_END:
            condition = "n/a"
    return rows


def recording_json(raw: mne.io.BaseRaw, sub: str, ses: str) -> dict:
    content = {
        "SamplingFrequency": raw.info["sfreq"],
        "RecordingDuration": round(raw.n_times / raw.info["sfreq"], 3),
    }
    high = raw.info["lowpass"]
    if high and high < raw.info["sfreq"] / 2:
        content["HardwareFilters"] = {
            "Low-pass (from the BDF header)": {"HighCutoff": high}
        }
    else:
        content["HardwareFilters"] = PAPER_HARDWARE_FILTER
    if (sub, ses) in ARTEFACT_NOTES:
        content["SubjectArtefactDescription"] = ARTEFACT_NOTES[(sub, ses)]
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-dir", type=Path, default=None, help="ds003626 folder")
    parser.add_argument(
        "--overwrite", action="store_true", help="replace existing files"
    )
    args = parser.parse_args()

    data_dir = args.data_dir or find_project_root(HERE) / "ds003626"
    if not data_dir.is_dir():
        sys.exit(f"Dataset folder not found: {data_dir}")
    written, kept = [], []
    unknown_codes: dict[int, int] = {}

    def track(path: Path, done: bool) -> None:
        (written if done else kept).append(path.relative_to(data_dir))

    # dataset_description.json is always updated (BIDSVersion, HowToAcknowledge)
    track(
        data_dir / "dataset_description.json",
        write_json(
            data_dir / "dataset_description.json", dataset_description(data_dir), True
        ),
    )
    track(
        data_dir / "participants.tsv",
        write_tsv(
            data_dir / "participants.tsv",
            ["participant_id", "age", "gender", "handedness"],
            PARTICIPANTS,
            args.overwrite,
        ),
    )
    track(
        data_dir / "participants.json",
        write_json(data_dir / "participants.json", PARTICIPANTS_JSON, args.overwrite),
    )
    track(
        data_dir / f"task-{TASK}_eeg.json",
        write_json(data_dir / f"task-{TASK}_eeg.json", EEG_JSON, args.overwrite),
    )
    track(
        data_dir / f"task-{TASK}_events.json",
        write_json(data_dir / f"task-{TASK}_events.json", EVENTS_JSON, args.overwrite),
    )
    deriv = data_dir / "derivatives"
    if deriv.is_dir():
        track(
            deriv / "dataset_description.json",
            write_json(
                deriv / "dataset_description.json",
                DERIVATIVES_DESCRIPTION,
                args.overwrite,
            ),
        )
        track(
            deriv / "events.json",
            write_json(deriv / "events.json", TRIAL_COLUMNS_JSON, args.overwrite),
        )

    recordings = sorted(
        data_dir.glob(f"sub-*/ses-*/eeg/sub-*_ses-*_task-{TASK}_eeg.bdf")
    )
    if not recordings:
        print(f"No .bdf files found under {data_dir}")
    for bdf in recordings:
        stem = bdf.name.removesuffix("_eeg.bdf")
        print(f"  {stem}")
        raw = mne.io.read_raw_bdf(bdf, preload=False, verbose="ERROR")
        track(
            bdf.with_name(f"{stem}_eeg.json"),
            write_json(
                bdf.with_name(f"{stem}_eeg.json"),
                recording_json(raw, *stem.split("_")[:2]),
                args.overwrite,
            ),
        )
        track(
            bdf.with_name(f"{stem}_channels.tsv"),
            write_tsv(
                bdf.with_name(f"{stem}_channels.tsv"),
                [
                    "name",
                    "type",
                    "units",
                    "low_cutoff",
                    "high_cutoff",
                    "description",
                    "status",
                ],
                channel_rows(raw),
                args.overwrite,
            ),
        )
        rows = event_rows(raw)
        for row in rows:
            if row[4] == "unknown":
                unknown_codes[row[3]] = unknown_codes.get(row[3], 0) + 1
        track(
            bdf.with_name(f"{stem}_events.tsv"),
            write_tsv(
                bdf.with_name(f"{stem}_events.tsv"),
                ["onset", "duration", "sample", "value", "trial_type", "condition"],
                rows,
                args.overwrite,
            ),
        )
        del raw

    if unknown_codes:
        print(f"Codes not in Table 3 (trial_type 'unknown'): {unknown_codes}")
    print(
        f"\nWrote {len(written)} files"
        + (f", kept {len(kept)} existing" if kept else "")
    )
    if kept:
        print("  (use --overwrite to replace them)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
