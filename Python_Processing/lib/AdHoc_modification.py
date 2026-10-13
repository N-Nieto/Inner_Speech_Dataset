"""
Created on Thu Aug  6 11:53:54 2020

@author: Nicolás Nieto
@email: nnieto@sinc.unl.edu.ar

Ad hoc correction subject 3:
    Subject S03 reported that in block 1 he did not perform the inner speech paradigm.
    Instead, he performed the visualized paradigm.
"""

from pathlib import Path

import numpy as np

from lib.derivatives_io import (
    EVENTS_COLUMNS,
    derivative_path,
    load_events,
    save_events,
)

# Rows (0-based) of sub-03 ses-01 recorded as inner speech but performed as
# visualized condition: the second inner speech run (trials 80-119)
_SUB03_SES01_ROWS = slice(80, 120)
_CONDITION_COL = EVENTS_COLUMNS.index("condition")
_VISUALIZED = 2


def adhoc_subject_3(derivatives_dir: Path, verbose: bool = True) -> None:
    """
    Correct and save events data for Subject 3, Block 1 (paradigm execution error).

    The subject performed the visualized paradigm instead of inner speech in
    trials 80-119 (40 trials), so their condition label is set to 2
    (visualized). Running it more than once gives the same result.

    Parameters:
    - derivatives_dir (Path): The ``derivatives`` folder written by the pipeline.
    - verbose (bool): Whether to print additional information. Default True.

    Raises:
    - FileNotFoundError: If the events file cannot be found.
    - ValueError: If the data doesn't match expected structure or correction fails.
    """
    n_s, n_b = 3, 1
    file_path = derivative_path(derivatives_dir, n_s, n_b, "events.dat")

    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"Events file not found: {file_path}")

    events = load_events(derivatives_dir, n_s, n_b)

    if verbose:
        print(f"Loaded events data from: {file_path}")
        print(f"Data shape: {events.shape}")

    # Check if we have enough rows for the correction
    if len(events) < _SUB03_SES01_ROWS.stop:
        raise ValueError(
            f"Expected at least {_SUB03_SES01_ROWS.stop} rows, got {len(events)}"
        )

    if verbose:
        _print_condition_counts("Original", events)

    # Apply correction: trials 80-119 (40 trials) -> visualized condition
    events[_SUB03_SES01_ROWS, _CONDITION_COL] = _VISUALIZED

    if verbose:
        _print_condition_counts("Updated", events)

    # Validate the correction
    condition = events[:, _CONDITION_COL]
    code_0_count = int((condition == 0).sum())
    code_1_count = int((condition == 1).sum())
    code_2_count = int((condition == 2).sum())

    expected_0 = 40  # Pronounced trials
    expected_1 = 40  # Inner speech trials
    expected_2 = 120  # Visualized trials (80 original + 40 corrected)

    if (
        code_0_count == expected_0
        and code_1_count == expected_1
        and code_2_count == expected_2
    ):
        if verbose:
            print("✓ AdHoc correction successful for Subject 3 Block 1")
            print(f"  - condition 0 (Pronounced): {code_0_count} trials")
            print(f"  - condition 1 (Inner speech): {code_1_count} trials")
            print(f"  - condition 2 (Visualized): {code_2_count} trials")
    else:
        error_msg = (
            f"Correction validation failed. Expected: "
            f"0={expected_0}, 1={expected_1}, 2={expected_2}. "
            f"Got: 0={code_0_count}, 1={code_1_count}, 2={code_2_count}"
        )
        raise ValueError(error_msg)

    # Save the corrected data back to the same file
    save_events(events, derivatives_dir, n_s, n_b)

    if verbose:
        print(f"✓ Corrected data saved to: {file_path}")


def _print_condition_counts(label: str, events: np.ndarray) -> None:
    values, counts = np.unique(events[:, _CONDITION_COL], return_counts=True)
    print(f"{label} condition distribution:")
    for code, count in zip(values, counts, strict=True):
        print(f"  condition {code}: {count} trials")
