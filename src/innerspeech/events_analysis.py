"""
Check and correct the events of a session, and derive the trial table.

The correction compares the recorded trigger sequence with the sequence the
stimulation protocol allows (:mod:`innerspeech.protocol`). Every recorded event
is either accepted, or dropped as out of sequence; missing events are inserted
where the protocol requires them. The combination with the fewest changes is
found for the whole session at once (dynamic programming), so several missing
events in a row, extra triggers and recordings with or without the initial
spurious trigger are handled the same way.

Typical use (``process_session_events`` runs these steps, with the
per-session exceptions of :data:`innerspeech.protocol.KNOWN_ISSUES`)::

    events = get_events_from_raw(raw, n_s, n_b)  # Time, Trigger, Code
    events = event_correction(events)  # + "inferred" column
    right, wrong = cognitive_control_check(events)
    trials = trial_table(events, session=n_b, condition_override=...)

``event_correction`` lists what it changed in ``events.attrs["corrections"]``.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from innerspeech.exceptions import EventSequenceError
from innerspeech.protocol import INNER_SPEECH, KNOWN_ISSUES, Protocol

logger = logging.getLogger(__name__)

EVENT_COLUMNS = ["Time", "Trigger", "Code"]
_START = "<start>"


# ----------------------------------------------------------------------------
# Whole session
# ----------------------------------------------------------------------------
def process_session_events(
    raw,
    n_s: int,
    n_b: int,
    protocol: Protocol = INNER_SPEECH,
    known_issues: dict | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Events, trial table and event-derived report fields of one recording.

    Reads the triggers of ``raw``, corrects them, counts the answers to the
    cognitive control questions and builds the trial table, applying the
    exceptions listed for the session in ``known_issues``.

    Parameters
    ----------
    raw : mne.io.BaseRaw
        Raw recording with its Status (stim) channel.
    n_s, n_b : int
        Subject and session numbers.
    protocol : Protocol
        Event structure (default: this dataset).
    known_issues : dict, optional
        Per-session exceptions keyed by ``(n_s, n_b)``; default
        :data:`innerspeech.protocol.KNOWN_ISSUES`.

    Returns
    -------
    events : pandas.DataFrame
        Corrected events (see :func:`event_correction`); ``mne_events(events)``
        gives the array to epoch with.
    trials : pandas.DataFrame
        Trial table (see :func:`trial_table`).
    report : dict
        ``Recording_time`` (s), ``Ans_R``, ``Ans_W``, ``Event_corrections``
        and, for sessions with a known issue, ``Known_issue``.
    """
    from innerspeech.data_extractions import get_events_from_raw

    issues = KNOWN_ISSUES if known_issues is None else known_issues
    issue = issues.get((n_s, n_b), {})
    events = event_correction(
        get_events_from_raw(raw, n_s, n_b, known_issues=issues), protocol
    )
    right, wrong = cognitive_control_check(events, protocol)
    trials = trial_table(events, n_b, protocol, issue.get("relabel_condition"))
    report = {
        "Recording_time": int(np.round(raw.last_samp / raw.info["sfreq"])),
        "Ans_R": right,
        "Ans_W": wrong,
        "Event_corrections": events.attrs["corrections"],
    }
    if "note" in issue:
        report["Known_issue"] = issue["note"]
    return events, trials, report


