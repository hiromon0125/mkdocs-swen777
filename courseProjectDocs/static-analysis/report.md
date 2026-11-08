# Static Analysis Report

## Tool used

We used **Ruff 0.1.14**, the version pinned in
`requirements/requirements-style.txt`. Ruff performs static analysis without
executing the application. We kept the repository's configured rules and enabled
additional bugbear, simplification, return, performance, and pathlib rules for
this assignment (`B,SIM,RET,PERF,PTH`). We used the pinned version because newer
Ruff versions have removed or renamed some rules in this repository's config.

| Item | Recorded value |
|---|---|
| Date | November 7, 2026 |
| Branch | `static-analysis-code-smells` |
| Baseline commit | `e58589b469567d7d4d7af00c830650ba91140df3` |
| Final revision | Changes on `static-analysis-code-smells` relative to the baseline; see the PR commit history |
| Analysis scope | Production Python under `mkdocs/`, excluding `mkdocs/tests/` |
| Other exclusions | Course scripts, generated reports, and bundled JavaScript are outside the production Python scan |
| Validation platform | macOS, CPython 3.12.12 |

Run these commands from the repository root. The extended scan intentionally
exits with status **1** when it finds diagnostics; status 2 indicates a tool or
configuration error.

```sh
uvx --from ruff==0.1.14 ruff --version
uvx --from ruff==0.1.14 ruff check mkdocs \
    --extend-exclude mkdocs/tests \
    --extend-select B,SIM,RET,PERF,PTH \
    --no-cache --output-format json > before.json
```

Run the identical scan after applying the fixes, writing to `after.json`.
We also ran the original project checks, which include tests and documentation
Python, before and after:

```sh
uvx --from ruff==0.1.14 ruff check mkdocs docs \
    --no-cache --output-format json > configured-before.json
```

For the final run, change only the output filename to `configured-after.json`.
The captured outputs are saved in [`results/`](results/).

## Key findings

The extended scan found **170 diagnostics**. We selected **nine logical code
smells**, covering **11 reported occurrences** across four rule types. The
`ListOfPaths` constructor and its two overload signatures are counted as one
logical finding. No formatting-only edits count toward the nine fixes.

All selected findings are classified as code smells. The mutable defaults are
preventive cleanup: configuration defaults already have a copying accessor,
which reduces the risk of accidental shared-state changes. The hook-cache
retention problem was also reproduced with a failing regression test.

Locations below refer to the **baseline** and correspond to `results/before.json`.

| ID | Rule | Original location | Finding and impact |
|---|---|---|---|
| SA-01 | B006 | [`mkdocs/commands/serve.py:25`](../../mkdocs/commands/serve.py), `serve` | `watch=[]` creates one shared mutable default at function definition time. Future mutation could carry watch paths between invocations. |
| SA-02 | B006 | [`mkdocs/config/config_options.py:762,766,769`](../../mkdocs/config/config_options.py), `ListOfPaths.__init__` | The constructor and both overloads declare mutable list defaults. The implementation stores the supplied default on the option; removing the shared object makes ownership clearer. |
| SA-03 | B006 | [`mkdocs/config/config_options.py:971`](../../mkdocs/config/config_options.py), `MarkdownExtensions.__init__` | The default extension list is shared across constructor calls. A fresh list per option avoids retaining shared mutable constructor state. |
| SA-04 | B019 | [`mkdocs/config/config_options.py:1190`](../../mkdocs/config/config_options.py), `Hooks._load_hook` | An unbounded class-level method cache includes `self` in each key, retaining hook-option instances after callers release them. |
| SA-05 | B028 | [`mkdocs/structure/files.py:100`](../../mkdocs/structure/files.py), `Files.append` | The replacement deprecation warning reports a MkDocs source location, making the caller's deprecated usage harder to locate. |
| SA-06 | B028 | [`mkdocs/structure/pages.py:223`](../../mkdocs/structure/pages.py), `Page._set_title` | The legacy-method warning also points inside MkDocs instead of identifying the calling code. |
| SA-07 | B904 | [`mkdocs/structure/files.py:111`](../../mkdocs/structure/files.py), `Files.remove` | Translating `KeyError` into `ValueError` leaves the cause implicit. Explicit chaining documents the relationship for traceback readers and exception-inspection tools. |
| SA-08 | B904 | [`mkdocs/localization.py:42`](../../mkdocs/localization.py), `parse_locale` | Invalid locale exceptions are translated to `ValidationError` without explicitly setting the originating exception as the cause. |
| SA-09 | B904 | [`mkdocs/theme.py:136`](../../mkdocs/theme.py), `Theme._load_theme_config` | Theme-file read failures are translated to `ValidationError` without an explicit filesystem-error cause. |

