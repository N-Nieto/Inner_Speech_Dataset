# Install

The shared code is a Python package, `innerspeech`, in `src/innerspeech`. Installing the
repository installs the package (in editable mode, so your changes are used right away)
together with its dependencies. Python 3.11 or newer is needed.

=== "uv (recommended)"

    [uv](https://docs.astral.sh/uv/) creates the environment with the exact versions
    pinned in `uv.lock`:

    ```bash
    uv sync --all-extras
    uv run python Python_Processing/InnerSpeech_preprocessing.py
    ```

    - `uv sync --extra download` or `--extra notebook` installs one extra only.
    - `uv sync -p 3.13` uses another Python version.
    - `uv sync` also installs the development tools (ruff, pytest); add `--no-dev` to
      skip them.

    `uv.lock` covers CPython on Linux (x86-64, aarch64), macOS and Windows (x64). On
    other platforms use pip.

=== "pip"

    Any virtual environment works, including conda:

    ```bash
    python -m venv .venv && source .venv/bin/activate
    # or: conda create -n inner_speech python=3.13 && conda activate inner_speech
    pip install -e ".[download,notebook]"
    ```

=== "Colab / no clone"

    Install the package straight from GitHub, e.g. in a notebook:

    ```bash
    pip install "inner-speech-dataset[download,notebook] @ git+https://github.com/N-Nieto/Inner_Speech_Dataset"
    ```

    The scripts in `Python_Processing/` and `checks/` are not included this way; clone
    the repository to use them.

## Optional extras

| Extra | Adds | Needed for |
| --- | --- | --- |
| `download` | `datalad`, `git-annex`, `tqdm` | Downloading from OpenNeuro (`innerspeech.download_helper`, the `*_download_tutorial.py` scripts) |
| `notebook` | `scikit-learn`, `ipykernel` | `Database_exploration_tutorial.ipynb` |

The core dependencies are MNE (≥ 1.7), NumPy, pandas, SciPy, Matplotlib, h5io and
joblib. The code is tested with Python 3.11–3.14, MNE 1.7–1.13, NumPy 1.26–2.5 and pandas
1.5–3.0.

!!! note "git-annex on older Linux"

    `git-annex` is installed from PyPI, which has wheels for Linux with glibc ≥ 2.34,
    macOS and Windows. On older Linux systems install it with
    `conda install -c conda-forge git-annex` or the system package manager. `git` itself
    must be installed too.

## Check the installation

```python
import innerspeech
from innerspeech.download_helper import list_versions

print(innerspeech.__version__)
print(list_versions())  # dataset versions on OpenNeuro, needs the download extra
```
