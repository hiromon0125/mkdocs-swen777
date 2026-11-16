# System Testing

Black-box, end-to-end tests of MkDocs project creation, site builds, live preview, and deployment, using the CLI and its observable outputs.

## Prerequisites

- Python 3.12 for the recorded environment; the tests use Python 3.8+ compatible standard-library APIs.
- `git` on PATH. Without it, the two deployment tests are skipped.
- Run all commands from the repository root.

**Windows (PowerShell)**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e .
python -m mkdocs --version
```

**macOS / Linux**

```sh
python3 -m venv venv
source venv/bin/activate
python -m pip install -e .
python -m mkdocs --version
```

Use Python 3.12 when creating the environment to match the recorded run (for example, `python3.12 -m venv venv` on macOS / Linux).

## Added tests

| File under `courseProjectCode/system-testing/` | Workflow | Test IDs |
|---|---|---|
| `system_build_tests.py` | Create a project and build its site; strict mode and missing configuration | ST-B1, ST-B2, ST-B3 |
| `system_serve_tests.py` | Serve pages over HTTP; reject an invalid address | ST-S1, ST-S2 |
| `system_deploy_tests.py` | Deploy to a local Git remote; fail outside a Git repository | ST-D1, ST-D2 |

`system_support.py` provides subprocess and plain-file fixture helpers. It does not match the test discovery pattern.

## Run the system tests

Save the output, including unittest's stderr, with:

```sh
python -m unittest discover -s courseProjectCode/system-testing -p "system_*_tests.py" -v > courseProjectDocs/system-testing/testResults/testResults.txt 2>&1
```

Expected result: `Ran 7 tests` and `OK`, with no skips when Git is available. Read the saved file to see the results. Omit the redirection to display them in the terminal.

Run a single file with:

```sh
python -m unittest discover -s courseProjectCode/system-testing -p "system_build_tests.py" -v
```

Expected result for this file: `Ran 3 tests` and `OK`.

**NOTES:**

- The tests run the installed `mkdocs` through `python -m mkdocs`, using the active interpreter. Run `pip install -e .` first so subprocesses launched from temporary directories can find this checkout.
- The serve test binds a random free port on `127.0.0.1`, polls HTTP readiness, and requests the homepage, a subpage, and a missing page. On macOS / Linux it stops the server with SIGINT. Cleanup falls back to `terminate()` and then `kill()`; Windows uses `terminate()` because POSIX SIGINT delivery is unavailable through this Popen setup.
- The deployment tests push only to a local bare repository inside a temporary directory, never to the network. Fixed Git identities and isolated global Git configuration keep personal hooks and signing settings out of the fixtures.
- Each test owns a temporary directory. Subprocess temporary files are also placed there, including files left by failed CLI commands.
- No MkDocs files are modified, and the test code never imports MkDocs.

## Output files

| File | Contents |
|---|---|
| [`testResults/testResults.txt`](testResults/testResults.txt) | Verbose unittest output for all seven tests, captured with `2>&1` |
| [`testResults/environment.txt`](testResults/environment.txt) | OS and architecture, Python version, then `pip freeze` |

See [`report.md`](report.md) for test cases, observed behavior, failure checks, and group contributions.
