---
title: Home
hide:
  - navigation
  - toc
---

<div class="is-hero" markdown>
<div markdown>

# Thinking out loud: an open EEG dataset for inner speech

<p class="is-hero__lead">Ten Spanish speakers thought, said and imagined the words
<em>arriba, abajo, derecha, izquierda</em> (up, down, right, left) while a 128-channel
EEG recorded their brain activity. The recordings, the preprocessed trials and the
code that made them are open, so you can decode inner speech, study how it differs
from speaking aloud, or build your own pipeline.</p>

[Get started](start/index.md){ .md-button .md-button--primary }
[Data on OpenNeuro](https://openneuro.org/datasets/ds003626){ .md-button }
[Read the paper](https://doi.org/10.1038/s41597-022-01147-2){ .md-button }

</div>
<div class="is-stimuli" aria-label="The four visual cues">
  <figure><svg viewBox="0 0 80 60" aria-hidden="true"><path d="M40 14 54 42H26Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><circle cx="40" cy="33" r="2" fill="#fff"/></svg><figcaption>arriba · up</figcaption></figure>
  <figure><svg viewBox="0 0 80 60" aria-hidden="true"><path d="M40 46 54 18H26Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><circle cx="40" cy="27" r="2" fill="#fff"/></svg><figcaption>abajo · down</figcaption></figure>
  <figure><svg viewBox="0 0 80 60" aria-hidden="true"><path d="M26 30 54 16V44Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><circle cx="45" cy="30" r="2" fill="#fff"/></svg><figcaption>izquierda · left</figcaption></figure>
  <figure><svg viewBox="0 0 80 60" aria-hidden="true"><path d="M54 30 26 16V44Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><circle cx="35" cy="30" r="2" fill="#fff"/></svg><figcaption>derecha · right</figcaption></figure>
</div>
</div>

<div class="is-stats">
  <div class="is-stat"><b>10</b><span>participants, one recording day each</span></div>
  <div class="is-stat"><b>30</b><span>sessions (three per participant)</span></div>
  <div class="is-stat"><b>5,640</b><span>trials</span></div>
  <div class="is-stat"><b>3</b><span>conditions: pronounced, inner, visualized</span></div>
  <div class="is-stat"><b>4</b><span>classes: up, down, right, left</span></div>
  <div class="is-stat"><b>128 + 8</b><span>EEG + external channels at 1024 Hz</span></div>
</div>

## Find your way

<div class="grid cards" markdown>

-   :material-brain:{ .lg .middle } __Understand the experiment__

    ---

    What the participants saw and did in every trial, how a session is organised,
    and what the three conditions are.

    [:octicons-arrow-right-24: The experiment](dataset/experiment.md)

-   :material-file-tree:{ .lg .middle } __Know the files__

    ---

    The raw BioSemi recordings, the preprocessed epochs, the trial tables and
    reports: what each file holds and how to read it.

    [:octicons-arrow-right-24: Files and formats](dataset/files.md)

-   :material-download:{ .lg .middle } __Get the data__

    ---

    Install the package and download all of the dataset, or only the subjects,
    sessions and file types you need.

    [:octicons-arrow-right-24: Install and download](start/install.md)

-   :material-chart-timeline-variant:{ .lg .middle } __Analyse it__

    ---

    Load trials as NumPy arrays or MNE Epochs, pick conditions and classes, and
    train a first classifier.

    [:octicons-arrow-right-24: Load and analyse](start/load.md)

-   :material-cog-outline:{ .lg .middle } __Reprocess from raw__

    ---

    The preprocessing pipeline step by step, with every setting you can change to
    make your own derivatives.

    [:octicons-arrow-right-24: Preprocessing](start/preprocessing.md)

-   :material-table-eye:{ .lg .middle } __Check each session__

    ---

    Trials, EMG-tagged trials, control answers and event corrections of all 30
    sessions, with the known issues.

    [:octicons-arrow-right-24: Sessions at a glance](dataset/sessions.md)

</div>

## Your first trials

```python
from pathlib import Path

from innerspeech.download_helper import get_derivatives
from innerspeech.data_extractions import extract_condition_epochs

get_derivatives(Path.cwd(), subjects="01", file_types=["eeg", "events"])  # (1)!
epochs = extract_condition_epochs(Path.cwd() / "ds003626", [1], condition="inner")
epochs.average().plot()  # the inner speech trials of sub-01, as MNE Epochs
```

1.  Downloads the preprocessed EEG and trial tables of sub-01 (three sessions,
    about 600 MB) into `./ds003626/derivatives`.

New to the code? Start with the [installation](start/install.md) or open the
tutorial notebook in Colab, no installation needed:
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/N-Nieto/Inner_Speech_Dataset/blob/main/Database_exploration_tutorial.ipynb)

## Cite

If you use the dataset, please cite the paper:

> Nieto, N., Peterson, V., Rufiner, H. L., Kamienkowski, J. E., & Spies, R. (2022).
> Thinking out loud, an open-access EEG-based BCI dataset for inner speech recognition.
> *Scientific Data*, 9, 52. <https://doi.org/10.1038/s41597-022-01147-2>

BibTeX entries are on the [Cite](cite.md) page.
