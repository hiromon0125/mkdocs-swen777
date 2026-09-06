
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


## Cyclomatic Complexity

- Measures every function and method in `.py` files under `mkdocs/` with [radon](https://radon.readthedocs.io/), split into production and test code
  - CC = decision points + 1 (`if`, `elif`, loops, `except`, boolean operators, comprehensions)
  - Thresholds: 1-5 fine, 6-10 watch, 11-15 refactor now, 16+ must split
- Setup
  - install uv: https://docs.astral.sh/uv/getting-started/installation/ (radon is fetched on demand by `uvx`)
- Execute from the repository root:
  - `uvx radon cc -s -a --total-average mkdocs/ > courseProjectCode/Metrics/cyclomatic_complexity_raw.txt`
- See the raw per-function output (`cyclomatic_complexity_raw.txt`) and the summarized report (`cyclomatic_complexity_report.md`) for hotspots and per-file results

### Results

| | Functions | Avg CC | Max CC | CC 1-5 | CC 6-10 | CC 11-15 | CC 16+ |
|---|---|---|---|---|---|---|---|
| Production | 453 | 2.83 | 32 | 398 | 39 | 12 | 4 |
| Test | 798 | 1.23 | 12 | 794 | 3 | 1 | 0 |

Highest-complexity production functions: `_RelativePathTreeprocessor.path_to_url` (32), `build` (24), `Plugins.load_plugin` (21), `Theme.run_validation` (16).
