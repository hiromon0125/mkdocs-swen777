# Mutation Testing Report

## Mutation testing setup

### Existing setup

MkDocs had no mutation testing set up. There is no mutmut, cosmic-ray, or similar tool in `pyproject.toml`, the hatch environments, or the GitHub Actions workflows. The project's own test command (`hatch run test:test`) runs `unittest` only.

### Added setup

| Item | Value |
|---|---|
| Tool | cosmic-ray 8.7.0 (runs tests with pytest) |
| Configuration | One TOML file per team member in `courseProjectCode/mutation-testing/config/` |
| Files mutated | `mkdocs/commands/gh_deploy.py`, `mkdocs/utils/meta.py`, `mkdocs/structure/toc.py` |
| Existing tests used | `mkdocs/tests/gh_deploy_tests.py`, the six meta-data tests in `mkdocs/tests/utils/utils_tests.py`, `mkdocs/tests/structure/toc_tests.py` |
| Added tests | `courseProjectCode/mutation-testing/mutation_{gh_deploy,meta,toc}_tests.py` |
| Run script | `courseProjectDocs/mutation-testing/run_mutation.py` |
| Report location | `courseProjectDocs/mutation-testing/results/{initial,final}/` |
| Recorded environment | Windows, Python 3.x |

**Why cosmic-ray.** Our team works on Windows. mutmut, the other common Python mutation tool, needs `fork()` and refuses to start on native Windows. cosmic-ray runs each mutant's tests in an ordinary subprocess, so it works the same on Windows, macOS, and Linux.

**How it works.** For each mutant, cosmic-ray edits the file under test, runs the config's `test-command`, and restores the file. A mutant is killed if the tests fail. Each config's `test-command` runs pytest on the existing MkDocs tests for that file plus the new test file, with `-o python_files=*_tests.py` to match MkDocs' test file naming. No existing MkDocs file was modified.

**Reproducing the initial score.** For the initial run, `run_mutation.py` sets `PYTEST_ADDOPTS='-k "not mutation_"'`, which deselects our new test files. This gives the score from before our tests were added, from the same commit and configs.

## Mutation scores

Mutation score = killed mutants / total mutants. cosmic-ray generated 170 mutants across the three files. There were no timeouts or incompetent mutants.

### Initial (existing MkDocs tests only)

| File | Mutants | Killed | Survived | Score |
|---|---:|---:|---:|---:|
| `mkdocs/commands/gh_deploy.py` | 90 | 34 | 56 | 37.8% |
| `mkdocs/utils/meta.py` | 36 | 26 | 10 | 72.2% |
| `mkdocs/structure/toc.py` | 44 | 41 | 3 | 93.2% |
| **Total** | **170** | **101** | **69** | **59.4%** |

### Final (existing tests + 9 new tests, 3 per team member)

| File | Mutants | Killed | Survived | Score |
|---|---:|---:|---:|---:|
| `mkdocs/commands/gh_deploy.py` | 90 | 57 | 33 | 63.3% |
| `mkdocs/utils/meta.py` | 36 | 31 | 5 | 86.1% |
| `mkdocs/structure/toc.py` | 44 | 44 | 0 | 100.0% |
| **Total** | **170** | **132** | **38** | **77.6%** |

### Change

31 of the 38 final survivors are **equivalent mutants**. They don't change the program's behavior, so no test can kill them (see the analysis below). The other 7 are in `gh_deploy.py` and could be killed with more tests. Each team member's three tests were chosen to kill as many surviving mutants as possible. Excluding equivalent mutants gives the score over the 139 mutants that can be killed.

| File | Initial | Final | Change | Newly killed | Equivalent | Final score excluding equivalent |
|---|---:|---:|---:|---:|---:|---:|
| `gh_deploy.py` | 37.8% | 63.3% | +25.5 pts | 23 | 26 | 57 / 64 = 89.1% |
| `meta.py` | 72.2% | 86.1% | +13.9 pts | 5 | 5 | 31 / 31 = 100% |
| `toc.py` | 93.2% | 100.0% | +6.8 pts | 3 | 0 | 44 / 44 = 100% |
| **Total** | **59.4%** | **77.6%** | **+18.2 pts** | **31** | **31** | **132 / 139 = 95.0%** |

Raw results: [`results/initial/summary.txt`](results/initial/summary.txt) and [`results/final/summary.txt`](results/final/summary.txt). Every mutant's outcome and diff is in `<file>-report.txt`, and survivors only are in `<file>-survivors.txt`.

## Mutants killed and survived: analysis

### `mkdocs/commands/gh_deploy.py`

**Why 56 survived initially.** `gh_deploy_tests.py` mocks `subprocess.Popen` and `ghp_import`, but it mostly asserts on return values. It never checks what the mocks were called with, it never tests version-comparison boundaries, and it uses only simple `user/repo.git` remote URLs.

**Killed by the new tests (23 mutants, 3 tests in `mutation_gh_deploy_tests.py`):**

| Test | Mutants killed |
|---|---|
| `test_default_arguments_are_passed_to_ghp_import` | 13: the `push` / `nojekyll` defaults flipped to `False` and `force` / `no_history` / `shell` flipped to `True` (5); `is None` → `is not None` (2); `not` added to the `host is None` and `.git` suffix checks (2); four changes to `repo[: -len('.git')]` (4). It asserts every keyword passed to `ghp_import.ghp_import` and the exact GitHub Pages URL that is printed. |
| `test_uppercase_prerelease_is_parsed_case_insensitively` | 7: replacements of `re.X \| re.I` that drop the case-insensitive flag, so `2.0.0RC1` is read as `2.0.0` |
| `test_same_version_logs_nothing_and_does_not_abort` | 3: `>` → `>=` (logs an upgrade) and `<` → `<=` / `is not` (aborts) when the versions are equal |

