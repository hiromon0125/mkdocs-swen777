# Integration Testing Report

## Test design summary

MkDocs already has one integration check, `mkdocs/tests/integration.py`. It builds a few sample projects and passes as long as each build finishes without errors. It doesn't look at what the build produced. Our tests fill that gap: each one runs a real chain of MkDocs modules and checks that the right data comes out at the end.

All three areas run the real site build. The only things replaced with fakes are the steps that would run git or push to GitHub.

| Area | Modules integrated | What we tested |
|---|---|---|
| `mkdocs gh-deploy` command | Command line (`mkdocs.__main__`) → `mkdocs.config` → `mkdocs.commands.build` → `mkdocs.commands.gh_deploy` → `ghp_import` (push, faked) | The options typed on the command line reach the push step, and the site is fully built before it is pushed. A failed push makes the command report an error. |
| Page titles | `mkdocs.config` → `mkdocs.commands.build` → `mkdocs.structure.files` / `pages` → `mkdocs.utils.meta` → `mkdocs.structure.nav` → theme | A title set in the settings block at the top of a page shows up as the page's name in the nav bar and browser tab. A broken block is handled without breaking the build. |
| Sidebar (table of contents) | `mkdocs.config` → `mkdocs.commands.build` → `mkdocs.structure.pages` → Markdown `toc` extension → `mkdocs.structure.toc` → theme | The links in a page's sidebar point to the right headings on the page, even when two headings have the same name. A page with no headings builds with an empty sidebar. |

### Test cases

| File | Test | Type | What it checks |
|---|---|---|---|
| `integration_gh_deploy_tests.py` | `test_builds_site_and_passes_cli_options_to_ghp_import` | Normal | Runs `mkdocs gh-deploy` with `--remote-branch`, `--remote-name`, `--message`, `--force` and `--ignore-version`. The push is called once, with the built site folder and exactly those settings. At the moment of the push, the site already contains the built pages. The version check is skipped. |
| `integration_gh_deploy_tests.py` | `test_push_failure_aborts_command_after_site_is_built` | Failure | The push fails. The command exits with code 1 and "Deployment Aborted!", and the site that was built before the push is still there. |
| `integration_meta_tests.py` | `test_title_block_sets_page_title_in_nav_and_tab` | Normal | A page starting with `title: Custom Title` in its settings block shows "Custom Title" in the nav bar and browser tab, and the settings block is not shown on the page. |
| `integration_meta_tests.py` | `test_invalid_title_block_is_shown_as_content_without_warning` | Edge | The settings block is not valid YAML (`title: [unclosed`). Reproduces BUG-1 below. |
| `integration_toc_tests.py` | `test_sidebar_links_match_heading_ids` | Normal | A page with two `## Setup` headings gets different anchors for them (`setup` and `setup_1`), and every sidebar link points to a heading on the page. |
| `integration_toc_tests.py` | `test_page_without_headings_has_empty_table_of_contents` | Edge | A page with no headings builds normally and has no sidebar links. |

## Test data preparation

- **Created by each test.** Each test writes a small MkDocs project (a `mkdocs.yml` and one or two Markdown pages) into a new temporary folder, builds it with the real build command, and reads the HTML files it produces. The folder is deleted after the test. No data files are stored in the repository.
- **Written by hand.** The Markdown for each page is a short string in the test, chosen to hit one interaction: a title in the settings block, an invalid settings block, duplicate headings, or no headings. The site name in `mkdocs.yml` is set by the test, so the expected browser-tab title is known.
- **Expected results.** Expected values come from MkDocs' documented behavior. For example, a title in the settings block overrides the page's heading, and duplicate headings get `_1`, `_2` added to their anchors. We confirmed them by building the same inputs and looking at the HTML. Tests check only the relevant parts of the HTML (the browser-tab title, the nav bar, the sidebar links and the heading anchors), not whole files, so unrelated theme changes don't break them.
- **Faked values (`gh-deploy` tests only).** The git helper functions return fixed answers: "this is a git repo", commit `abc1234`, and the remote `https://github.com/user/project.git`. The push to GitHub is replaced with a fake that records what it was given and looks at the site folder at the moment of the push. In the failure test, the fake push raises an error instead, as if GitHub rejected the push.

