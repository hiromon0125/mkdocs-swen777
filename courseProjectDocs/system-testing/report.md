# System Testing Report

## Test Scope and Coverage

This suite covers three complete user workflows: creating and building a documentation project, previewing it over HTTP, and deploying generated pages to a Git branch. The public CLI is the only application interface: each invocation runs `[sys.executable, "-m", "mkdocs", ...]` in a fresh temporary project directory.

The tests treat MkDocs as a black box. Fixtures are plain configuration and Markdown files. Assertions inspect process exit codes, stdout/stderr, generated files, HTTP responses, and Git state read through the `git` CLI. Test code never imports MkDocs, calls internal functions, or replaces application behavior with mocks. Subprocess temporary files stay inside each test's disposable directory. Deployment uses a local bare remote and does not contact GitHub.

The [functional requirements and test oracles](../requirements-and-oracles.md#test-oracles) guide the build and preview checks:

| Requirement | Relevant checks |
|---|---|
| FR1.1: collect Markdown from `docs/` | ST-B1 builds `docs/index.md` and `docs/about.md`; ST-S1 serves both pages. This samples Markdown collection rather than repeating the oracle's numbered-file fixture. |
| FR2: generate page URL paths | ST-B1 checks `about/index.html` and `href="about/"`; ST-S1 requests `/about/`. These check default directory URLs. |
| FR3: use root configuration | ST-B1 and ST-S1 observe the configured site name; ST-B3 checks the missing-configuration failure. |
| FR4: use `site_name` in the page title | ST-B1 checks that the generated HTML `<title>` contains `System Test Site`. |

Out of scope are `get-deps` (which needs the network), themes beyond the default, and dedicated plugin behavior. The default configuration's bundled search plugin can run, but its behavior is not asserted. This suite also makes no performance, responsive-layout, or cross-browser claims. Unlike `mkdocs/tests/cli_tests.py`, which mocks command implementations, these tests execute real CLI processes and inspect their external effects.

## Test Case Summary

| ID | Title | Pre-conditions | Test Steps | Expected Results |
|---|---|---|---|---|
| ST-B1 | Create and build a project | Empty temporary directory; editable MkDocs installation | Run `new proj`; inspect the scaffold; set `site_name`, add an About page and link; run `build -d out` from `proj` | Both commands exit 0; scaffold contains `site_name: My Docs` and `docs/index.md`; output contains `index.html`, `about/index.html`, `sitemap.xml`, and `404.html`; HTML title contains `System Test Site` and link is `href="about/"` |
| ST-B2 | Broken link and strict mode | Plain project whose index links to `missing.md` | Run `build`, then `build --strict` | Normal build exits 0 and stderr contains `WARNING` and `missing.md`; strict build exits 1, reports the same warning on stderr, and stdout matches `Aborted with \d+ warnings? in strict mode!` |
| ST-B3 | Missing configuration | Empty temporary directory | Run `build` | Exit 1; stderr contains `Config file 'mkdocs.yml' does not exist.` |
| ST-S1 | Serve pages over HTTP | Project with home and About pages; free loopback port | Start `serve -a 127.0.0.1:<port> --no-livereload`; poll `GET /` for up to 30 seconds; request `/about/` and `/does-not-exist/`; stop the server with SIGINT on macOS / Linux | Homepage returns 200 and contains `Serve Test Site`; About returns 200 and contains `About`; missing page returns 404; project has no `site/`; process is reaped, with terminate/kill fallbacks available |
| ST-S2 | Invalid development address | Plain project with valid configuration | Run `serve -a notanaddress`, with a 30-second timeout | Non-zero exit; stderr contains `Must be a string of format 'IP:PORT'` |
| ST-D1 | Deploy to a Pages branch | Git on PATH; temporary bare remote and committed project with `origin` pointing to it | Run `gh-deploy`; list remote `gh-pages` files and read its latest commit message with Git | Exit 0; branch contains `index.html` and `.nojekyll`; message starts with `Deployed ` and contains `with MkDocs version:`; its source SHA resolves to the project's `HEAD` |
| ST-D2 | Deploy outside Git | Plain project outside any Git repository; Git discovery bounded by `GIT_CEILING_DIRECTORIES` | Run `gh-deploy`; inspect its output and generated files | Non-zero exit; stderr contains `Cannot deploy - this directory does not appear to be a git repository`; stdout contains `Deployment Aborted!`; already generated `site/index.html` remains until fixture cleanup |

## Execution and Results

The recorded run used macOS 26.6.1 (arm64), CPython 3.12.12, MkDocs 1.6.1 installed with `pip install -e .`, and Git 2.50.1 (Apple Git-155), on November 16, 2026. The full installed dependency list is in [`testResults/environment.txt`](testResults/environment.txt).

From the repository root with the virtual environment activated:

```sh
python -m unittest discover -s courseProjectCode/system-testing -p "system_*_tests.py" -v > courseProjectDocs/system-testing/testResults/testResults.txt 2>&1
```

Recorded result, with zero failures, errors, or skips:

```text
Ran 7 tests in 2.405s

OK
```

The complete output is saved in [`testResults/testResults.txt`](testResults/testResults.txt). The README installation, version check, single-file command, and full suite were also verified in a second clean Python 3.12 virtual environment. Other operating systems and Python versions were not executed.

To check that the main tests detect incorrect results, we temporarily changed one expected value in each test, ran that test alone, and restored the original file:

- **ST-B1:** Changed the expected title from `System Test Site` to `Wrong Site`; one assertion failed and unittest exited 1.
- **ST-S1:** Changed the expected homepage text from `Serve Test Site` to `Wrong Site`; one assertion failed and unittest exited 1. Cleanup still stopped the child and removed its temporary files.
- **ST-D1:** Changed the expected remote file from `index.html` to `wrong.html`; one assertion failed and unittest exited 1.

All three deliberate changes were reverted. The final unmodified suite passed. Cleanup verification inspected an isolated temporary root and used `lsof` on the actual serve test port after the run; no fixture directories, preview directories, or listening server remained. Git checks confirmed that nothing under `mkdocs/` changed and no test code imports MkDocs.

**Behavioural deviations:**

- **ST-D2:** Deployment outside a Git repository does not stop at the repository check. Observed stderr first reports site cleaning, building, and successful documentation generation, then `Cannot deploy - this directory does not appear to be a git repository`. It continues to the copy/push attempt and reports `Failed to deploy to GitHub with error:` followed by a not-a-repository error from the Git import step. The process exits 1 and prints `Deployment Aborted!` on stdout. `site/index.html` remains. The test asserts this leftover file before its temporary directory is removed. The logging-only check in [`gh_deploy.py`](../../mkdocs/commands/gh_deploy.py) is consistent with this result; the CLI builds before calling that function.
- **ST-B2:** A broken Markdown link is a warning during a normal build, so it still exits 0. With `--strict`, the same fixture exits 1 and prints `Aborted with 1 warnings in strict mode!`. The abort summary is on stdout, while the warning is on stderr. The initial stderr-only expectation failed; the final assertion uses the observed stream.
- **ST-D1:** The deployment message uses an abbreviated source SHA, rather than the full output of `git rev-parse HEAD`. The initial literal equality assertion failed. The final test resolves the message's SHA through Git and compares the full result with `HEAD`.
- **ST-S1:** `serve` generates preview files in a temporary directory rather than the project's `site/`. During failure injection, terminating the process with SIGTERM left its preview directory behind. POSIX cleanup now sends SIGINT first, even after an assertion failure, and retains terminate/kill fallbacks. No shutdown-message assertion is used. Windows uses termination and relies on fixture containment for file cleanup.
- **ST-S2:** An invalid development address also left an empty `mkdocs_*` temporary directory behind during verification. Subprocess `TMPDIR`, `TMP`, and `TEMP` now point inside the owned fixture directory, so cleanup contains this application side effect without modifying MkDocs.

The first deployment fixture commit was also blocked by this machine's personal global Git author-email hook. Subprocesses now use a fixed test identity and `GIT_CONFIG_GLOBAL` pointing to the null device; no personal Git configuration was changed. These initial harness failures were resolved before recording the final passing results.

## Group Contributions

The workflow ownership below follows the team allocation.

| Team member | Tests | Contribution |
|---|---|---|
| [Hiroto Takeuchi (@hiromon0125)](https://github.com/hiromon0125) | ST-B1, ST-B2, ST-B3 | Project setup and build: `mkdocs new` → `mkdocs build`; check `index.html`, the configured site name in the title, expected URL paths, strict-mode behavior, and missing configuration. |
| [Ty Carpenter (@tjc7058)](https://github.com/tjc7058) | ST-D1, ST-D2 | Deployment: run `mkdocs gh-deploy` against a local bare repository; check `gh-pages` for `index.html`, `.nojekyll`, and source commit metadata; document the outside-Git failure. |
| [Godson Umoren (@KayUmoren004)](https://github.com/KayUmoren004) | ST-S1, ST-S2 | Live preview: start `mkdocs serve -a 127.0.0.1:<free port>`, request `/` and a subpage over HTTP, check 404 and invalid-address behavior, and stop the server with SIGINT on the recorded platform. |
