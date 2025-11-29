# -*- coding: utf-8 -*-

"""
Created on Wed Oct 16 15:18:45 2019
Last Update: 09/06/2022

@author: Nieto Nicolás
@email: nnieto@sinc.unl.edu.ar
"""

import mne
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional


# Constants for better readability and maintainability
EVENT_CODES = {
    "STARTS": [11, 12, 13, 14],
    "BLOCKS": [21, 22, 23],
    "TAGS": [31, 32, 33, 34],
    "MARKS": [42, 44, 45, 46],
    "QUESTIONS": [16, 17],
    "ANSWERS": [61, 62, 63, 64],
    "EXCLUDE": 65536,
}
TIME_OFFSETS = {
    42: 1945,  # Start mark
    44: 2594,  # Useful interval
    45: 1075,  # Concentration interval
    46: 1075,  # Rest interval
    17: 2092,  # Question
    61: 2092,  # Answer
    "TAG": 563,  # For tags 31-34
}


EXPECTED_TRANSITIONS = {
    42: [31, 32, 33, 34, 44],  # Start mark -> Tags or Useful interval
    46: [42, 16, 17, 61, 62, 63, 64],  # Rest interval -> Start, Questions, or Answers
    17: [61, 62, 63, 64],  # Question -> Answers
    44: [45, 46],  # Useful interval -> Concentration or Rest
    45: [46],  # Concentration interval -> Rest
}

GROUP_TRANSITIONS = {
    "BLOCKS": (21, 22, 23),  # Should be followed by 42
    "ANSWERS": (61, 62, 63, 64),  # Should be followed by 42 or 16
    "TAGS": (31, 32, 33, 34),  # Should be followed by 44 or 45
}


def event_correction(events: pd.DataFrame) -> pd.DataFrame:
    """
    Correct and validate event sequences in EEG/MRI data by detecting and inserting missing events.

    This function analyzes temporal event sequences to identify missing events based on expected
    patterns and relationships between event codes. It inserts corrected events with appropriate
    timing offsets and validates the final sequence against expected constraints.

    Args:
        events: DataFrame with at least 3 columns representing:
            - Column 0: Time stamps (numeric)
            - Column 1: Trigger information (any type)
            - Column 2: Event codes (numeric)

    Returns:
        pd.DataFrame: Corrected events DataFrame with same structure as input, sorted by time.
        Missing events are inserted with calculated timestamps.

    Raises:
        ValueError: If input DataFrame doesn't have at least 3 columns
        Exception: If corrected event sequence fails sanity checks

    Example:
        >>> raw_events = pd.DataFrame({
        ...     'time': [1000, 2000, 3000],
        ...     'trigger': [0, 0, 0],
        ...     'code': [42, 31, 44]
        ... })
        >>> corrected_events = event_correction(raw_events)
        >>> print(f"Original: {len(raw_events)} events, Corrected: {len(corrected_events)} events")
    """
    print("Starting event correction process...")

    # Step 1: Validate input and prepare clean working data
    events_df = _validate_input_dataframe(events)

    # Step 2: Build analysis arrays for event sequence
    events_code, event_count = _build_event_analysis_arrays(events_df)

    # Step 3: Detect sequence warnings and missing events
    warnings = _detect_sequence_warnings(events_code, event_count)

    # Step 4: Apply corrections by inserting missing events
    corrected_events_df = _apply_event_corrections(events_df, warnings)

    # Step 5: Build final event count from corrected data for validation
    corrected_codes = corrected_events_df.iloc[:, 2].astype(int).to_numpy()
    unique_codes_fix, counts_fix = np.unique(corrected_codes, return_counts=True)
    event_count_fix = np.zeros((len(unique_codes_fix), 2), dtype=int)
    event_count_fix[:, 0] = unique_codes_fix
    event_count_fix[:, 1] = counts_fix

    # Step 6: Run comprehensive sanity checks on corrected events
    _validate_corrected_events(event_count_fix)

    print("Event correction process completed successfully")
    return corrected_events_df


