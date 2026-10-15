"""Event extraction, correction and standardisation on synthetic recordings."""

import numpy as np
import pytest

from innerspeech.data_extractions import get_events_from_raw
from innerspeech.derivatives_io import _as_events_array
from innerspeech.events_analysis import (
    add_block_tag,
    add_condition_tag,
    check_baseline_tags,
    cognitive_control_check,
    delete_trigger_column,
    event_correction,
    standardize_labels,
)
from innerspeech.exceptions import EventSequenceError
from synthetic import make_event_sequence, make_raw

TAGS, MARKS = (31, 32, 33, 34), (42, 44, 45, 46)


def corrected(**kw):
    events = get_events_from_raw(make_raw(**kw), 1, 1)
    events = check_baseline_tags(events)
    return event_correction(events=events)


def counts(events, codes):
    values = events["Code"].to_numpy()
    return [int((values == c).sum()) for c in codes]


def nth(code, n, **kw):
    """Index of the n-th event with ``code`` in the synthetic sequence."""
    events, _ = make_event_sequence(**kw)
    return [i for i, (_, c) in enumerate(events) if c == code][n]


def test_clean_session():
    events = corrected()
    assert counts(events, TAGS) == [50] * 4
    assert counts(events, MARKS) == [200] * 4
    assert 65536 not in events["Code"].to_numpy()
    assert cognitive_control_check(events) == (20, 0)


def test_missing_tag_is_restored():
    events = corrected(drop=(nth(31, 5),))
    assert counts(events, TAGS) == [50] * 4


def test_missing_marks_and_spurious_trigger():
    drop = (nth(44, 10), nth(46, 30))
    events = corrected(drop=drop, spurious=(500_000,))
    assert counts(events, MARKS) == [200] * 4
    assert 65536 not in events["Code"].to_numpy()


def test_inserted_event_lies_between_its_neighbours():
    i = nth(44, 10)
    full, _ = make_event_sequence()
    events = corrected(drop=(i,))
    times = events["Time"].to_numpy()
    inserted = times[(events["Code"].to_numpy() == 44)][10]
    assert full[i - 1][0] < inserted < full[i + 1][0]


def test_standardised_events():
    events = corrected()
    events = add_condition_tag(events)
    events = add_block_tag(events, N_B=2)
    events = standardize_labels(delete_trigger_column(events))
    array = _as_events_array(events)
    assert array.shape == (200, 4)
    assert np.bincount(array[:, 1]).tolist() == [50] * 4
    assert np.bincount(array[:, 2]).tolist() == [40, 80, 80]
    assert (array[:, 3] == 2).all()
    assert (np.diff(array[:, 0]) > 0).all()


# Known limitations of the current correction (see the discussion of a more
# general approach); these tests document them and will pass once fixed.
@pytest.mark.xfail(raises=EventSequenceError, strict=True)
def test_two_adjacent_missing_events():
    i = nth(32, 3)
    corrected(drop=(i, i + 1))  # tag and the following 44 in the same trial


@pytest.mark.xfail(raises=EventSequenceError, strict=True)
def test_recording_without_initial_spurious_trigger():
    raw = make_raw()
    raw._data[-1, :5] = 0
    events = check_baseline_tags(get_events_from_raw(raw, 1, 1))
    event_correction(events=events)
