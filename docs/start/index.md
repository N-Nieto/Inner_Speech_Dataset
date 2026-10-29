# Get started

There are three ways to work with the dataset. Pick the one that matches what you need.

<div class="grid cards" markdown>

-   :material-play-circle-outline:{ .lg .middle } __Try it in the browser__

    ---

    The tutorial notebook runs in Google Colab: it installs the package, downloads
    one subject, plots the trials and trains a classifier. Nothing to install.

    [:octicons-arrow-right-24: Open in Colab](https://colab.research.google.com/github/N-Nieto/Inner_Speech_Dataset/blob/main/Database_exploration_tutorial.ipynb)

-   :material-rocket-launch-outline:{ .lg .middle } __Use the preprocessed trials__

    ---

    The usual route for analysis and decoding. Install the package, download the
    derivatives (all or part), and load trials with their labels.

    [:octicons-arrow-right-24: Install](install.md) →
    [Download](download.md) →
    [Load and analyse](load.md)

-   :material-tune-variant:{ .lg .middle } __Start from the raw recordings__

    ---

    For your own filters, time windows or artefact handling. Download the `.bdf`
    files and run the preprocessing script with your settings.

    [:octicons-arrow-right-24: Preprocessing](preprocessing.md)

</div>

## Folder layout

The scripts expect the dataset next to the repository, in a folder called `ds003626`.
The download functions put it there when you pass the parent folder of the repository.

```text
my_project/
├── Inner_Speech_Dataset/        ← this repository (git clone)
├── ds003626/                    ← the dataset (created by the download functions)
│   ├── sub-01/ … sub-10/        raw recordings
│   └── derivatives/             preprocessed trials
└── results/                     created by the analysis and check scripts
```

```bash
mkdir my_project && cd my_project
git clone https://github.com/N-Nieto/Inner_Speech_Dataset.git
cd Inner_Speech_Dataset
```
