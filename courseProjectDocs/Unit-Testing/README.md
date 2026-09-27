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

For the dependency versions used in the recorded run, activate a Python 3.12 virtual environment and run `python -m pip install -r courseProjectDocs/Unit-Testing/testResults/environment.txt` from the repository root. The recorded platform is macOS; platform-dependent results may differ elsewhere.

The following shell commands write directly to the deliverable folders:

```sh
mkdir -p courseProjectDocs/Unit-Testing/testResults courseProjectDocs/Unit-Testing/testCoverage
python -m coverage run --branch --source=mkdocs --omit "mkdocs/tests/*" -m unittest discover -s mkdocs -p "*tests.py" > courseProjectDocs/Unit-Testing/testResults/testResults.txt 2>&1
python -m coverage report --show-missing > courseProjectDocs/Unit-Testing/testCoverage/existingSuiteCoverageReport.txt
python -m coverage json -o courseProjectDocs/Unit-Testing/testCoverage/existingSuiteCoverage.json
python -m coverage run --append --branch --source=mkdocs --omit "mkdocs/tests/*" -m unittest discover -s courseProjectCode/Unit-Testing -p "*tests.py" -v >> courseProjectDocs/Unit-Testing/testResults/testResults.txt 2>&1
python -m coverage report --show-missing > courseProjectDocs/Unit-Testing/testCoverage/coverageReport.txt
python -m coverage json -o courseProjectDocs/Unit-Testing/testCoverage/coverage.json
python -m coverage html -d courseProjectDocs/Unit-Testing/testCoverage/htmlcov
```

The recorded existing-suite run exits with status 1 because two subtests fail within one method. Run the subsequent commands even when that occurs, so the added tests and reports are produced; do not join these commands with `&&`. See `report.md` for the failure details and method-level counts.

NOTES:

- The added tests live in `courseProjectCode/` rather than `mkdocs/tests/` because they are our code, not part of MkDocs. The existing MkDocs test command only discovers tests under `mkdocs/`, so the added tests are run with a second command.
- `--append` adds the coverage from the second run to the first instead of overwriting it, so the final report reflects the existing suite plus the added tests.
- `--branch` and the other flags match the baseline command in `courseProjectDocs/Setup/README.md`, so the before and after coverage numbers are able to be compared.
- `2>&1` is required because unittest writes its output to stderr.
- `testResults.txt` contains two summaries: one for the existing MkDocs suite and one for the added tests.

## Output files

The commands above write directly into this folder’s `testResults/` and `testCoverage/` directories.

| File | Contents |
|---|---|
| `testResults/testResults.txt` | Full test run output for the existing suite and the added tests, including the pass/fail summaries |
| `testCoverage/coverageReport.txt` | Per-module statement and branch coverage, including the added tests |
| `testCoverage/htmlcov/` | Browsable HTML coverage report. Open `index.html` |
| `report.md` | New test cases and rationale, test results, and coverage comparison with the baseline |
| `testCoverage/existingSuiteCoverageReport.txt` | Existing-suite control measurement on the current environment |
| `testCoverage/existingSuiteCoverage.json`, `testCoverage/coverage.json` | Exact coverage counts before and after adding the cases |
| `testResults/environment.txt` | Recorded platform, interpreter, and installable dependency versions |
