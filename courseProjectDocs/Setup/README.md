# Baseline Build & Test

How to reproduce the artifacts in this folder.

## Prerequisites

- Python 3.12
- Run all commands from the repository root

## Build

- Install the package and its docs dependencies:
  - `python -m pip install -e ".[i18n]"`
  - `python -m pip install -r requirements/requirements-docs.txt`
- Build the documentation site: `python -m mkdocs build`
- Output is written to `site/`. Opening `site/index.html` in a browser will produce what you see in `builtSite.png`.
- Note: the docs requirements are required. Without them the build aborts with `Failed to load extension 'callouts'`.

## Tests and coverage

- Install coverage: `python -m pip install coverage`
- Run the suite under coverage:
  - `python -m coverage run --branch --source=mkdocs --omit "mkdocs/tests/*" -m unittest discover -s mkdocs -p "*tests.py" > testResults.txt 2>&1`
- Generate the reports:
  - `python -m coverage report --show-missing > coverageReport.txt`
  - `python -m coverage html`
- Run the integration suite: `python -m mkdocs.tests.integration > integrationResults.txt 2>&1`

NOTES:

- Coverage is measured with `coverage.py`, which MkDocs already uses — the project ships a `.coveragerc` and runs coverage in its CI pipeline. We use the project's existing tooling rather than adding our own.
- `--branch` is passed as a flag on the `coverage run` command above, since the project's `.coveragerc` does not enable branch coverage. We chose not to edit `.coveragerc` so that no MkDocs files are modified.
- `coverage html` generates the browsable report in `htmlcov/`, which gives per-file and per-line detail that the text summary in `coverageReport.txt` does not.
- `2>&1` is required because unittest writes its output to stderr.
- The integration suite is not included in the coverage figures. It does not match the `*tests.py` discovery pattern, and it runs builds in subprocesses that `coverage` would not measure anyway.

## Output files

The commands above write to the repository root. The generated files were then moved into `testResults/` and `testCoverage/`.


| File | Contents |
|---|---|
| `testResults/testResults.txt` | Full test run output, including tracebacks and the pass/fail summary |
| `testCoverage/coverageReport.txt` | Per-module statement and branch coverage |
| `testCoverage/htmlcov/` | Browsable HTML coverage report — open `index.html` |
| `testResults/integrationResults.txt` | Output from the integration suite |
| `builtSite.png` | Screenshot of the documentation site produced by `mkdocs build` |