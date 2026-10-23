# The dataset

The Inner Speech Dataset (OpenNeuro [ds003626](https://openneuro.org/datasets/ds003626))
holds EEG recordings of ten participants who performed the same four commands in three
ways. It was designed for decoding inner speech in a brain-computer interface (BCI) and
for comparing it with speaking aloud and with visual imagery.

| | |
| --- | --- |
| **Participants** | 10 healthy, right-handed native Spanish speakers (4 female, 6 male), aged 24–56 |
| **Recording** | BioSemi ActiveTwo, 128 EEG + 8 external channels, 1024 Hz, 24 bit |
| **Design** | one day per participant, 3 sessions, each a 15 s baseline and 5 runs |
| **Conditions** | <span class="is-swatch pron"></span>pronounced speech · <span class="is-swatch inner"></span>inner speech · <span class="is-swatch vis"></span>visualized condition |
| **Classes** | *arriba* (up), *abajo* (down), *derecha* (right), *izquierda* (left), balanced in every session |
| **Trials** | 5,640: 1,128 pronounced, 2,236 inner speech, 2,276 visualized |
| **Format** | BIDS: raw `.bdf` recordings plus preprocessed MNE epochs (`.fif`) in `derivatives/` |
| **Size** | about 20 GB raw, 7 GB derivatives |
| **Licence** | CC0 (data), GPL-3.0 (code) |

## The three conditions

Pronounced speech
:   The participant says the word aloud, repeatedly, as if giving an order to the
    computer. These trials show what overt speech looks like in the EEG and in the
    mouth (EMG) channels.

Inner speech
:   The participant repeats the word with the inner voice, as if giving the order to
    the computer in their mind, without moving the lips or the tongue. This is the
    condition the dataset was built for.

Visualized condition
:   The participant mentally moves the circle on the screen in the direction of the
    cue. It shares the visual input and the direction with the other conditions but
    involves no speech, which makes it a control for what inner speech adds.

No rhythm was imposed in any condition, so each participant set their own pace.

## In this section

- [The experiment](experiment.md): the timing of a trial and of a session, interactively.
- [Event codes](events.md): every trigger in the recordings and how missing ones were restored.
- [Files and formats](files.md): what each file holds, its shape, and how to read it.
- [Sessions at a glance](sessions.md): trials, EMG control, answers and corrections of every session.
- [Notes and versions](notes.md): differences from the paper, known issues and the version history.
