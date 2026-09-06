# Cyclomatic Complexity Report: mkdocs

Tool: `radon cc` (via `uvx radon cc -s -a --total-average mkdocs/`). Scope: every `.py` under `mkdocs/`, split into production code and `mkdocs/tests/`.
CC = decision points + 1 (`if`, `elif`, loops, `except`, boolean operators in conditions, comprehensions).
No project linter sets a complexity threshold, so default thresholds are used: 1-5 fine, 6-10 watch, 11-15 refactor now, 16+ must split.

Raw per-block output: `cyclomatic_complexity_raw.txt`.

## Summary

| | Functions/methods | Avg CC | Max CC | CC 1-5 | CC 6-10 | CC 11-15 | CC 16+ |
|---|---|---|---|---|---|---|---|
| Production | 453 | 2.83 | 32 | 398 | 39 | 12 | 4 |
| Test | 798 | 1.23 | 12 | 794 | 3 | 1 | 0 |

All 1392 blocks (classes included) average CC 1.81; radon grades the codebase **A** overall.

## Production hotspots (CC >= 11)

| CC | Rating | Function | Location | Lines |
|---|---|---|---|---|
| 32 | must split | `_RelativePathTreeprocessor.path_to_url` | `mkdocs/structure/pages.py:419` | 98 |
| 24 | must split | `build` | `mkdocs/commands/build.py:249` | 116 |
| 21 | must split | `Plugins.load_plugin` | `mkdocs/config/config_options.py:1105` | 61 |
| 16 | must split | `Theme.run_validation` | `mkdocs/config/config_options.py:819` | 40 |
| 15 | refactor now | `_data_to_navigation` | `mkdocs/structure/nav.py:188` | 36 |
| 14 | refactor now | `get_navigation` | `mkdocs/structure/nav.py:130` | 56 |
| 13 | refactor now | `RepoURL.post_validation` | `mkdocs/config/config_options.py:576` | 29 |
| 13 | refactor now | `Page._set_edit_url` | `mkdocs/structure/pages.py:171` | 36 |
| 13 | refactor now | `_RelativePathTreeprocessor._possible_target_uris` | `mkdocs/structure/pages.py:382` | 36 |
| 12 | refactor now | `load_config` | `mkdocs/config/base.py:340` | 53 |
| 12 | refactor now | `ListOfItems.run_validation` | `mkdocs/config/config_options.py:211` | 31 |
| 12 | refactor now | `DictOfItems.run_validation` | `mkdocs/config/config_options.py:266` | 33 |
| 12 | refactor now | `MarkdownExtensions.run_validation` | `mkdocs/config/config_options.py:993` | 42 |
| 12 | refactor now | `LiveReloadServer._serve_request` | `mkdocs/livereload/__init__.py:264` | 62 |
| 11 | refactor now | `Nav.run_validation` | `mkdocs/config/config_options.py:868` | 16 |
| 11 | refactor now | `SearchPlugin.on_post_build` | `mkdocs/contrib/search/__init__.py:95` | 26 |

## Production watch list (CC 6-10)

| CC | Function | Location |
|---|---|---|
| 10 | `serve` | `mkdocs/commands/serve.py:20` |
| 10 | `_open_config_file` | `mkdocs/config/base.py:290` |
| 10 | `get_themes` | `mkdocs/utils/__init__.py:263` |
| 10 | `get_data` | `mkdocs/utils/meta.py:56` |
| 9 | `gh_deploy` | `mkdocs/commands/gh_deploy.py:100` |
| 9 | `set_exclusions` | `mkdocs/structure/files.py:527` |
| 9 | `get_files` | `mkdocs/structure/files.py:546` |
| 9 | `Page.validate_anchor_links` | `mkdocs/structure/pages.py:304` |
| 8 | `_build_page` | `mkdocs/commands/build.py:185` |
| 8 | `PropagatingSubConfig.run_validation` | `mkdocs/config/config_options.py:132` |
| 8 | `IpAddress.run_validation` | `mkdocs/config/config_options.py:470` |
| 8 | `URL.run_validation` | `mkdocs/config/config_options.py:511` |
| 8 | `EditURI.post_validation` | `mkdocs/config/config_options.py:612` |
| 8 | `Plugins._parse_configs` | `mkdocs/config/config_options.py:1069` |
| 8 | `Plugins.load_plugin_with_namespace` | `mkdocs/config/config_options.py:1088` |
| 8 | `LangOption.run_validation` | `mkdocs/contrib/search/__init__.py:34` |
| 8 | `LiveReloadServer._build_loop` | `mkdocs/livereload/__init__.py:192` |
| 8 | `PluginCollection._register_event` | `mkdocs/plugins.py:509` |
| 8 | `Page.title` | `mkdocs/structure/pages.py:228` |
| 8 | `_replace_elements_with_text` | `mkdocs/utils/rendering.py:89` |
| 7 | `_populate_page` | `mkdocs/commands/build.py:147` |
| 7 | `SubConfig.__init__` | `mkdocs/config/config_options.py:83` |
| 7 | `Deprecated.pre_validation` | `mkdocs/config/config_options.py:421` |
| 7 | `_get_merged_translations` | `mkdocs/localization.py:66` |
| 7 | `File.copy_file` | `mkdocs/structure/files.py:473` |
| 7 | `_get_norm_url` | `mkdocs/utils/__init__.py:220` |
| 7 | `yaml_load` | `mkdocs/utils/yaml.py:128` |
| 6 | `_showwarning` | `mkdocs/__main__.py:28` |
| 6 | `callback` | `mkdocs/__main__.py:196` |
| 6 | `_build_theme_template` | `mkdocs/commands/build.py:91` |
| 6 | `Config.__init__` | `mkdocs/config/base.py:158` |
| 6 | `Choice.__init__` | `mkdocs/config/config_options.py:364` |
| 6 | `RepoName.post_validation` | `mkdocs/config/config_options.py:671` |
| 6 | `SearchPlugin.on_config` | `mkdocs/contrib/search/__init__.py:65` |
| 6 | `SearchIndex.generate_search_index` | `mkdocs/contrib/search/search_index.py:95` |
| 6 | `LiveReloadServer.serve_request` | `mkdocs/livereload/__init__.py:240` |
| 6 | `_filter_paths` | `mkdocs/structure/files.py:613` |
| 6 | `get_relative_url` | `mkdocs/utils/__init__.py:177` |
| 6 | `_construct_dir_placeholder` | `mkdocs/utils/yaml.py:22` |