# ----------------------------------------------------------------------------
# Correction
# ----------------------------------------------------------------------------
def event_correction(
    events: pd.DataFrame,
    protocol: Protocol = INNER_SPEECH,
    insert_cost: float = 1.0,
    drop_cost: float = 2.5,
    validate: bool = True,
) -> pd.DataFrame:
    """
    Correct the event sequence of one session against the protocol.

    Parameters
    ----------
    events : pandas.DataFrame
        Events as returned by ``get_events_from_raw``: columns ``Time``
        (sample), ``Trigger`` (previous Status value) and ``Code``.
    protocol : Protocol
        Event structure of the session (default: this dataset).
    insert_cost, drop_cost : float
        Cost of inserting a missing event and of dropping a recorded one. With
        the defaults, up to two missing events are inserted before a recorded
        event is considered out of sequence.
    validate : bool
        Check the event counts of the corrected session (``protocol.checks``).

    Returns
    -------
    pandas.DataFrame
        Corrected events sorted by time, with the columns of the input and a
        boolean ``inferred`` column (True for inserted events).
        ``attrs["corrections"]`` lists every inserted, dropped, ignored and
        missing event as dicts with ``sample``, ``code``, ``action`` and
        ``reason``.

    Raises
    ------
    EventSequenceError
        If ``validate`` is True and the corrected counts are inconsistent.
    """
    corrections: list[dict] = []
    observed = []
    for time, trigger, code in events[EVENT_COLUMNS].itertuples(index=False):
        code = int(code)
        if code in protocol.ignored_codes or code not in protocol.role_of_code:
            reason = (
                "hardware artefact"
                if code in protocol.ignored_codes
                else "unknown code"
            )
            corrections.append(_log(time, code, "ignored", reason))
            continue
        observed.append((int(time), int(trigger), code, protocol.role_of_code[code]))

    steps = _align(observed, protocol, insert_cost, drop_cost)
    rows, inserted_cues = _build_rows(observed, steps, protocol, corrections)
    _infer_cue_classes(rows, inserted_cues, observed, protocol, corrections)

    corrected = pd.DataFrame(rows, columns=[*EVENT_COLUMNS, "inferred"])
    corrected = corrected.sort_values("Time", kind="stable").reset_index(drop=True)
    corrected.attrs["corrections"] = corrections
    for item in corrections:
        logger.info(
            "%s %s at sample %s (%s)",
            item["action"],
            item["code"],
            item["sample"],
            item["reason"],
        )
    if validate:
        validate_counts(corrected, protocol)
    return corrected


def _log(sample, code, action: str, reason: str) -> dict:
    return {
        "sample": int(sample),
        "code": None if code is None else int(code),
        "action": action,
        "reason": reason,
    }


def _path(protocol: Protocol, state: str, role: str) -> tuple[str, ...] | None:
    """Roles after ``state`` up to and including ``role``, or None."""
    if state == _START:
        if role == protocol.first_role:
            return (role,)
        rest = protocol.shortest_paths[protocol.first_role].get(role)
        return None if rest is None else (protocol.first_role, *rest)
    return protocol.shortest_paths[state].get(role)


def _align(observed, protocol, insert_cost, drop_cost) -> list[tuple]:
    """Fewest-changes alignment of the recorded events with the protocol.

    ``cost[j, s]`` is the lowest cost of explaining the first ``j`` events
    with ``s`` as the role of the last kept event. Returns one step per
    recorded event: ``("keep", previous_state, path)`` or ``("drop", state)``.
    """
    states = [_START, *protocol.roles]
    index = {s: i for i, s in enumerate(states)}
    n = len(observed)
    cost = np.full((n + 1, len(states)), np.inf)
    back: list[dict[int, tuple]] = [{} for _ in range(n + 1)]
    cost[0, index[_START]] = 0.0
    for j, (_, _, _, role) in enumerate(observed):
        target = index[role]
        for s in np.flatnonzero(np.isfinite(cost[j])):
            base = cost[j, s]
            path = _path(protocol, states[s], role)
            if path is not None:  # keep, inserting the missing roles before it
                c = base + insert_cost * (len(path) - 1)
                if c < cost[j + 1, target]:
                    cost[j + 1, target] = c
                    back[j + 1][target] = ("keep", s, path)
            c = base + drop_cost  # drop as out of sequence
            if c < cost[j + 1, s]:
                cost[j + 1, s] = c
                back[j + 1][s] = ("drop", s)
    state = int(np.argmin(cost[n]))
    steps = []
    for j in range(n, 0, -1):
        step = back[j][state]
        steps.append(step)
        state = step[1]
    return [(step[0], states[step[1]], *step[2:]) for step in steps[::-1]]