def _validate_input_dataframe(events: pd.DataFrame) -> pd.DataFrame:
    """
    Validate input DataFrame and return a clean working copy.

    Args:
        events: Input events DataFrame with at least 3 columns (time, trigger, code)

    Returns:
        pd.DataFrame: Cleaned events DataFrame with excluded codes removed

    Raises:
        ValueError: If input doesn't have required columns
    """
    if events.shape[1] < 3:
        raise ValueError(
            "Events DataFrame must have at least 3 columns (time, trigger, code)"
        )

    # Exclude specific tag and ensure proper filtering
    mask = events.iloc[:, 2].astype(int) != EVENT_CODES["EXCLUDE"]
    events = events.loc[mask].reset_index(drop=True)

    return events


def _build_event_analysis_arrays(
    events_df: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build event code arrays for sequence analysis.

    Args:
        events_df: Cleaned events DataFrame

    Returns:
        Tuple[np.ndarray, np.ndarray]:
            - Events_code array with shape (n_events, 2) containing [code, position]
            - Event_count array with shape (n_unique_codes, 2) containing [code, count]
    """
    codes = events_df.iloc[:, 2].astype(int).to_numpy()

    # Build Events_code array: [code, position]
    events_code = np.zeros((len(codes), 2), dtype=int)
    events_code[:, 0] = codes
    events_code[:, 1] = np.arange(len(codes), dtype=int)

    # Build Event_count array: [code, count]
    unique_codes, counts = np.unique(codes, return_counts=True)
    event_count = np.zeros((len(unique_codes), 2), dtype=int)
    event_count[:, 0] = unique_codes
    event_count[:, 1] = counts

    return events_code, event_count


def _detect_missing_tag_code(event_count: np.ndarray) -> int:
    """
    Identify which tag code (31-34) is missing based on minimum count.

    Args:
        event_count: Event_count array with [code, count]

    Returns:
        int: The tag code with the minimum count (likely missing)
    """
    tag_counts = []
    for tag_code in EVENT_CODES["TAGS"]:
        counts = event_count[event_count[:, 0] == tag_code, 1]
        tag_counts.append(int(counts[0]) if len(counts) else np.iinfo(int).max)

    min_idx = int(np.argmin(tag_counts))
    return EVENT_CODES["TAGS"][min_idx]


def _check_event_transition(
    current_code: int, next_code: int, event_count: np.ndarray
) -> Optional[int]:
    """
    Check if transition between current and next event code follows expected patterns.

    Args:
        current_code: Current event code in sequence
        next_code: Next event code in sequence
        event_count: Event_count array for statistical analysis

    Returns:
        Optional[int]: Missing event code if transition is invalid, None if valid
    """
    # Check: 42 (Start mark) should be followed by Tags (31-34) or 44 (Useful interval)
    if current_code == 42 and next_code not in EXPECTED_TRANSITIONS[42]:
        if next_code == 44:
            return _detect_missing_tag_code(event_count)
        return 42  # Missing start mark

    # Check: 46 (Rest interval) should be followed by valid next events
    elif current_code == 46 and next_code not in EXPECTED_TRANSITIONS[46]:
        if next_code in EVENT_CODES["ANSWERS"]:
            return 17  # Missing question before answer
        return 42  # Missing start mark

    # Check: Blocks (21-23) should be followed by 42 (Start mark)
    elif current_code in GROUP_TRANSITIONS["BLOCKS"] and next_code != 42:
        return 42  # Missing start after block

    # Check: Answers (61-64) should be followed by 42 or 16
    elif current_code in GROUP_TRANSITIONS["ANSWERS"] and next_code not in (42, 16):
        return 42  # Missing start after answer

    # Check: Tags (31-34) should be followed by 44 or 45
    elif current_code in GROUP_TRANSITIONS["TAGS"] and next_code not in (44, 45):
        return 44  # Missing useful interval after tag

    # Check: 44 (Useful interval) should be followed by 45 or 46
    elif current_code == 44 and next_code not in EXPECTED_TRANSITIONS[44]:
        return 45  # Missing concentration interval

    # Check: 45 (Concentration interval) should be followed by 46 (Rest interval)
    elif current_code == 45 and next_code != 46:
        return 46  # Missing rest interval

    # Check: 17 (Question) should be followed by Answers (61-64)
    elif current_code == 17 and next_code not in EXPECTED_TRANSITIONS[17]:
        return 61  # Missing answer after question

    return None  # Valid transition


def _detect_sequence_warnings(
    events_code: np.ndarray, event_count: np.ndarray
) -> List[Dict[str, int]]:
    """
    Scan event sequence to detect missing events and invalid transitions.

    Args:
        events_code: Events_code array with [code, position]
        event_count: Event_count array with [code, count]

    Returns:
        List[Dict[str, int]]: List of warnings with position and missing code
    """
    warnings = []

    for i in range(len(events_code) - 1):
        current_code = events_code[i, 0]
        next_code = events_code[i + 1, 0]

        missing_code = _check_event_transition(current_code, next_code, event_count)

        if missing_code is not None:
            warning_msg = f"Warning, missing code {missing_code} at position {i}"
            print(warning_msg)

            warnings.append(
                {
                    "position": i,
                    "missing_code": missing_code,
                    "current_code": current_code,
                    "next_code": next_code,
                }
            )

    return warnings


def _create_correction_event(
    events_df: pd.DataFrame, position: int, missing_code: int
) -> List:
    """
    Create a new event row for insertion as a correction.

    Args:
        events_df: Original events DataFrame
        position: Position in original sequence where correction is needed
        missing_code: Event code to insert

    Returns:
        List: New event row with calculated timestamp and missing code
    """
    base_time = int(events_df.iloc[position, 0])

    # Calculate correction time based on missing code type
    if missing_code in TIME_OFFSETS:
        time_offset = TIME_OFFSETS[missing_code]
    else:
        time_offset = TIME_OFFSETS["TAG"]  # Default offset for tags

    correction_time = base_time + time_offset

    # Build correction row matching original DataFrame structure
    correction_row = [0] * events_df.shape[1]
    correction_row[0] = correction_time  # Time column
    correction_row[2] = int(missing_code)  # Code column

    return correction_row


def _apply_event_corrections(
    events_df: pd.DataFrame, warnings: List[Dict]
) -> pd.DataFrame:
    """
    Apply detected corrections to events DataFrame by inserting missing events.

    Args:
        events_df: Original events DataFrame
        warnings: List of detected warnings with correction information

    Returns:
        pd.DataFrame: Corrected events DataFrame with missing events inserted
    """
    if not warnings:
        print("No warnings detected, no corrections needed")
        return events_df

    print(f"Applying {len(warnings)} corrections to events")

    # Generate correction rows for all detected issues
    correction_rows = []
    for warning in warnings:
        correction_row = _create_correction_event(
            events_df, warning["position"], warning["missing_code"]
        )
        correction_rows.append(correction_row)

    # Create corrections DataFrame and merge with original
    corrections_df = pd.DataFrame(correction_rows, columns=events_df.columns)
    corrected_events = pd.concat([events_df, corrections_df], ignore_index=True)

    # Sort by time (first column) to maintain temporal order
    time_column = corrected_events.columns[0]
    corrected_events = corrected_events.sort_values(by=time_column).reset_index(
        drop=True
    )

    return corrected_events


def _get_event_count(count_array: np.ndarray, target_code: int) -> int:
    """
    Extract count for a specific event code from count array.

    Args:
        count_array: Event_count array with [code, count]
        target_code: Event code to count

    Returns:
        int: Count of specified event code, 0 if not found
    """
    matching_indices = np.where(count_array[:, 0] == target_code)[0]
    return int(count_array[matching_indices, 1][0]) if matching_indices.size else 0


def _validate_corrected_events(event_count_fix: np.ndarray):
    """
    Run comprehensive sanity checks on corrected event counts.

    Args:
        event_count_fix: Event_count array from corrected events

    Raises:
        Exception: With descriptive message if any sanity check fails
    """
    # Check 1: Start codes (11-14) should each appear exactly once
    start_counts = [
        _get_event_count(event_count_fix, code) for code in EVENT_CODES["STARTS"]
    ]
    if not all(count == 1 for count in start_counts):
        raise Exception("Missing or duplicate start codes")
    print("Start codes OK")

    # Check 2: Block consistency (15, 16, 51 counts should follow specific relationship)
    count_15 = _get_event_count(event_count_fix, 15)
    count_16 = _get_event_count(event_count_fix, 16)
    count_51 = _get_event_count(event_count_fix, 51)

    if not (count_15 == count_16 and count_15 == count_51 + 1):
        raise Exception("Missing or inconsistent blocks")
    print("Blocks OK")

    # Check 3: Tags (31-34) should all have equal counts
    tag_counts = [
        _get_event_count(event_count_fix, code) for code in EVENT_CODES["TAGS"]
    ]
    if not all(count == tag_counts[0] for count in tag_counts):
        raise Exception("Missing or inconsistent tags")
    print("Tags OK")

    # Check 4: Marks (42, 44, 45, 46) should all have equal counts
    mark_counts = [
        _get_event_count(event_count_fix, code) for code in EVENT_CODES["MARKS"]
    ]
    if not all(count == mark_counts[0] for count in mark_counts):
        raise Exception("Missing or inconsistent marks")
    print("Marks OK")

    # Check 5: Cognitive control - questions should match answers
    question_count = _get_event_count(event_count_fix, 17)
    total_answers = sum(
        _get_event_count(event_count_fix, code) for code in EVENT_CODES["ANSWERS"]
    )

    if question_count != total_answers:
        raise Exception("Missing cognitive control question/answer pairs")
    print("Cognitive control OK")


def cognitive_control_check(events: pd.DataFrame) -> Tuple[int, int]:
    """
    Check the correctness of cognitive control answers using vectorized pandas operations.

    This version uses pandas shift operations for maximum efficiency.

    Parameters:
    - events (pd.DataFrame): Corrected events DataFrame from event_correction function.

    Returns:
    - tuple: A tuple containing the count of correct and wrong answers.
    """
    events_pd = events.copy()
    # Add shifted columns for comparison
    events_pd["prev_4_code"] = events_pd["Code"].shift(
        4
    )  # Code from 4 positions back (the tag)
    events_pd["next_code"] = events_pd["Code"].shift(
        -1
    )  # Code from next position (the answer)

    # Identify question events and check answers
    question_mask = events["Code"] == 17
    valid_question_mask = (
        question_mask
        & (events_pd["prev_4_code"].notna())
        & (events_pd["next_code"].notna())
    )

    # Filter to valid questions with sufficient context
    valid_questions = events_pd[valid_question_mask]

    if len(valid_questions) == 0:
        print("No cognitive control questions found with sufficient context")
        return 0, 0

    # Calculate expected answers and check correctness
    valid_questions = valid_questions.copy()
    valid_questions["expected_answer"] = valid_questions["prev_4_code"] + 30
    valid_questions["is_correct"] = (
        valid_questions["next_code"] == valid_questions["expected_answer"]
    )

    # Count results
    ans_r = valid_questions["is_correct"].sum()
    ans_w = len(valid_questions) - ans_r

    # Handle questions without sufficient context
    insufficient_context_questions = question_mask.sum() - len(valid_questions)
    if insufficient_context_questions > 0:
        print(
            f"Warning: {insufficient_context_questions} questions skipped due to insufficient context"
        )
        ans_w += insufficient_context_questions  # Count these as wrong for conservative reporting

    # Validation and reporting
    total_questions_found = question_mask.sum()

    if ans_r + ans_w == total_questions_found:
        if ans_w == 0:
            print("All cognitive control answers are correct")
        else:
            print(
                f"Cognitive control results: {ans_r} correct, {ans_w} wrong out of {total_questions_found} questions"
            )
    else:
        print(
            f"Validation note: Found {total_questions_found} questions, validated {ans_r + ans_w}"
        )

    return int(ans_r), int(ans_w)


def count_events_by_condition(
    events: pd.DataFrame,
) -> Tuple[List[int], List[int], List[int]]:
    """
    Count events by condition in the corrected events data.

    Parameters:
    - events (pd.DataFrame): Corrected events DataFrame from event_correction function.

    Returns:
    - tuple: A tuple containing the counts for Pron, Im, and Vis conditions.
             Each is a list of counts for tags [31, 32, 33, 34] in that condition.
    """
    events_array = events.iloc[:, 2].to_numpy()  # Use only the code column

    # Initialize counters
    pron = 0
    im = 0
    vis = 0

    pron_count = [0, 0, 0, 0]  # Counts for tags 31, 32, 33, 34 in Pron condition
    im_count = [0, 0, 0, 0]  # Counts for tags 31, 32, 33, 34 in Im condition
    vis_count = [0, 0, 0, 0]  # Counts for tags 31, 32, 33, 34 in Vis condition

    for i in range(len(events_array)):
        current_code = events_array[i]

        # Update current condition
        if current_code == 21:
            pron = 1
            im = 0
            vis = 0
        elif current_code == 22:
            pron = 0
            im = 1
            vis = 0
        elif current_code == 23:
            pron = 0
            im = 0
            vis = 1

        # Count tags based on current condition
        if 31 <= current_code <= 34:
            tag_index = current_code - 31
            if pron == 1:
                pron_count[tag_index] += 1
            elif im == 1:
                im_count[tag_index] += 1
            elif vis == 1:
                vis_count[tag_index] += 1

    # Validate tag distribution
    if (
        min(pron_count) == max(pron_count)
        and min(im_count) == max(im_count)
        and min(vis_count) == max(vis_count)
    ):
        print("Tags are evenly distributed across conditions")
    else:
        raise ValueError("Missing or incorrect tags distribution across conditions")

    return pron_count, im_count, vis_count


def add_block_tag(events: pd.DataFrame, N_B: int) -> pd.DataFrame:
    """
    Add block tags to the corrected events data.

    Parameters:
    - events (pd.DataFrame): Corrected events DataFrame from event_correction function.
    - N_B (int): Block number to be added as a tag.

    Returns:
    - pd.DataFrame: The events data with the block tags added as a new column.
    """
    # Add as new column to DataFrame
    events["block"] = N_B

    return events


def add_condition_tag(events: pd.DataFrame) -> pd.DataFrame:
    """
    Add condition tags to the corrected events data.

    Parameters:
    - events (pd.DataFrame): Corrected events DataFrame from event_correction function.

    Returns:
    - pd.DataFrame: The events data with the condition tags added as a new column.
                    Only includes rows with tag codes 31, 32, 33, 34.
    """
    events_array = events.iloc[:, :3].to_numpy()  # Use first 3 columns

    mod_tag = np.zeros(len(events_array), dtype=int)
    current_mod = 0  # 0: Pron, 1: Im, 2: Vis, 3: Unknown

    for i in range(len(events_array)):
        current_code = events_array[i, 2]

        # Update current condition
        if current_code == 21:
            current_mod = 0  # Pron
        elif current_code == 22:
            current_mod = 1  # Im
        elif current_code == 23:
            current_mod = 2  # Vis
        # Don't reset to 3 for other codes - maintain last known condition

        mod_tag[i] = current_mod

    # Add condition tag to DataFrame
    events["condition"] = mod_tag

    # Filter to only include tag events (31, 32, 33, 34) using MNE
    # First convert to MNE events format (time, duration, code)
    mne_events = events.iloc[:, :3].to_numpy()
    mne_events = mne_events.astype(int)  # Ensure integer type

    # Use MNE to pick only the tag events
    try:
        picked_indices = mne.pick_events(mne_events, include=[31, 32, 33, 34])
        events_filtered = events.iloc[picked_indices].reset_index(drop=True)
        return events_filtered
    except Exception as e:
        print(f"Warning: MNE event picking failed: {e}")
        print("Falling back to manual filtering...")
        # Manual filtering as fallback
        mask = events.iloc[:, 2].isin([31, 32, 33, 34])
        return events[mask].reset_index(drop=True)


def delete_trigger_column(events: pd.DataFrame) -> pd.DataFrame:
    """
    Delete the trigger column from the corrected events data.

    Parameters:
    - events (pd.DataFrame): Corrected events DataFrame from event_correction function.

    Returns:
    - pd.DataFrame: Events data with the trigger column removed.
    """
    # Check if "Trigger" column exists
    if "Trigger" in events.columns:
        events_modified = events.drop(columns=["Trigger"])
        print("Trigger column deleted successfully")
    else:
        print("Warning: No 'Trigger' column found to delete")
        events_modified = events

    return events_modified


def standardize_labels(events: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize labels in the corrected events data using pandas replace method.

    Parameters:
    - events (pd.DataFrame): Corrected events DataFrame from event_correction function.

    Returns:
    - pd.DataFrame: Events data with standardized labels (31->0, 32->1, 33->2, 34->3).
                    All other codes remain unchanged.
    """

    # Define the mapping dictionary for replacement
    code_mapping = {
        31: 0,  # "Arriba" / "Up" -> 0
        32: 1,  # "Abajo" / "Down" -> 1
        33: 2,  # "Derecha" / "Right" -> 2
        34: 3,  # "Izquierda" / "Left" -> 3
    }

    # Use pandas replace method for efficient mapping
    events["Code"] = events["Code"].replace(code_mapping)

    return events


def check_baseline_tags(events: pd.DataFrame) -> pd.DataFrame:
    """
    Check and add baseline tags to the corrected events DataFrame if necessary.

    Parameters:
    - events (pd.DataFrame): Corrected events DataFrame from event_correction function.
                            Expected to have at least 3 columns where
                            column 0 is time, column 2 is the event code.

    Returns:
    - pd.DataFrame: Events data with baseline tags checked and potentially added.
    """
    if len(events) < 4:
        raise ValueError(
            "Events DataFrame must have at least 4 rows to check baseline tags"
        )

    # The tag 14 (end of baseline) should be in the 4th row in the 3rd column
    if int(events.iloc[3, 2]) != 14:
        print("Adding missing baseline end tag...")

        # Baseline duration is 15 seconds, sampling freq assumed 1024
        baseline_duration = 15 * 1024  # 15 seconds * 1024 Hz
        time = int(events.iloc[2, 0]) + baseline_duration

        # Build correction row using the same columns as the input DataFrame
        correction_data = {events.columns[0]: time, events.columns[2]: 14}

        # Fill other columns with defaults (0 or appropriate values)
        for col in events.columns:
            if col not in correction_data:
                correction_data[col] = 0

        correction = pd.DataFrame([correction_data])

        # Append, sort by the time column, and reset index
        events_corrected = pd.concat([events, correction], ignore_index=True)
        events_corrected = events_corrected.sort_values(
            by=events.columns[0]
        ).reset_index(drop=True)

    else:
        print("Baseline tags are correct")
        events_corrected = events

    return events_corrected
