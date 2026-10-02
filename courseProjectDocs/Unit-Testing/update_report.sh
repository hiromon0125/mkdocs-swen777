#!/usr/bin/env bash

# First argument can be used to specify the path to the Python executable. Default is to use the Python executable found in the current environment or "/usr/bin/python".
python_path=${1:-$(which python || echo "/usr/bin/python")}

# This script updates the report file with the latest test results.
$python_path -m coverage run --branch --source=mkdocs --omit "mkdocs/tests/*" -m unittest discover -s mkdocs -p "*tests.py" > courseProjectDocs/Unit-Testing/testResults/testResults.txt 2>&1
$python_path -m coverage report --show-missing > courseProjectDocs/Unit-Testing/testCoverage/existingSuiteCoverageReport.txt
$python_path -m coverage json -o courseProjectDocs/Unit-Testing/testCoverage/existingSuiteCoverage.json
$python_path -m coverage run --append --branch --source=mkdocs --omit "mkdocs/tests/*" -m unittest discover -s courseProjectCode/Unit-Testing -p "*tests.py" -v >> courseProjectDocs/Unit-Testing/testResults/testResults.txt 2>&1
$python_path -m coverage report --show-missing > courseProjectDocs/Unit-Testing/testCoverage/coverageReport.txt
$python_path -m coverage json -o courseProjectDocs/Unit-Testing/testCoverage/coverage.json
$python_path -m coverage html -d courseProjectDocs/Unit-Testing/testCoverage/htmlcov

echo "Test results and coverage reports have been updated."