def _build_rows(observed, steps, protocol, corrections):
    rows, inserted_cues = [], []
    previous_time = None
    run_index = -1
    for (time, trigger, code, role), step in zip(observed, steps, strict=True):
        if step[0] == "drop":
            corrections.append(_log(time, code, "dropped", "out of sequence"))
            continue
        path = step[2]
        for missing in path[:-1]:
            if missing == protocol.run_start_role:
                run_index += 1
            if previous_time is None:  # before the first recorded event
                corrections.append(
                    _log(
                        time,
                        None,
                        "missing",
                        f"{missing} before the first recorded event, not inserted",
                    )
                )
                continue
            previous_time += protocol.offset(missing)
            fill = _fill_code(protocol, missing, run_index)
            if missing == protocol.cue_role:
                inserted_cues.append(len(rows))
            rows.append([previous_time, 0, fill, True])
            corrections.append(
                _log(previous_time, fill, "inserted", f"missing {missing}")
            )
        if role == protocol.run_start_role:
            run_index += 1
        rows.append([time, trigger, code, False])
        previous_time = time
    return rows, inserted_cues


def _fill_code(protocol: Protocol, role: str, run_index: int) -> int | None:
    codes = protocol.roles[role]
    if len(codes) == 1:
        return codes[0]
    if role == protocol.run_type_role and 0 <= run_index < len(protocol.run_order):
        return protocol.run_order[run_index]
    if role == protocol.cue_role:
        return None  # inferred afterwards
    return protocol.fill_codes.get(role, codes[0])


def _infer_cue_classes(rows, inserted, observed, protocol, corrections) -> None:
    """Class of the inserted cues.

    One missing cue in the session: the class recorded least often in the
    session (the rule of the original correction). Several: within each run,
    the classes with fewer cues than the others, since every run presents the
    classes equally often.
    """
    if not inserted:
        return
    cue_codes = protocol.roles[protocol.cue_role]
    if len(inserted) == 1:
        recorded = [code for _, _, code, _ in observed]
        counts = [recorded.count(c) for c in cue_codes]
        _set_cue(
            rows,
            inserted[0],
            cue_codes[int(np.argmin(counts))],
            corrections,
            "class recorded least often in the session",
        )
        return
    run_starts = set(protocol.roles[protocol.run_start_role])
    run, runs = -1, []
    for row in rows:
        run += row[2] in run_starts
        runs.append(run)
    for r in sorted({runs[i] for i in inserted}):
        in_run = [row[2] for row, rr in zip(rows, runs, strict=True) if rr == r]
        counts = np.array([in_run.count(c) for c in cue_codes])
        deficit = counts.max() - counts
        for i in (i for i in inserted if runs[i] == r):
            reason = "class missing from the run's balance"
            if deficit.sum() == 0:
                deficit = counts.max() + 1 - counts
                reason = "class ambiguous, the run's least frequent class used"
            k = int(np.argmax(deficit > 0))
            deficit[k] -= 1
            counts[k] += 1
            _set_cue(rows, i, cue_codes[k], corrections, reason)


def _set_cue(rows, i, code, corrections, reason) -> None:
    rows[i][2] = code
    for item in corrections:
        if (
            item["action"] == "inserted"
            and item["code"] is None
            and item["sample"] == rows[i][0]
        ):
            item["code"] = int(code)
            item["reason"] += f" ({reason})"
            break


