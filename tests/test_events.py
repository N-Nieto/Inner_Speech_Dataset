"""Event extraction, correction and the trial table on synthetic recordings."""

import numpy as np
import pandas as pd
import pytest

from innerspeech.data_extractions import get_events_from_raw
from innerspeech.events_analysis import (
    cognitive_control_check,
    event_correction,
    mne_events,
    process_session_events,
    trial_table,
)
from innerspeech.exceptions import EventSequenceError
from synthetic import make_event_sequence, make_raw

TAGS, MARKS = (31, 32, 33, 34), (42, 44, 45, 46)


def frame(events, initial_spurious=True):
    """Events of make_event_sequence as get_events_from_raw returns them."""
    rows = [(s, 0, c) for s, c in events]
    if initial_spurious:
        rows.insert(0, (0, 0, 65536))
    return pd.DataFrame(rows, columns=["Time", "Trigger", "Code"])


def corrected(initial_spurious=True, **kw):
    events, _ = make_event_sequence(**kw)
    return event_correction(frame(events, initial_spurious))


def counts(events, codes):
    values = events["Code"].to_numpy()
    return [int((values == c).sum()) for c in codes]


def nth(code, n, **kw):
    """Index of the n-th event with ``code`` in the synthetic sequence."""
    events, _ = make_event_sequence(**kw)
    return [i for i, (_, c) in enumerate(events) if c == code][n]


def actions(events):
    return [c["action"] for c in events.attrs["corrections"]]


def test_clean_recording():
    events = get_events_from_raw(make_raw(), 1, 1)
    events = event_correction(events)
    assert counts(events, TAGS) == [50] * 4
    assert counts(events, MARKS) == [200] * 4
    assert 65536 not in events["Code"].to_numpy()
    assert not events["inferred"].any()
    assert actions(events) == ["ignored"]  # the initial 65536 trigger
    assert cognitive_control_check(events) == (20, 0)
    assert mne_events(events).shape == (len(events), 3)


def test_missing_cue_gets_the_missing_class():
    full, _ = make_event_sequence()
    i = nth(32, 5)
    events = corrected(drop=(i,))
    assert counts(events, TAGS) == [50] * 4
    inserted = events[events["inferred"]]
    assert inserted["Code"].tolist() == [32]
    assert full[i - 1][0] < inserted["Time"].iloc[0] < full[i + 1][0]
    (item,) = [c for c in events.attrs["corrections"] if c["action"] == "inserted"]
    assert item["code"] == 32 and "cue" in item["reason"]
    trials = trial_table(events, session=1)
    assert trials["cue_inferred"].sum() == 1


def test_several_missing_cues_use_each_runs_balance():
    full, _ = make_event_sequence()
    drop = (nth(31, 3), nth(34, 7), nth(33, 35))  # runs 1, 1 and 4
    events = corrected(drop=drop)
    assert counts(events, TAGS) == [50] * 4
    inserted = events.loc[events["inferred"], "Code"].tolist()
    assert inserted == [full[i][1] for i in sorted(drop)]


@pytest.mark.parametrize("code", [44, 45, 46, 42])
def test_missing_mark_is_inserted_between_its_neighbours(code):
    full, _ = make_event_sequence()
    i = nth(code, 10)
    events = corrected(drop=(i,))
    assert counts(events, MARKS) == [200] * 4
    time = events.loc[events["inferred"], "Time"].iloc[0]
    assert full[i - 1][0] < time < full[i + 1][0]


def test_adjacent_missing_events_and_spurious_triggers():
    i = nth(32, 3)
    events = corrected(drop=(i, i + 1, nth(46, 30)), spurious=(500_000, 700_123))
    assert counts(events, TAGS) == [50] * 4
    assert counts(events, MARKS) == [200] * 4
    assert 65536 not in events["Code"].to_numpy()
    assert actions(events).count("inserted") == 3


def test_recording_without_initial_spurious_trigger():
    events = corrected(initial_spurious=False)
    assert events.attrs["corrections"] == []
    assert counts(events, TAGS) == [50] * 4


def test_duplicated_and_unknown_codes_are_removed():
    full, _ = make_event_sequence()
    i = nth(44, 20)
    extra = [(full[i][0] + 3, 44), (full[i][0] + 400, 99)]
    events = event_correction(frame(sorted(full + extra)))
    assert counts(events, MARKS) == [200] * 4
    assert 99 not in events["Code"].to_numpy()
    assert sorted(actions(events)) == ["dropped", "ignored", "ignored"]


def test_missing_run_type_is_taken_from_the_run_order():
    """The condition of the run's trials must not change (40 trials)."""
    events = corrected(drop=(nth(22, 1),))  # second inner speech run
    trials = trial_table(events, session=1)
    assert np.bincount(trials["condition"]).tolist() == [40, 80, 80]
    assert (trials["condition"][80:120] == 1).all()


def test_unrecoverable_session_raises():
    with pytest.raises(EventSequenceError):
        corrected(drop=(nth(11, 0),))  # protocol start, before every event


def test_trial_table():
    trials = trial_table(corrected(), session=2)
    assert list(trials.columns) == [
        "sample",
        "class",
        "condition",
        "session",
        "cue_inferred",
    ]
    assert len(trials) == 200
    assert np.bincount(trials["class"]).tolist() == [50] * 4
    assert np.bincount(trials["condition"]).tolist() == [40, 80, 80]
    assert (trials["session"] == 2).all()
    assert (np.diff(trials["sample"]) > 0).all()


def test_wrong_and_missing_answers():
    full, _ = make_event_sequence()
    answers = [i for i, (_, c) in enumerate(full) if 61 <= c <= 64]
    first = full[answers[0]]
    full[answers[0]] = (first[0], 61 if first[1] != 61 else 62)  # wrong answer
    events = event_correction(frame(full))
    assert cognitive_control_check(events) == (19, 1)


def test_known_issues_are_applied():
    raw = make_raw()
    # A one-sample glitch is found by default and ignored as an unknown code
    raw._data[-1, 100_000] = 99
    assert 99 in get_events_from_raw(raw, 1, 1)["Code"].to_numpy()
    issues = {
        (1, 1): {
            "note": "test",
            "find_events": {"min_duration": 0.002},
            "relabel_condition": {"trials": (80, 120), "condition": 2},
        }
    }
    assert 99 not in get_events_from_raw(raw, 1, 1, issues)["Code"].to_numpy()
    _, trials, report = process_session_events(raw, 1, 1, known_issues=issues)
    assert np.bincount(trials["condition"]).tolist() == [40, 40, 120]
    assert report["Known_issue"] == "test"
    assert (report["Ans_R"], report["Ans_W"]) == (20, 0)
    assert report["Recording_time"] == round(raw.last_samp / 1024)
