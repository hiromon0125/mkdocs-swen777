# Integration Testing

How to run the integration tests. Works on Windows, macOS, and Linux.

## Prerequisites

- Python 3.8 or newer
- Run all commands from the repository root
- Install the package (this also installs click and ghp-import, which the tests use):

```sh
python -m pip install -e ".[i18n]"
```

On macOS / Linux, use `python3` in place of `python` if `python` isn't found.

## Run the tests

```sh
python -m unittest discover -s courseProjectCode/integration-testing -p "integration_*_tests.py" -v
```

Expected result: `Ran 6 tests` and `OK`

To run one file, change the pattern, for example `-p "integration_meta_tests.py"`.

Each test creates its own small MkDocs project in a temporary folder, builds it, and deletes it afterwards, so nothing in the repository changes. No network access or git setup is needed: the `gh-deploy` tests replace the git and GitHub steps with fakes.

The tests live in `courseProjectCode/integration-testing/`, not `mkdocs/tests/`, so MkDocs' own test command (`python -m unittest discover -s mkdocs -p "*tests.py"`) does not run them. We kept them outside `mkdocs/` so that no MkDocs files were changed, as in our earlier assignments.

## Test files

| File | What it tests | Tests |
|---|---|---|
| `integration_gh_deploy_tests.py` | The `mkdocs gh-deploy` command, from the command line through the site build to the push | 2 |
| `integration_meta_tests.py` | A title set at the top of a page shows up in the built site's nav bar and browser tab | 2 |
| `integration_toc_tests.py` | The sidebar links on a built page match the page's headings | 2 |

`report.md` describes each test, how the test data is made, the results, and the bug we found.
