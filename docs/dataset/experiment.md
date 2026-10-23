# The experiment

Each participant came for one recording day of about two hours, including 45 minutes
to place the cap and the external electrodes. The recording took place in an
electrically shielded room; the participant sat in front of a screen with a light-grey
background, and a stimulation program written in MATLAB with Psychtoolbox-3 showed the
cues and sent a trigger code to the EEG system at every step.

## A trial

Every trial lasts 4.5 s plus a short rest, and every trial looks the same on screen,
whatever the condition. Only the instruction given at the start of the run changes what
the participant does in the action interval.

<div class="is-figure" markdown>
<p class="is-figure__title">One trial, step by step</p>
<p class="is-figure__sub">What the participant saw in each interval, the trigger code that marks its start, and how the time axes of the paper and of the epoch files line up.</p>
<div data-viz="trial-timeline"><p>Concentration 0.5 s (code 42) → cue 0.5 s (31–34) → action 2.5 s (44) → relax 1 s (45) → rest 1.5–2 s (46).</p></div>
</div>

!!! tip "Two time axes"

    The paper and `innerspeech.data_processing.select_time_window` count time from the
    **start of the trial** (concentration interval, t = 0). The epoch files count it
    from the **cue** (`epochs.times` runs from −0.5 to 4.0 s). The action interval is
    therefore 1.0–3.5 s in trial time and 0.5–3.0 s in `epochs.times`.

## A session

Each participant did three sessions in a row, with a self-paced break between them.
Every session starts with a 15 s baseline, followed by five runs in a fixed order: one
pronounced speech, two inner speech and two visualized condition runs, separated by
one-minute breaks. The screen announced the condition for 3 s at the start of each run.

<div class="is-figure" markdown>
<p class="is-figure__title">One session</p>
<p class="is-figure__sub">A complete session has 200 trials (40 per run) and lasts about 27 minutes. Widths are proportional to time.</p>
<div data-viz="session-structure"><p>Baseline 15 s → run 1 pronounced → run 2 inner → run 3 inner → run 4 visualized → run 5 visualized, 40 trials each.</p></div>
</div>

The class of each trial was drawn at random, balanced within the session (50 trials per
class in a full session). The first two sessions of every participant have 200 trials.
In the third session some participants stopped earlier because of tiredness: sub-01,
sub-03 and sub-08 did 100 trials, sub-06 did 140. sub-03 also swapped the run types in
sessions 1 and 3, see [Notes](notes.md#per-session-exceptions).

### Attention control

To check that the participants kept attending, the inner speech and visualized runs
included control questions at random points: after a trial, the screen asked for the
direction of the last cue, and the participant answered with the arrow keys (no time
limit, with feedback). The questions and answers are in the recordings (codes 17 and
61–64), and the number of right and wrong answers is in every session's report. Mistakes
were rare (mean 0.5 per session).

## Recording setup

| Channel(s) | Placement | Purpose |
| --- | --- | --- |
| A1–D32 | BioSemi 128-channel head cap (radial A–D layout) | EEG |
| EXG1, EXG2 | left and right ear lobes | reference (no neural activity) |
| EXG3, EXG4 | left and right temples | horizontal eye movements (EOG) |
| EXG5, EXG6 | above and below the right eye | vertical eye movements and blinks (EOG) |
| EXG7, EXG8 | above and below the right side of the mouth (orbicularis oris) | mouth movements (EMG) |
| Status | | trigger codes sent by the stimulation computer |

The system recorded at 1024 Hz with 24-bit resolution and only a 208 Hz low-pass filter
in hardware; electrode impedances were checked before every session. BioSemi is a
reference-free system (CMS/DRL), so the data have to be re-referenced; the published
derivatives use the mean of the two ear lobes.

The stimulation program is in the repository under
[`Stimulation Protocol - MatLab/`](https://github.com/N-Nieto/Inner_Speech_Dataset/tree/main/Stimulation%20Protocol%20-%20MatLab)
(`Stimulation_protocol.m` is the main script), if you want to see exactly how the cues
were shown or to collect data with the same protocol.
