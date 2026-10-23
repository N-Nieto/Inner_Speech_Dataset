# Sessions at a glance

Every session has its own trial table and report in `derivatives/`. This page puts the
main numbers of all 30 side by side, so you can see where a session is shorter, where the
EMG control tagged many trials, or which triggers had to be restored. Choose a value,
then click a session for its details.

<div class="is-figure" markdown>
<div data-viz="sessions" data-src="../../assets/data/sessions.json"><p>The interactive overview needs JavaScript. The numbers are in the table below.</p></div>
</div>

## Reading the numbers

Trials
:   200 in a complete session: 40 pronounced speech, 80 inner speech and 80 visualized,
    50 per class. Four third sessions are shorter (100 or 140 trials), and sub-03 has a
    different split in sessions 1 and 3 ([why](notes.md#per-session-exceptions)).

EMG-tagged
:   Inner speech or visualized trials in which the mouth channels (EXG7, EXG8) exceeded
    the baseline by more than 3 standard deviations, i.e. the participant probably
    moved the mouth. 115 of the 4,512 inspected trials (2.5 %) are tagged, mostly in
    sub-02 session 1 and sub-06, sub-09. The trials are kept in the data; use the
    `emg_tagged` column of `events.tsv` to leave them out.

Event corrections
:   Triggers missing from the recording and restored by the
    [event correction](events.md#missing-triggers-and-how-they-are-restored). A
    restored cue means the trial's class was inferred (`cue_inferred` in `events.tsv`).

Control answers
:   Right and wrong answers to the attention questions. sub-01 answered many more
    questions in session 1; the number was reduced for everyone after that.

## Table

The figure and this table are built from the derivatives by
`docs/scripts/session_stats.py`. *Inserted events* counts the triggers restored by the
event correction; it is n/a for sessions whose files are still in the format of version
2.1.2.

--8<-- "sessions_table.md"