def validate_counts(events: pd.DataFrame, protocol: Protocol = INNER_SPEECH) -> None:
    """
    Check the event counts of a corrected session (``protocol.checks``).

    Raises
    ------
    EventSequenceError
        Describing the first check that fails.
    """
    codes = events["Code"].to_numpy(dtype=int)

    def count(code: int) -> int:
        return int((codes == code).sum())

    checks = protocol.checks
    for code in checks.get("once", ()):
        if count(code) != 1:
            raise EventSequenceError(
                f"Code {code} found {count(code)} times, expected 1"
            )
    if "runs" in checks:
        start, end, between = (count(c) for c in checks["runs"])
        if not start == end == between + 1:
            raise EventSequenceError(
                f"Inconsistent runs: {start} starts, {end} ends, {between} breaks"
            )
    for group in checks.get("equal_counts", ()):
        counts = [count(c) for c in group]
        if len(set(counts)) > 1:
            raise EventSequenceError(f"Unequal counts of codes {group}: {counts}")
    if "questions" in checks:
        question, answers = checks["questions"]
        if count(question) != sum(count(c) for c in answers):
            raise EventSequenceError("Questions and answers do not match")


# ----------------------------------------------------------------------------
# Derived information
# ----------------------------------------------------------------------------
def cognitive_control_check(
    events: pd.DataFrame, protocol: Protocol = INNER_SPEECH
) -> tuple[int, int]:
    """
    Count right and wrong answers to the cognitive control questions.

    An answer is right when it names the class of the last cue before the
    question. A question without an answer counts as wrong.

    Returns
    -------
    tuple of int
        ``(right, wrong)``.
    """
    cues = set(protocol.roles[protocol.cue_role])
    questions = set(protocol.roles[protocol.question_role])
    answers = set(protocol.roles[protocol.answer_role])
    codes = events["Code"].to_numpy(dtype=int)
    right = wrong = 0
    last_cue = None
    for i, code in enumerate(codes):
        if code in cues:
            last_cue = int(code)
        elif code in questions:
            answer = int(codes[i + 1]) if i + 1 < len(codes) else None
            if (
                answer in answers
                and last_cue is not None
                and answer == last_cue + protocol.answer_offset
            ):
                right += 1
            else:
                wrong += 1
    return right, wrong


def trial_table(
    events: pd.DataFrame,
    session: int,
    protocol: Protocol = INNER_SPEECH,
    condition_override: dict | None = None,
) -> pd.DataFrame:
    """
    One row per trial (cue event) of a corrected session.

    Parameters
    ----------
    events : pandas.DataFrame
        Output of :func:`event_correction`.
    session : int
        Session number, stored in every row.
    protocol : Protocol
        Event structure (default: this dataset).
    condition_override : dict, optional
        ``{"trials": (first, stop), "condition": c}`` sets the condition of
        trials ``first`` to ``stop - 1`` (see ``protocol.KNOWN_ISSUES``).

    Returns
    -------
    pandas.DataFrame
        Columns ``sample`` (sample of the raw 1024 Hz recording), ``class``
        (0 = up, 1 = down, 2 = right, 3 = left), ``condition`` (0 = pronounced,
        1 = inner, 2 = visualized), ``session`` and ``cue_inferred``.
    """
    cue_codes = protocol.roles[protocol.cue_role]
    run_types = set(protocol.roles[protocol.run_type_role])
    inferred = events["inferred"] if "inferred" in events else [False] * len(events)
    condition = 0
    rows = []
    for time, code, was_inferred in zip(
        events["Time"], events["Code"], inferred, strict=True
    ):
        code = int(code)
        if code in run_types:
            condition = protocol.condition_codes[code]
        elif code in cue_codes:
            rows.append(
                (
                    int(time),
                    cue_codes.index(code),
                    condition,
                    session,
                    bool(was_inferred),
                )
            )
    table = pd.DataFrame(
        rows, columns=["sample", "class", "condition", "session", "cue_inferred"]
    )
    if condition_override:
        first, stop = condition_override["trials"]
        table.loc[first : stop - 1, "condition"] = condition_override["condition"]
    return table


def mne_events(events: pd.DataFrame) -> np.ndarray:
    """Events as the ``(n, 3)`` integer array MNE expects."""
    return events[EVENT_COLUMNS].to_numpy(dtype=int)
