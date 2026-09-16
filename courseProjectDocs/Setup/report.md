# Baseline Build & Test Report — MkDocs

**Team 7 (SWEN-777):** Godson Umoren, Ty Carpenter, Hiroto Takeuchi
**Project:** MkDocs 1.6.1 (fork: https://github.com/hiromon0125/mkdocs-swen777)

## Environment

| | |
|---|---|
| Operating system | Windows 11 |
| Python | 3.12 |
| Package install | `pip install -e ".[i18n]"` (editable install from source) |
| Docs dependencies | `requirements/requirements-docs.txt` |
| Test runner | `unittest` (Python standard library) |
| Coverage tool | `coverage.py` |

Reproduction commands are in `README.md` in this folder.

## Build

The project builds from source without modification. After installing the package and the documentation requirements, `mkdocs build` renders MkDocs' own documentation into a `site/` directory:

```
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: C:\SWEN-777\mkdocs-swen777BuildAndTest\site
INFO    -  Documentation built in 1.48 seconds
```

The generated site renders correctly in a browser see `courseProjectDocs/Setup/builtSite.png`. Building MkDocs' documentation with MkDocs itself actually runs the full pipeline: configuration loading, Markdown rendering, theme templating, and copying the theme's stylesheets and images.

One build issue I think is worth recording. The documentation requirements are a separate install from the package itself. Without them, the build aborts with `Failed to load extension 'callouts'`, because `mkdocs.yml` declares Markdown extensions that are not dependencies of the `mkdocs` package.

## Test suite summary

MkDocs has two distinct test suites.

**Unit tests** — 20 files under `mkdocs/tests/`, discovered with `python -m unittest discover -s mkdocs -p "*tests.py"`. These are the 725 tests measured below. The test files map directly onto the package structure, with subfolders mirroring the production packages: `config/` for configuration loading and validation, `structure/` for the page, file, navigation, and table-of-contents model, and `utils/` for shared helper functions.

**Integration tests** — a separate suite at `mkdocs/tests/integration.py`, run with `python -m mkdocs.tests.integration`. It builds the MkDocs documentation against each theme and four sample projects, and checks that the builds succeed. All six builds completed successfully. It does not follow the `*tests.py` naming pattern, so it is excluded from unittest discovery and from the coverage figures below.

There are no system or UI test suites.

## Test results

| Metric | Count |
|---|---|
| Tests run | 725 |
| Passed | 720 |
| Failed (assertion failures) | 0 |
| Errors (unexpected exceptions) | 4 |
| Skipped | 1 |

No test failed on an assertion. The four errors are all the same problem: tests in `livereload_tests.py` have this failure `OSError: [WinError 1314] A required privilege is not held by the client`.

- `test_watch_with_broken_symlinks`
- `test_watches_direct_symlinks`
- `test_watches_through_relative_symlinks`
- `test_watches_through_symlinks`

The reason these fail is because Windows restricts symbolic link creation to administrators unless Developer Mode is enabled. These are environment failures, not defects in MkDocs. Full tracebacks are in `testResults/testResults.txt`.

## Coverage summary

| Metric | Value |
|---|---|
| Statements | 3,643 |
| Statements missed | 323 |
| Branches | 1,098 |
| Branches partially covered | 108 |
| Overall coverage | 90% |

This run reports 90% overall. The coverage report in `courseProjectCode/Metrics/` reports 91% because it was generated without `--branch`. The difference is not a change in what the tests exercise. It is how coverage.py combines the two measures into a single figure rather than averaging them:

    statements:       3,320 / 3,643 = 91.1%
    branches:    928 / 1,098 = 84.5%

    combined:
    covered:  3,320 statements +   928 branches = 4,248
    total:    3,643 statements + 1,098 branches = 4,741

    4,248 / 4,741 = 89.6% -> 90%


Coverage is high across most of the codebase.

### Lowest covered modules

| Module | Statements | Coverage |
|---|---|---|
| `utils/cache.py` | 11 | 0% |
| `utils/filters.py` | 1 | 0% |
| `commands/serve.py` | 59 | 16% |
| `__main__.py` | 185 | 79% |
| `commands/new.py` | 25 | 79% |

## Observations

**Uncovered code is concentrated in entry points and wrappers, not in logic.** The three lowest-covered modules are the `serve` command, a one line filter module, and an 11 statement cache wrapper.

**`commands/serve.py` at 16% reflects its design.** The function starts a development server that blocks until interrupted, so a unit test that called it wouldn't complete or serve a useful purpose. The underlying server mechanism it depends on is tested separately here: `livereload/` sits at 83% across 236 statements.

**`utils/cache.py` at 0% because it is a delegation wrapper.** It uses an external package and its other function makes a live HTTP request, which would require network access in a test. Nothing inside `mkdocs/` imports it.

**The test suite is large relative to the production code.** From `courseProjectCode/Metrics/metrics.csv`: 10,222 test LOC / 5,619 production LOC = 1.82, so there is roughly 1.8 times as much test code as production code. The tests are simple and readable rather than a second system to maintain.


