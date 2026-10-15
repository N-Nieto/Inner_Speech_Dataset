"""Selecting trials by condition and class across subjects and sessions."""

import mne
import numpy as np
import pytest

from innerspeech.data_extractions import (
    extract_condition_epochs,
    extract_data_from_subject,
)
from innerspeech.data_processing import filter_by_class, filter_by_condition


@pytest.mark.parametrize(
    ("condition", "class_label"),
    [("all", "all"), ("inner", "all"), ("vis", "left"), ("pron", "up")],
)
def test_matches_loading_everything_then_filtering(derivatives, condition, class_label):
    epochs = extract_condition_epochs(
        derivatives, [1, 2], "eeg", condition=condition, class_label=class_label
    )
    expected_x, expected_y = [], []
    for n_s in (1, 2):
        x, y = extract_data_from_subject(derivatives, n_s, "eeg")
        x, y = filter_by_condition(x, y, condition)
        x, y = filter_by_class(x, y, class_label)
        expected_x.append(x)
        expected_y.append(y)
    expected_x, expected_y = np.concatenate(expected_x), np.concatenate(expected_y)

    assert np.array_equal(epochs.get_data(), expected_x)
    assert np.array_equal(epochs.metadata["class"], expected_y[:, 1])
    assert np.array_equal(epochs.metadata["session"], expected_y[:, 3])
    assert np.array_equal(epochs.events[:, 2], expected_y[:, 1] + 1)
    assert isinstance(epochs, mne.EpochsArray)


def test_baseline_is_rejected(derivatives):
    with pytest.raises(ValueError, match="baseline"):
        extract_condition_epochs(derivatives, [1], "baseline")
