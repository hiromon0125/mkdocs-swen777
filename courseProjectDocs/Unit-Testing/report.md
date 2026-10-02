# Unit Testing I — Extend Coverage

## Scope and reproduction

The 15 added cases in [unit_testing1_tests.py](../../courseProjectCode/Unit-Testing/unit_testing1_tests.py) use Python's built-in `unittest`. This report compares coverage from the existing tests with coverage after including the 15 added tests. Production code and the added tests were not changed. Integration tests are excluded, matching the baseline.

See [README.md](README.md) for commands and [environment.txt](testResults/environment.txt) for the Python, macOS, and dependency versions. This run used Python 3.12.11 and coverage.py 7.16.2. The historical baseline used Python 3.12 on Windows 11. The existing tests were also run on this machine before the new tests were included. This gives us a comparison using the same setup, so we can identify the improvement from the added tests.

## New cases and rationale

All names below refer to test methods in `unit_testing1_tests.py`.

| Test case | Rationale / behavior checked |
|---|---|
| `test_bad_yaml_raises_configuration_error` | Malformed YAML must become a MkDocs `ConfigurationError`. |
| `test_empty_yaml_returns_empty_dict` | Empty configuration input returns an empty dictionary. |
| `test_warning_filter_still_works` | The older `warning_filter` attribute still returns a logging filter. |
| `test_unknown_attribute_raises_error` | An unknown utility attribute raises `AttributeError`. |
| `test_path_to_url_converts_backslashes` | Windows-style separators become URL forward slashes. |
| `test_markdown_title_none_when_first_line_is_not_heading` | A later heading must not become the title when plain text comes first. |
| `test_markdown_title_none_for_blank_input` | Blank and whitespace-only content has no title. |
| `test_create_media_urls_joins_base` | Both stylesheet and script paths receive the requested base path. |
| `test_clean_directory_keeps_hidden_files` | Cleanup removes a visible file while preserving a hidden file. |
| `test_private_vars_still_returns_theme_settings` | The older `Theme._vars` attribute still returns the theme settings. |
| `test_delete_key_from_theme` | Removing a theme setting returns its value, removes it from the theme, and reduces the number of settings by one. |
| `test_new_does_not_overwrite_existing_config` | Project creation preserves an existing user configuration. |
| `test_new_does_not_overwrite_existing_index` | Project creation preserves an existing homepage. |
| `test_new_in_existing_empty_folder` | An existing empty directory still receives configuration and homepage files. |
| `test_abort_exits_with_code_1` | Stopping a build with `Abort` exits with error code 1. This checks an edge case but did not increase coverage in this run. |


## Test results

> [!NOTE] The report files mentioned below have been updated since Unit test 2 assignment. If you wish to review the resulting report files, please view [tagged commit on GitHub](https://github.com/hiromon0125/mkdocs-swen777/releases/tag/unittest1).

The [full test output](testResults/testResults.txt) includes error details for the existing tests and individual results for all 15 added tests.

| Suite | Test methods run | Passed | Failed methods | Errors | Skipped |
|---|---:|---:|---:|---:|---:|
| Historical baseline | 725 | 720 | 0 | 4 | 1 |
| Existing suite, current environment | 725 | 720 | 1 | 0 | 4 |
| Added cases | 15 | 15 | 0 | 0 | 0 |
| Current combined total | 740 | 735 | 1 | 0 | 4 |

All 15 added cases passed. The full suite is not entirely passing. `unittest` reports `FAILED (failures=2, skipped=4)` for the existing suite: both failures come from two scenarios within the same test method, `BuildTests.test_draft_docs_with_comments_from_user_guide`, for `serve_url=None` and `serve_url='http://localhost:123/documentation/'`. They are both artifacts prior to our new set of unittests. 

The baseline's four errors came from MkDocs’ existing live-reload tests because Windows denied permission to create symbolic links. They were not in the 15 added tests. The current run has no errors and four skipped tests, but uses a different operating system and dependency versions. Warnings about older features being phased out do not count as test failures.

## Coverage improvement

All three measurements use branch coverage, `--source=mkdocs`, and `--omit "mkdocs/tests/*"`. Each measurement checks the same amount of code: 3,643 executable statements and 1,098 possible outcomes of code branches. Statement coverage shows how much code the tests run; branch coverage shows which outcomes they exercise, such as both sides of an `if` condition.

| Metric                           | Historical baseline | Current existing suite | Current suite + added cases |
| -------------------------------- | ------------------: | ---------------------: | --------------------------: |
| Covered statements               |               3,320 |                  3,318 |                       3,336 |
| Missed statements                |                 323 |                    325 |                         307 |
| Statement coverage               |              91.13% |                 91.08% |                      91.57% |
| Covered branch outcomes          |                 928 |                    929 |                         937 |
| Missed branch outcomes           |                 170 |                    169 |                         161 |
| Partially covered branches       |                 108 |                    107 |                          99 |
| Branch coverage                  |              84.52% |                 84.61% |                      85.34% |
| Combined coverage                |              89.60% |                 89.58% |                      90.13% |

Combined coverage is `(covered statements + covered branch outcomes) / (3,643 + 1,098)`. The baseline tests covered 4,248 of these items, and the current tests cover 4,273. This improves coverage by 0.53 percentage points over the historical baseline.

Comparing the runs on this machine shows that the added tests cover 18 more statements and 8 more branch outcomes. Combined coverage rises from 89.58% to 90.13%, an improvement of 0.55 percentage points. Compared with the original Windows baseline, the increase is 16 statements and 9 branch outcomes. That comparison also reflects differences in the test environment, so the added tests do not account for the entire change.

### Modules improved by the added tests

For these four modules, coverage from the existing tests is the same in the baseline and the current run. The percentages below include both statement and branch coverage.

| Module | Before | After | Newly covered statements | Newly covered branch outcomes |
|---|---:|---:|---:|---:|
| `mkdocs/commands/new.py` | 78.79% | 96.97% | 3 | 3 |
| `mkdocs/theme.py` | 91.00% | 95.00% | 4 | 0 |
| `mkdocs/utils/__init__.py` | 88.28% | 92.41% | 8 | 4 |
| `mkdocs/utils/yaml.py` | 87.91% | 92.31% | 3 | 1 |

Project creation shows the largest improvement. The added tests check that existing files are preserved and that a project can be created in an existing directory. They also cover invalid or empty YAML input and older utility and theme features. `mkdocs/exceptions.py` remains at 90% because the existing tests already run the code checked by the Abort test. A test can check useful behavior without increasing coverage.

The tests still leave 307 statements and 161 branch outcomes uncovered. The added tests do not target `commands/serve.py`, `utils/cache.py`, or `utils/filters.py`. Coverage shows which code ran during testing; it does not guarantee that the code is correct. The existing test failures are recorded above.