Rule explanations: [mutable defaults (B006)](https://docs.astral.sh/ruff/rules/mutable-argument-default/),
[cached instance methods (B019)](https://docs.astral.sh/ruff/rules/cached-instance-method/),
[warning stack levels (B028)](https://docs.astral.sh/ruff/rules/no-explicit-stacklevel/),
and [exception chaining (B904)](https://docs.astral.sh/ruff/rules/raise-without-from-inside-except/).

## Fix summary

- **SA-01:** Changed `watch` to default to `None` and allocate an empty list
  inside `serve` when omitted.
- **SA-02 and SA-03:** Replaced list defaults with immutable empty tuples and
  copied supplied sequences into per-instance lists. `MarkdownExtensions` copies
  dictionary defaults as dictionaries so extension options are preserved.
  Explicit `default=None` retains its previous meaning. Both `ListOfPaths`
  overloads match the constructor.
- **SA-04:** Replaced the decorated method cache with an instance-owned module
  dictionary keyed by `(name, path)`. This removes the global reference to `self`
  while retaining module reuse across configuration reloads. The path remains
  part of the key so separate projects can use the same hook name.
- **SA-05 and SA-06:** Added `stacklevel=2` to attribute warnings to the caller.
- **SA-07 through SA-09:** Added `raise ... from e`, preserving the original
  exception as the explicit cause. Error types and messages remain the same;
  traceback presentation now identifies a direct cause.

### Analysis results

| Check | Before | After | Removed |
|---|---:|---:|---:|
| Extended production scan | 170 | 159 | 11 |
| B006, all occurrences in scope | 5 | 0 | 5 |
| B019, all occurrences in scope | 1 | 0 | 1 |
| B028, all occurrences in scope | 11 | 9 | 2 |
| B904, all occurrences in scope | 17 | 14 | 3 |
| Original repository-configured scan (`mkdocs docs`) | 0 | 0 | 0 |

All nine selected findings were addressed. The **159 remaining diagnostics**
include pathlib recommendations, control-flow suggestions, other warnings and
exception sites, and resource-management suggestions. They remain outside the
agreed fixes and require individual review; this assignment does not establish
that the entire application is free of defects.

Evidence: [`before.json`](results/before.json), [`after.json`](results/after.json),
[`configured-before.json`](results/configured-before.json), and
[`configured-after.json`](results/configured-after.json).

### Validation

| Check | Result | Evidence |
|---|---|---|
| Original unit suite, baseline | 725 tests, four skipped, no failures | [`tests-before.txt`](results/tests-before.txt) |
| Unit suite after initial fixes | 728 tests, four skipped, no failures | [`tests-after.txt`](results/tests-after.txt) |
| Final unit suite with documentation dependencies | 729 tests, four skipped, no failures | [`tests-after-docs.txt`](results/tests-after-docs.txt) |
| Hook-option retention regression before fix | Failed: released option was still alive | [`regressions-red.txt`](results/regressions-red.txt) |
| Hook tests after fix | Five tests pass, including three added tests | [`hooks-green.txt`](results/hooks-green.txt) |
| Mapping-default regression before review fix | Failed: extension options were discarded | [`mapping-default-red.txt`](results/mapping-default-red.txt) |
| Markdown extension tests after review fix | 17 tests pass, including the added mapping-default regression | [`markdown-extensions-green.txt`](results/markdown-extensions-green.txt) |
| Integration builds | Both built-in themes and all four fixture projects pass strict builds | [`integration-after.txt`](results/integration-after.txt) |
| Type checking | Mypy 1.8.0 passes all 61 source files | [`types-after.txt`](results/types-after.txt) |
| Formatting and import order | Black 23.12.1 and isort 5.13.2 checks pass for all seven changed Python files | [`style-after.txt`](results/style-after.txt) |

The three added tests in
[`config_options_tests.py`](../../mkdocs/tests/config/config_options_tests.py)
exercise hook-option garbage collection, module reuse across configuration
reloads, and distinct modules for identical names in different project paths.

Review of the initial PR commit (`f7be8f6`) also caught a regression in SA-03:
converting dictionary defaults into lists discarded extension options. The
follow-up fix preserves the dictionary and its values. A fourth added test
checks this through the resolved configuration's `markdown_extensions` and
`mdx_configs` values. This corrects the original SA-03 fix; the assignment still
contains nine logical findings.

An initial baseline using `pathspec 1.1.1` had two failing subtests in
`test_draft_docs_with_comments_from_user_guide` before production changes.
Changing only `pathspec` to **0.11.2**, the version pinned in the repository's
documentation requirements, made the original suite pass. The passing before
and after unit runs use that same version. The initial failures and environment
are retained in [`tests-before-latest.txt`](results/tests-before-latest.txt) and
[`environment-latest.txt`](results/environment-latest.txt). No dependency file
was changed as part of the fixes.

To reproduce the unit-test environment and run the suite:

```sh
TASK_ENV="$(mktemp -d)"
uv venv --python 3.12 "$TASK_ENV"
uv pip install --python "$TASK_ENV/bin/python" \
    -r courseProjectDocs/static-analysis/results/environment.txt
"$TASK_ENV/bin/python" -m unittest discover -s mkdocs -p '*tests.py'
```

For integration builds, install
[`environment-docs.txt`](results/environment-docs.txt) into another Python 3.12
environment and run the following. The environment includes the docs plugins
and the editable local MkDocs package. Installing the repository's docs
requirements alone would install MkDocs 1.5.3 instead of this checkout.

```sh
PATH="$TASK_ENV/bin:$PATH" "$TASK_ENV/bin/python" -m mkdocs.tests.integration
```

For type checking, install [`environment-types.txt`](results/environment-types.txt)
and run `mypy mkdocs`. Freeze files use `-e .` for the editable package so they
can be installed from another checkout's root. Validation was performed on
Python 3.12; the fixes retain Python 3.8-compatible syntax with postponed
annotations and introduce no newer runtime APIs. Other supported interpreters
were not executed for this assignment.

## Group Contributions

Each team member identified three code smells and fixed their findings, for a
total of nine logical fixes. The work used AI assistance for analysis,
implementation, validation, and report preparation.

| Team member | Findings identified and fixed | Contribution |
|---|---|---|
| [Godson Umoren (@KayUmoren004)](https://github.com/KayUmoren004) | SA-01, SA-02, SA-03 | Removed shared mutable defaults from `serve`, `ListOfPaths`, and `MarkdownExtensions`, including the constructor overloads. |
| [Ty Carpenter (@tjc7058)](https://github.com/tjc7058) | SA-04, SA-05, SA-06 | Replaced the instance-retaining hook cache and corrected warning attribution in `Files.append` and `Page._set_title`. |
| [Hiroto Takeuchi (@hiromon0125)](https://github.com/hiromon0125) | SA-07, SA-08, SA-09 | Added explicit exception causes in `Files.remove`, `parse_locale`, and `Theme._load_theme_config`. |
