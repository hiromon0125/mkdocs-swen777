
# Metrics

## Code Structure (LOC & comment density)

- Measures every `.py` file under `mkdocs/`, splits into production and test code
  - LOC = non-blank lines
  - Comment line = a line whose first character is `#`, or a line inside a docstring
- Setup: none, standard library only
- Execute python script from this directory:
  - `cd courseProjectCode/Metrics`
  - `python metrics.py ../../mkdocs`
- See the generated file (`metrics.csv`) for per-file results, plus a summary printed to the console

### Results

| | Files | LOC | Comment lines | Density |
|---|---|---|---|---|
| Production | 35 | 5,619 | 1,020 | 18.2% |
| Test | 26 | 10,222 | 553 | 5.4% |


## Codecov

- Setup
  - install uv: https://docs.astral.sh/uv/getting-started/installation/
- Execute python script: `./courseProjectCode/Metrics/codecov.py` or `uv run courseProjectCode/Metrics/codecov.py`
- see the generated file(`coverage_report.txt`)

