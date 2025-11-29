# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 11:53:54 2020

@author: Nicolás Nieto
@email: nnieto@sinc.unl.edu.ar

Ad hoc correction subject 3:
    Subject S03 inform in block 1 he did not realice the inner speech paradigm.
    Instaed he perform the visualized paradigm.
"""
import pandas as pd
from pathlib import Path


def adhoc_subject_3(root_dir: Path, verbose: bool = True) -> None:
    """
    Corrects and saves events data for Subject 3, Block 1 by fixing paradigm execution errors.

    This function specifically addresses an issue where the subject executed a different
    paradigm than intended for trials 80-119 (40 trials total).

    Parameters:
    - root_dir (Path): The root directory containing the data.
    - verbose (bool): Whether to print additional information. Default True.

    Raises:
    - FileNotFoundError: If the events file cannot be found.
    - ValueError: If the data doesn't match expected structure or correction fails.
    - Exception: For other unexpected errors.
    """
    num_s = "sub-03"
    n_b = 1

    try:
        # Construct file path
        file_path = (
            root_dir 
            / "derivatives" 
            / num_s 
            / f"ses-0{n_b}" 
            / f"{num_s}_ses-0{n_b}_events.csv"
        )
        
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Events file not found: {file_path}")

        # Load events data using pandas (preserving column structure)
        events_df = pd.read_csv(file_path, index_col=0)
        
        if verbose:
            print(f"Loaded events data from: {file_path}")
            print(f"Data shape: {events_df.shape}")
            print(f"Columns: {list(events_df.columns)}")

        # Check if we have enough rows for the correction
        if len(events_df) < 120:
            raise ValueError(f"Expected at least 120 rows, got {len(events_df)}")

        # Identify the code column (assuming it's the third column or named 'Code')
        code_column = None
        if 'condition' in events_df.columns:
            code_column = 'condition'
        elif events_df.shape[1] >= 3:
            # Assume third column is the code if no 'Code' column found
            code_column = events_df.columns[2]
        else:
            raise ValueError("Could not identify code column in events data")

        if verbose:
            original_counts = events_df[code_column].value_counts().sort_index()
            print("Original code distribution:")
            for code, count in original_counts.items():
                print(f"  condition {code}: {count} trials")

        # Apply correction: change codes for trials 80-119 (40 trials) to 2
        # Note: DataFrame indexing is 0-based, so rows 80-119 correspond to indices 80-119
        events_df.loc[80:119, code_column] = 2

        if verbose:
            updated_counts = events_df[code_column].value_counts().sort_index()
            print("Updated code distribution:")
            for code, count in updated_counts.items():
                print(f"  condition {code}: {count} trials")

        # Validate the correction
        code_0_count = (events_df[code_column] == 0).sum()
        code_1_count = (events_df[code_column] == 1).sum() 
        code_2_count = (events_df[code_column] == 2).sum()

        expected_0 = 40  # Pronounced trials
        expected_1 = 40  # Imagined trials  
        expected_2 = 120 # Visually guided trials (80 original + 40 corrected)

        if code_0_count == expected_0 and code_1_count == expected_1 and code_2_count == expected_2:
            if verbose:
                print("✓ AdHoc correction successful for Subject 3 Block 1")
                print(f"  - condition 0 (Pronounced): {code_0_count} trials")
                print(f"  - condition 1 (Imagined): {code_1_count} trials")
                print(f"  - condition 2 (Visually guided): {code_2_count} trials")
        else:
            error_msg = (
                f"Correction validation failed. Expected: "
                f"0={expected_0}, 1={expected_1}, 2={expected_2}. "
                f"Got: 0={code_0_count}, 1={code_1_count}, 2={code_2_count}"
            )
            raise ValueError(error_msg)

        # Save the corrected data back to the same file
        events_df.to_csv(file_path, index=False)
        
        if verbose:
            print(f"✓ Corrected data saved to: {file_path}")
