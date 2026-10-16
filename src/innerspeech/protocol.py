"""
Description of the stimulation protocol, used to check and correct the events.

The protocol is data, not code: :class:`Protocol` lists the *roles* an event
can play (trial start, cue, answer, ...), the trigger codes of each role, which
role may follow which, and how far after the previous event a missing event is
placed when it has to be inserted. :func:`innerspeech.events_analysis.event_correction`
works for any protocol written this way; :data:`INNER_SPEECH` is the protocol
of this dataset (Nieto et al., 2022, Table 3 and ``Stimulation_protocol.m``).

Per-session exceptions of this dataset (a spurious trigger that needs another
event detection setting, a participant who performed a run in another
condition) are listed in :data:`KNOWN_ISSUES` instead of being coded as
special cases.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from functools import cached_property


@dataclass(frozen=True)
class Protocol:
    """
    Event structure of a recording session.

    Parameters
    ----------
    roles : dict of str to tuple of int
        Trigger codes of every role, e.g. ``{"cue": (31, 32, 33, 34)}``.
    transitions : dict of str to tuple of str
        Roles that may follow each role, in order of preference.
    first_role : str
        Role of the first event of a session.
    insert_offsets : dict of str to int
        Samples between the previous event and an inserted event of this role.
    default_offset : int
        Offset for roles missing from ``insert_offsets``.
    fill_codes : dict of str to int
        Code given to an inserted event of a role with several codes, when it
        cannot be inferred (the cue class is inferred, see ``cue_role``).
    run_start_role, run_type_role, run_order : str, str, tuple of int
        A missing run type is taken from ``run_order`` (codes of the runs of a
        session, in order).
    cue_role, trial_start_role, question_role, answer_role : str
        Roles used to build the trial table and the cognitive control check.
    answer_offset : int
        ``answer code - cue code`` for a correct answer.
    ignored_codes : tuple of int
        Codes removed before the correction (hardware artefacts).
    checks : dict
        Count checks of a corrected session: ``"once"`` (codes present exactly
        once), ``"equal_counts"`` (groups of codes with equal counts) and
        ``"runs"`` (run start, run end and between-run codes: starts = ends =
        between + 1).
    condition_codes : dict of int to int
        Run type code to condition number used in the trial table.
    """

    roles: dict[str, tuple[int, ...]]
    transitions: dict[str, tuple[str, ...]]
    first_role: str
    insert_offsets: dict[str, int]
    default_offset: int
    fill_codes: dict[str, int]
    run_start_role: str
    run_type_role: str
    run_order: tuple[int, ...]
    cue_role: str
    trial_start_role: str
    question_role: str
    answer_role: str
    answer_offset: int
    ignored_codes: tuple[int, ...] = ()
    checks: dict = field(default_factory=dict)
    condition_codes: dict[int, int] = field(default_factory=dict)

    @cached_property
    def role_of_code(self) -> dict[int, str]:
        """Role of every trigger code."""
        return {code: role for role, codes in self.roles.items() for code in codes}

    @cached_property
    def shortest_paths(self) -> dict[str, dict[str, tuple[str, ...]]]:
        """``paths[a][b]``: roles after ``a`` up to and including ``b``.

        Breadth-first search in the order of ``transitions``, so ties are
        resolved by the order in which the successors are listed.
        """
        paths = {}
        for start in self.roles:
            found = {}
            queue = deque([(start, ())])
            while queue:
                role, path = queue.popleft()
                for nxt in self.transitions.get(role, ()):
                    if nxt not in found:
                        found[nxt] = (*path, nxt)
                        queue.append((nxt, found[nxt]))
            paths[start] = found
        return paths

    def offset(self, role: str) -> int:
        """Samples between the previous event and an inserted ``role`` event."""
        return self.insert_offsets.get(role, self.default_offset)


# Insertion offsets of the original correction (samples at 1024 Hz after the
# previous event), kept so that the published derivatives are reproduced.
INNER_SPEECH = Protocol(
    roles={
        "protocol_start": (11,),
        "baseline_start": (13,),
        "baseline_end": (14,),
        "run_start": (15,),
        "run_type": (21, 22, 23),
        "trial_start": (42,),
        "cue": (31, 32, 33, 34),
        "action": (44,),
        "relax": (45,),
        "rest": (46,),
        "question": (17,),
        "answer": (61, 62, 63, 64),
        "run_end": (16,),
        "inter_run": (51,),
        "protocol_end": (12,),
    },
    transitions={
        "protocol_start": ("baseline_start",),
        "baseline_start": ("baseline_end",),
        "baseline_end": ("run_start",),
        "run_start": ("run_type",),
        "run_type": ("trial_start",),
        "trial_start": ("cue",),
        "cue": ("action",),
        "action": ("relax",),
        "relax": ("rest",),
        "rest": ("trial_start", "question", "run_end"),
        "question": ("answer",),
        "answer": ("trial_start", "run_end"),
        "run_end": ("inter_run", "protocol_end"),
        "inter_run": ("run_start",),
        "protocol_end": (),
    },
    first_role="protocol_start",
    insert_offsets={
        "baseline_end": 15 * 1024,  # 15 s baseline
        "trial_start": 1945,
        "cue": 563,
        "action": 2594,
        "relax": 1075,
        "rest": 1075,
        "question": 2092,
        "answer": 2092,
    },
    default_offset=563,
    fill_codes={"answer": 61},
    run_start_role="run_start",
    run_type_role="run_type",
    run_order=(21, 22, 22, 23, 23),  # pronounced, inner x2, visualized x2
    cue_role="cue",
    trial_start_role="trial_start",
    question_role="question",
    answer_role="answer",
    answer_offset=30,
    ignored_codes=(65536,),  # BioSemi trigger overflow
    checks={
        "once": (11, 13),
        "equal_counts": ((31, 32, 33, 34), (42, 44, 45, 46)),
        "runs": (15, 16, 51),
        "questions": (17, (61, 62, 63, 64)),
    },
    condition_codes={21: 0, 22: 1, 23: 2},
)

# Per-session exceptions of this dataset, keyed by (subject, session)
KNOWN_ISSUES: dict[tuple[int, int], dict] = {
    (10, 1): {
        "note": "A spurious trigger overlaps the baseline end; events shorter than "
        "2 ms are ignored, which also drops the baseline end (it is re-inserted).",
        "find_events": {"min_duration": 0.002},
    },
    (3, 1): {
        "note": "The participant performed the second inner speech run (trials "
        "80-119) as visualized condition.",
        "relabel_condition": {"trials": (80, 120), "condition": 2},
    },
}
