# Mutation Testing

How to run the mutation tests and the added unit tests. Works on Windows, macOS, and Linux.

## Prerequisites

- Python 3.10 or newer (the recorded run used Python 3.13)
- Run all commands from the repository root
- Install the package, cosmic-ray, and pytest (cosmic-ray runs the tests through pytest):

Windows (PowerShell):

```powershell
python -m pip install -e ".[i18n]"
python -m pip install cosmic-ray==8.7.0 pytest
```

macOS / Linux:

```sh
python3 -m pip install -e ".[i18n]"
python3 -m pip install cosmic-ray==8.7.0 pytest
```

## Setup

- Tool: [cosmic-ray](https://github.com/sixty-north/cosmic-ray) 8.7.0
- Added tests: `courseProjectCode/mutation-testing/mutation_*_tests.py`
- No existing MkDocs file was changed.
- Configuration: one file per team member in `courseProjectCode/mutation-testing/config/`. Each config's `test-command` runs the existing MkDocs tests for that file plus the new test file for it.

| Config | File under test |
|---|---|
| `gh_deploy.toml` | `mkdocs/commands/gh_deploy.py` |
| `meta.toml` | `mkdocs/utils/meta.py` |
| `toc.toml` | `mkdocs/structure/toc.py` |

## Run only the added tests

```sh
python -m unittest discover -s courseProjectCode/mutation-testing -p "mutation_*_tests.py" -v
```

Expected result: `Ran 9 tests` and `OK`

## Run mutation testing (initial and final)

```sh
python courseProjectDocs/mutation-testing/run_mutation.py
```

This takes about 5 minutes. It runs cosmic-ray on all three files twice and writes the results to `courseProjectDocs/mutation-testing/results/`:

1. **Initial:** existing MkDocs tests only. The script sets `PYTEST_ADDOPTS='-k "not mutation_"'`, which deselects our new test files, so this reproduces the score from before we added any tests.
2. **Final:** existing MkDocs tests plus our new tests.

To run one phase, add `initial` or `final`, for example `python courseProjectDocs/mutation-testing/run_mutation.py final`.

Expected totals:

```
== initial ==   TOTAL  170  101  69  0  59.4%
== final ==     TOTAL  170  132  38  0  77.6%
```

cosmic-ray edits the source file for each mutant and restores it afterwards. If you stop a run partway (Ctrl+C), run `git status`; if anything under `mkdocs/` shows as modified, restore it with `git restore mkdocs`.


## Output files

Written by `run_mutation.py` into `results/`:

| File | Contents |
|---|---|
| `results/initial/summary.txt`, `results/final/summary.txt` | Per-file mutant counts and mutation score |
| `results/<phase>/<file>-report.txt` | Every mutant with its outcome (killed / survived) and diff |
| `results/<phase>/<file>-survivors.txt` | Only the surviving mutants, with diffs |
| `results/testResults.txt` | `unittest` output for the 9 added tests (3 per team member) |

Other files in this folder:

| File | Contents |
|---|---|
| `run_mutation.py` | Script that runs both phases and writes the files above |
| `report.md` | Setup, scores, killed/survived analysis, and group contributions |
