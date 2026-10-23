# Development

Contributions and bug reports are welcome on
[GitHub](https://github.com/N-Nieto/Inner_Speech_Dataset/issues).

## Set up

```bash
git clone https://github.com/N-Nieto/Inner_Speech_Dataset.git
cd Inner_Speech_Dataset
uv sync --all-extras          # package, extras and development tools
```

## Tests

```bash
uv run pytest
```

The tests run on **synthetic data** (`tests/synthetic.py`): small recordings and
derivatives that follow the protocol, with triggers removed or added on purpose. They
cover the event correction, the readers and writers of the derivatives, the
preprocessing script end to end (without ICA), the EMG control, the BIDS sidecars and the
check scripts, and take about 20 s. No download is needed.

The same tests run on GitHub for the oldest and newest supported Python (3.11 and 3.14)
on every push and pull request, together with the linters.

## Code style

```bash
uv run ruff check .           # lint
uv run ruff format .          # format
uv run codespell              # spelling
```

Docstrings follow the [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html)
format; the [API reference](index.md#the-package) of this site is generated from them.

## This website

The site is built with [MkDocs](https://www.mkdocs.org/) and the
[Material](https://squidfunk.github.io/mkdocs-material/) theme from the Markdown files in
`docs/` and the docstrings of the package. A GitHub Action publishes it to GitHub Pages
on every push to `main`.

```bash
uv sync --group docs
uv run mkdocs serve           # live preview at http://127.0.0.1:8000
uv run mkdocs build --strict  # what the Action runs
```

The interactive figures are drawn by `docs/javascripts/innerspeech.js` (no external
libraries). The per-session numbers on [Sessions at a glance](../dataset/sessions.md)
come from `docs/assets/data/sessions.json` and `docs/snippets/sessions_table.md`; rebuild
both after the derivatives change:

```bash
uv run python docs/scripts/session_stats.py --derivatives ../ds003626/derivatives
```

## Repository scripts

| Folder | Scripts |
| --- | --- |
| `checks/` | `verify_dataset.py`, `reproduce_session.py`, `session_noise.py`: see [Check your copy](../start/checks.md) |
| `bids/` | `make_bids_sidecars.py` writes the BIDS sidecar files; `convert_derivatives.py` adds `events.tsv` and `report.json` to the published derivatives after checking that the current code reproduces them |

Run them with `python <script>` from the repository folder.