**Remaining 33 survivors.** 26 are equivalent:

| Mutants | Why it's equivalent |
|---|---|
| 22 replacements of `\|` in the type hints `tuple[str, str] \| tuple[None, None]` and `str \| None` | The file starts with `from __future__ import annotations`, so annotations are stored as strings and never evaluated. Changing the operator has no effect at runtime. |
| `re.X \| re.I` → `re.X + re.I` and `re.X ^ re.I` | `re.X` and `re.I` are separate bit flags, so `\|`, `+` and `^` all give the same value |
| `elif currentv < previousv` → `!=` | This branch is only reached when `currentv > previousv` is false, so `<` and `!=` select the same cases |
| `if TYPE_CHECKING:` → `if not TYPE_CHECKING:` | It only controls whether `MkDocsConfig` is imported for type hints. Importing it at runtime changes nothing. |

The other 7 could be killed, but each would need its own extra test and kills only one or two mutants, so they fall outside the three tests per member:

| Mutant | Test that would kill it |
|---|---|
| `except FileNotFoundError` replaced in `_is_cwd_git_repo` | git missing must log an error and abort |
| `proc.wait() == 0` → `<= 0` | a negative git exit code must return `False` |
| `cwd=repo_path or None` → `and` | assert the `cwd` passed to git |
| `split('github.com/', 1)`, `split('github.com:', 1)`, `path.split('/', 1)` → `2` (3) | remote URLs that contain the separator twice |
| `host is None or path is None` → `and` | a remote with a host but no path |

### `mkdocs/utils/meta.py`

**Why 10 survived initially.** The existing tests never put a non-metadata line straight after a key, never have more than one body line after metadata, and never exercise the fallback used when PyYAML's C loader (libyaml) is not available.

**Killed by the new tests (5 mutants, 3 tests in `mutation_meta_tests.py`):**

| Mutant | What changed | Test that kills it |
|---|---|---|
| `ReplaceAndWithOr` | `if m2 and key:` → `or` (crashes when a plain line follows a key) | `test_non_metadata_line_after_key_stops_parsing` |
| `NumberReplacer` ×2 | `lines.insert(0, line)` → `insert(1, ...)` / `insert(-1, ...)` (the first body line is put back in the wrong place) | same test, with three body lines so the position is visible |
| `ReplaceComparisonOperator_Eq_Lt` | `line.strip() == ''` → `< ''` (blank lines no longer end the metadata) | `test_whitespace_only_line_ends_metadata` |
| `ExceptionReplacer` | `except ImportError` around `from yaml import CSafeLoader` replaced (meta.py can't be imported without libyaml) | `test_falls_back_to_pure_python_loader_without_libyaml` swaps in a `yaml` module without `CSafeLoader` and re-imports meta.py |

**Remaining 5 survivors (all equivalent):**

| Mutants | Why it's equivalent |
|---|---|
| `re.UNICODE \| re.DOTALL` → `+`, `^`, `-` | `+` and `^` give the same flag value. `-` gives `re.DOTALL` alone, which behaves the same because `re.UNICODE` is already the default for `str` patterns in Python 3. |
| `line.strip() == ''` → `<= ''` | No string is less than `''`, so `<=` is true for exactly the same strings as `==` |
| `line.strip() == ''` → `is ''` | CPython reuses a single empty-string object, so `strip()` of a blank line is always that same object |

### `mkdocs/structure/toc.py`

**Why 3 survived initially.** `get_toc()` marks the first table-of-contents entry with `active = True`, but no existing test reads `active`, and none checks which entry gets it.

**Killed by the new tests (3 mutants, 3 tests in `mutation_toc_tests.py`):**

| Mutant | What changed | Test that kills it |
|---|---|---|
| `ReplaceTrueWithFalse` | `active = True` → `False` | `assertIs(first.active, True)` |
| `NumberReplacer` | `toc[0].active` → `toc[-1].active` (marks the last entry instead) | a TOC with two top-level entries; only the first may have `active` |
| `AddNot` | `if len(toc):` → `if not len(toc):` (nothing is ever marked) | same test |

No mutants survive in `toc.py`.

## Group contributions

As a team, we discussed the assignment and decided which files and areas to target:
`mkdocs/commands/gh_deploy.py`, `mkdocs/utils/meta.py`, and `mkdocs/structure/toc.py`.
Ty Carpenter then carried out the work: setting up cosmic-ray, writing the tests,
running the initial and final mutation runs, and writing the README and this report.
Godson Umoren and Hiroto Takeuchi reviewed the work and the PR before it was merged.

| File | Initial → final score | New tests | Mutants killed |
|---|---|---:|---:|
| `mkdocs/commands/gh_deploy.py` | 37.8% → 63.3% (89.1% excluding equivalent) | 3 | 23 |
| `mkdocs/utils/meta.py` | 72.2% → 86.1% (100% excluding equivalent) | 3 | 5 |
| `mkdocs/structure/toc.py` | 93.2% → 100.0% | 3 | 3 |