## Test code (CC >= 6)

| CC | Function | Location |
|---|---|---|
| 12 | `BuildTests.test_plugins_adding_files_and_interacting` | `mkdocs/tests/build_tests.py:815` |
| 8 | `BuildTests._assert_build_logs` | `mkdocs/tests/build_tests.py:562` |
| 8 | `RelativePathExtensionTests.get_rendered_result` | `mkdocs/tests/structure/page_tests.py:773` |
| 6 | `load_config` | `mkdocs/tests/base.py:26` |

## Per-file (production)

| File | Functions | Avg CC | Max CC | CC > 10 |
|---|---|---|---|---|
| `mkdocs/structure/pages.py` | 31 | 4.26 | 32 | 3 |
| `mkdocs/commands/build.py` | 8 | 7.38 | 24 | 1 |
| `mkdocs/config/config_options.py` | 91 | 3.30 | 21 | 7 |
| `mkdocs/structure/nav.py` | 16 | 3.50 | 15 | 2 |
| `mkdocs/config/base.py` | 29 | 2.83 | 12 | 1 |
| `mkdocs/livereload/__init__.py` | 20 | 3.10 | 12 | 1 |
| `mkdocs/contrib/search/__init__.py` | 6 | 5.00 | 11 | 1 |
| `mkdocs/commands/serve.py` | 4 | 4.25 | 10 | 0 |
| `mkdocs/utils/__init__.py` | 32 | 2.59 | 10 | 0 |
| `mkdocs/utils/meta.py` | 1 | 10.00 | 10 | 0 |
| `mkdocs/commands/gh_deploy.py` | 5 | 4.20 | 9 | 0 |
| `mkdocs/structure/files.py` | 58 | 2.40 | 9 | 0 |
| `mkdocs/plugins.py` | 57 | 1.40 | 8 | 0 |
| `mkdocs/utils/rendering.py` | 9 | 3.33 | 8 | 0 |
| `mkdocs/localization.py` | 4 | 3.50 | 7 | 0 |
| `mkdocs/utils/yaml.py` | 11 | 2.27 | 7 | 0 |
| `mkdocs/__main__.py` | 19 | 2.00 | 6 | 0 |
| `mkdocs/contrib/search/search_index.py` | 13 | 2.77 | 6 | 0 |
| `mkdocs/commands/new.py` | 1 | 5.00 | 5 | 0 |
| `mkdocs/theme.py` | 13 | 1.62 | 5 | 0 |
| `mkdocs/utils/babel_stub.py` | 2 | 3.50 | 5 | 0 |
| `mkdocs/utils/templates.py` | 2 | 3.00 | 5 | 0 |
| `mkdocs/config/defaults.py` | 4 | 1.75 | 3 | 0 |
| `mkdocs/structure/toc.py` | 10 | 1.50 | 3 | 0 |
| `mkdocs/structure/__init__.py` | 4 | 1.25 | 2 | 0 |
| `mkdocs/exceptions.py` | 1 | 1.00 | 1 | 0 |
| `mkdocs/utils/cache.py` | 2 | 1.00 | 1 | 0 |
