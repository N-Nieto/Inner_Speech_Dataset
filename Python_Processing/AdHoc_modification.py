# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 11:53:54 2020

@author: Nicolás Nieto
@email: nnieto@sinc.unl.edu.ar

Ad hoc correction subject 3:

    Subject S03 inform in block 1 he did not realice the inner speech paradigm.
    Instaed he perform the visualized paradigm.
"""
import numpy as np


def adhoc_subject_3(root_dir: str, verbose: bool = True) -> None:
    """
    Corrects and saves events data for Subject 3, Block 1.

    Parameters:
    - root_dir (str): The root directory containing the data.
    - verbose (bool): Whether to print additional information.

    Raises:
    - Exception: If the correction fails.
    """
    num_s: str = 'sub-03'
    n_b: int = 1

    # Load events data file
    file_name: str = f"{root_dir}/derivatives/{num_s}/ses-0{n_b}/{num_s}_ses-0{n_b}_events.dat"         # noqa
    y_s3: np.ndarray = np.load(file_name, allow_pickle=True)

    # Correct the 40 trials where the subject executed a different paradigm
    y_s3[80:120, 2] = 2

    if verbose:
        # Check if only 40 trials of Pronounced are left
        if (
            np.count_nonzero(y_s3[:, 2] == 0) == 40 and
            np.count_nonzero(y_s3[:, 2] == 1) == 40 and
            np.count_nonzero(y_s3[:, 2] == 2) == 120
        ):
            print("AdHoc Correction Subject 3 Block 1")
        else:
            raise Exception("Correction fail")

    # Save the corrected data
    y_s3.dump(file_name)
