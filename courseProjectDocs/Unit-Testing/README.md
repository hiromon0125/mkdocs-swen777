# Unit Testing I

How to run the added unit tests

## Prerequisites

- Python 3.12
- Run all commands from the repository root
- Install the package and coverage:
  - `python -m pip install -e ".[i18n]"`
  - `python -m pip install coverage`

## Added tests

- Location: `courseProjectCode/Unit-Testing/unit_testing1_tests.py`
- Framework: Python's built-in `unittest`, the same framework used by the existing MkDocs test suite
- 15 test cases targeting lines reported as missing in the baseline coverage report (`courseProjectDocs/Setup/testCoverage/coverageReport.txt`)

## Run only the added tests

- `python -m unittest discover -s courseProjectCode/Unit-Testing -p "*tests.py" -v`
- Expected result: `Ran 15 tests` and `OK`

## Run the full suite with coverage

- Run the existing MkDocs suite under coverage (same command as the baseline):
  - `python -m coverage run --branch --source=mkdocs --omit "mkdocs/tests/*" -m unittest discover -s mkdocs -p "*tests.py" > testResults.txt 2>&1`
- Run the added tests and append their coverage to the same data:
  - `python -m coverage run --append --branch --source=mkdocs --omit "mkdocs/tests/*" -m unittest discover -s courseProjectCode/Unit-Testing -p "*tests.py" >> testResults.txt 2>&1`
- Generate the reports:
  - `python -m coverage report --show-missing > coverageReport.txt`
  - `python -m coverage html`

NOTES:

- The added tests live in `courseProjectCode/` rather than `mkdocs/tests/` because they are our code, not part of MkDocs. The existing MkDocs test command only discovers tests under `mkdocs/`, so the added tests are run with a second command.
- `--append` adds the coverage from the second run to the first instead of overwriting it, so the final report reflects the existing suite plus the added tests.
- `--branch` and the other flags match the baseline command in `courseProjectDocs/Setup/README.md`, so the before and after coverage numbers are able to be compared.
- `2>&1` is required because unittest writes its output to stderr.
- `testResults.txt` contains two summaries: one for the existing MkDocs suite and one for the added tests.

## Output files

The commands above write to the repository root. The generated files were then moved into `testResults/` and `testCoverage/`.

| File | Contents |
|---|---|
| `testResults/testResults.txt` | Full test run output for the existing suite and the added tests, including the pass/fail summaries |
| `testCoverage/coverageReport.txt` | Per-module statement and branch coverage, including the added tests |
| `testCoverage/htmlcov/` | Browsable HTML coverage report. Open `index.html` |
| `report.md` | New test cases and rationale, test results, and coverage comparison with the baseline |