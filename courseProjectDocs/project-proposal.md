# Project Proposal — MkDocs

**Team 7 (SWEN-777):** Godson Umoren, Ty Carpenter, Hiroto Takeuchi
**Repository:** https://github.com/mkdocs/mkdocs (fork: https://github.com/hiromon0125/mkdocs-swen777)
**Version analyzed:** 1.6.1

## Project Overview

MkDocs is an open-source static site generator written in Python that builds project documentation websites using provided Markdown source files.

The system is configuration driven. A user writes Markdown in a `docs/` directory, configures desired site settings in a `mkdocs.yml` file, and MkDocs renders a themed static HTML site. Its architecture is organized around a few areas: configuration loading and validation (`config/`), the document model of pages, files, and navigation (`structure/`), the build and serve commands (`commands/`), a plugin system with a documented event hook API (`plugins.py`), and a live reloading development server (`livereload/`).

We selected MkDocs for three reasons. First, it is an actively maintained project rather than a random codebase, so the metrics we collect describe real production software. Second, it is a manageable size. It is roughly 5,600 lines of production Python code across 35 files, which means we can analyze individual modules beyond just only reporting on the project as a whole. Third, it already has a pretty meaningful quality infrastructure in place. It has a test suite of 725 cases, a code coverage configuration, and a CI pipeline that runs coverage on every push. That gave us a baseline to measure against rather than a codebase where we would have had to build the tooling ourselves.

## Key Quality Metrics

We focused on two quality attributes from the assignment: **maintainability**, measured through code structure, and **testability**, measured through the test suite and its coverage. All metrics were collected utilizing scripts. The scripts and instructions to reproduce every number below are in `courseProjectCode/Metrics/`.

**Scope and definitions.** All three metrics measure `.py` files under the `mkdocs/` package, reported on both production and test code. We defined a line of code as any non-blank line, and a comment line as any line beginning with `#` or any line inside a docstring. We chose to include docstrings because MkDocs documents its public API primarily through docstrings rather than inline comments. We felt counting only `#` lines would have reported 3.8% comment density instead of 18.2% and would have significantly underestimated how well the codebase is documented.

### Code Structure

| | Files | LOC | Comment lines | Density | Avg LOC/file |
|---|---|---|---|---|---|
| Production | 35 | 5,619 | 1,020 | 18.2% | 160 |
| Test | 26 | 10,222 | 553 | 5.4% | 393 |

Production modules average 160 lines, which is a reasonable size, but the distribution is uneven. `config/config_options.py` is 978 lines which is nearly six times the average and by far the largest module. `plugins.py` (541), `structure/files.py` (506), and `structure/pages.py` (466) have more than the average lines of code as well. These four files hold roughly 45% of all the production code.

Comment density is at 18.2%, but it is not evenly distributed either. `plugins.py` contains over half documentation which may be intentional because its docstrings serve as the reference for developers writing MkDocs plugins. Three `utils/` modules have no comments at all, while `utils/meta.py` is 45% documentation.

### Cyclomatic Complexity

| | Functions | Avg CC | Max CC | CC 1-5 | CC 6-10 | CC 11-15 | CC 16+ |
|---|---|---|---|---|---|---|---|
| Production | 453 | 2.83 | 32 | 398 | 39 | 12 | 4 |
| Test | 798 | 1.23 | 12 | 794 | 3 | 1 | 0 |

Average complexity of 2.83 is low, and 88% of the production functions score 5 or below. The codebase is mostly simple, straight code with not much branching. Four functions score 16 or higher: `_RelativePathTreeprocessor.path_to_url` (32) in `structure/pages.py`, build (24) in `commands/build.py`, and Plugins.load_plugin (21) and Theme.run_validation (16) in `config/config_options.py`. Two of these files also rank among the largest by LOC, so size and complexity concentrate in the same places.

### Testability

| Metric | Value |
|---|---|
| Test cases | 725 |
| Test files | 26 |
| Test LOC | 10,222 |
| Test-to-production LOC ratio | 1.82 : 1 |
| Line coverage | 91% (3,643 statements, 326 missed) |

MkDocs is well tested. There is nearly twice as much test code as production code, and line coverage sits at 91%. Test functions also average 1.23 complexity, meaning the tests themselves are simple and readable as well.

Coverage is high across most modules, but two gaps in the coverage_report stand out. `commands/serve.py` sits at 20% and `utils/cache.py` at 0%. The `serve` file runs a development server that blocks until interrupted, which is difficult to exercise in a unit test. The `cache` file is a wrapper around an external package and requires network access to test it. These are cases where low coverage reflects the design of the code rather than neglect by the developers. It also shows why coverage should be read alongside structural metrics rather than on its own.

### What the metrics suggest

Taken together, the three metrics describe a codebase that is well tested and well documented, with complexity concentrated in a small number of modules. Our findings overlap most clearly on `config/config_options.py`, which is both the largest production module at 978 lines and the home of two of the four functions scoring 16 or higher. `structure/pages.py` is another point of interest, ranking 4th by LOC and containing the single most complex function at 32. These files point to where future analysis should be focused. Additionally, `commands/build.py` is at 98% coverage despite holding a function at 24, which may suggest the maintainers are already aware of the risk in this file.

## Notes

The test suite reports 2 failures and 4 skipped tests when run in a current environment.