## Execution and results

Command, run from the repository root:

```sh
python -m unittest discover -s courseProjectCode/integration-testing -p "integration_*_tests.py" -v
```

All 6 tests passed (Windows, run in 0.851 s):

```
Ran 6 tests in 0.851s

OK
```

| File | Test | Type | Result |
| --- | --- | --- | --- |
| `integration_gh_deploy_tests.py` | `test_builds_site_and_passes_cli_options_to_ghp_import` | Normal | Pass |
| `integration_gh_deploy_tests.py` | `test_push_failure_aborts_command_after_site_is_built` | Failure | Pass |
| `integration_meta_tests.py` | `test_title_block_sets_page_title_in_nav_and_tab` | Normal | Pass |
| `integration_meta_tests.py` | `test_invalid_title_block_is_shown_as_content_without_warning` | Edge | Pass |
| `integration_toc_tests.py` | `test_sidebar_links_match_heading_ids` | Normal | Pass |
| `integration_toc_tests.py` | `test_page_without_headings_has_empty_table_of_contents` | Edge | Pass |

**Defects found:** one, BUG-1 (below). Its test passes because it is written to confirm the bug happens. If MkDocs fixes the bug, that test will fail and should be updated.

## Bug reports

### BUG-1: An invalid settings block is silently shown as page content and hides the page title

We wrote an integration test, `test_invalid_title_block_is_shown_as_content_without_warning`, that reproduces this bug. It builds a page with a broken settings block and checks for the problems listed under **Actual** below. The test documents the bug but does not fix it.

| Field | Value |
|---|---|
| Severity | Low to medium. The build succeeds, but the page shows the wrong title and stray text, and nothing tells the author why. |
| Found by | `test_invalid_title_block_is_shown_as_content_without_warning` |
| Modules involved | `mkdocs.utils.meta`, `mkdocs.structure.pages`, `mkdocs.structure.toc`, theme |
| Status | Reproduced and documented. Not fixed in this assignment, and not reported to the MkDocs project. |

**Steps to reproduce.** Build a site with a page `guide.md` containing:

```markdown
---
title: [unclosed
---

# Fallback Heading
```

`[unclosed` is missing its closing `]`, so the settings block is not valid YAML.

**Expected.** MkDocs warns that it couldn't read the settings block. Even if it ignores the block, the page's own `# Fallback Heading` is used as its title.

**Actual.**
1. **No warning or error is shown.** The build succeeds silently.
2. **The broken settings block is shown on the page.** The first `---` becomes a horizontal line, and `title: [unclosed` with the `---` below it becomes a heading.
3. **That broken line also appears in the page's sidebar.**
4. **The page's title becomes "Guide", from the filename.** The `# Fallback Heading` is ignored.

**Cause.** Two modules interact:
- `mkdocs/utils/meta.py`, `get_data()`: when the settings block can't be read, it catches the error with `except Exception` and treats the whole block as normal page text, without logging anything.
- `mkdocs/structure/pages.py`, `_ExtractTitleTreeprocessor.run()`: only checks the *first* element of the page for a `#` heading. The leftover `---` is now first, so the real heading is never seen.

Each module behaves reasonably on its own. The problem only shows up when they work together in a real build, which is why unit tests of either module alone don't catch it.

**Suggested fix.** Log a warning in `get_data()` when a page starts with a settings block that isn't valid YAML, naming the page. Optionally, remove the broken block so it isn't shown on the page.

## Group contributions

As a team, we discussed the assignment and decided which areas to target: the `gh-deploy` command, page titles, and the sidebar. We then split the coding work so that each member wrote the integration tests for one area, with one normal and one failure or edge case each.

| Member | File | Area | Tests |
| --- | --- | --- | --- |
| Ty Carpenter | `integration_gh_deploy_tests.py` | `gh-deploy` command | 2 (1 normal, 1 failure) |
| Godson Umoren | `integration_meta_tests.py` | Page titles | 2 (1 normal, 1 edge) |
| Hiroto Takeuchi | `integration_toc_tests.py` | Sidebar (table of contents) | 2 (1 normal, 1 edge) |
