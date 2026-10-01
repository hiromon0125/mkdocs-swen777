# Unit Testing II — Mocking `serve()`

## Scope

The three new tests in [`unit_testing2_mocking_tests.py`](../../courseProjectCode/Unit-Testing/unit_testing2_mocking_tests.py) exercise `mkdocs.commands.serve.serve()`. The real `serve()` function is called, but its external dependencies are replaced with mocks so the tests do not start a web server, wait for file changes, or perform a full documentation build.

The tests use Python's built-in `unittest` framework and `unittest.mock.MagicMock`. No production code was changed.

## Mocking strategy

The dependencies used by `serve()` were mocked so the tests focus on the function's control flow. The real `serve()` function still runs, but the mocks prevent it from starting a network server, performing a full build, or deleting the test fixture.

1. `LiveReloadServer`: Prevents a real development server from opening a port and running indefinitely. The mock records calls to `serve()`, `watch()`, and `shutdown()` so the tests can verify how `serve()` controls the server.
2. `build`: Prevents each unit test from performing a complete MkDocs build while still allowing the call to `build()` to occur inside `serve()`.
3. `load_config`: Returns a controlled configuration with known documentation, configuration, theme, and extra watch paths.
4. `tempfile.mkdtemp`: Returns a predictable temporary site directory owned by the test fixture.
5. `shutil.rmtree`: Prevents `serve()` from deleting the test fixture before `tearDown()` cleans it up.

`LiveReloadServer` is the main test double because it replaces the long-running network component. `MagicMock` records each method call, which allows the tests to check that the server is started, given the correct watch paths, and shut down. The other mocks provide controlled inputs and remove unrelated file and build behavior from the unit under test.

## New test cases & rationale

1. `test_serve_starts_and_shuts_down_server`: Calls `serve()` with live reload disabled and verifies that the server receives the requested browser option. It also verifies that the server and plugins are shut down. This tests the normal lifecycle without starting a real web server.
2. `test_serve_registers_watch_paths_when_livereload_is_enabled`: Calls `serve()` with live reload and theme watching enabled. It verifies that the documentation directory, configuration file, theme directory, and extra user path are registered with the server. This tests the main live-reload branch and confirms that every type of watch path is included.
3. `test_serve_shuts_down_after_keyboard_interrupt`: Configures the mocked server to raise `KeyboardInterrupt`, representing the user pressing Ctrl+C. It verifies that server and plugin shutdown still occur. This tests the interruption path and guards against leaving server resources open.

Together, these cases test normal startup, live-reload configuration, and
cleanup after an interruption. They also exercise both the enabled and disabled
outcomes of the live-reload condition.

## Test results

| Suite | Tests run | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|---:|
| Existing MkDocs suite | 725 | 721 | 0 | 0 | 4 |
| Unit Testing I additions | 15 | 15 | 0 | 0 | 0 |
| New mocking tests | 3 | 3 | 0 | 0 | 0 |
All three new mocking tests passed.

## Coverage improvement analysis

Both measurements below were produced on the same machine with branch coverage enabled. The before measurement includes the existing MkDocs suite and the 15 Unit Testing I tests. The after measurement adds only the three new mocking tests.

1. Covered statements increased by 39, giving a new total of 3,379 out of 3,643 statements.
2. Statement coverage increased by 1.07 percentage points, giving a new score of 92.75%.
3. Covered branch outcomes increased by 10, giving a new total of 947 out of 1,098 branch outcomes.
4. Branch coverage increased by 0.91 percentage points, giving a new score of 86.25%.
5. Combined coverage increased by 1.03 percentage points, giving a new score of 91.25%.

### `mkdocs/commands/serve.py` improvement

1. Covered statements increased by 39, giving a new total of 51 out of 59 statements.
2. Statement coverage increased by 66.10 percentage points, giving a new score of 86.44%.
3. Covered branch outcomes increased by 10, giving a new total of 10 out of 18 branch outcomes.
4. Branch coverage increased by 55.56 percentage points, giving a new score of 55.56%.
5. Combined coverage shown by coverage.py increased by 63 percentage points, giving a new score of 79%.

The new tests are responsible for the 39 additional statements and 10
additional branch outcomes because the before and after reports were generated
in the same environment and differ only by the three mocking tests.

The largest change is in `mkdocs/commands/serve.py`. Its displayed combined
coverage increased from 16% to 79%. Statement coverage rose by 66.10 percentage
points because the tests now execute server creation, the initial build call,
watch registration, normal shutdown, interrupted shutdown, plugin shutdown, and
temporary-directory cleanup. Branch coverage rose from 0.00% to 55.56% because
the tests exercise live reload as both enabled and disabled, enable theme
watching, provide a configuration file path, and trigger `KeyboardInterrupt`.

Overall project coverage increased by 1.03 percentage points. This project-wide
change is smaller than the change in `serve.py` because `serve.py` contains only
59 of the project's 3,643 statements. The results still show that the new tests
targeted a previously under-tested component and covered meaningful behavior
rather than repeating paths already exercised by the existing suite.

The complete text report is available in
[`mockingCoverageReport.txt`](testCoverage/mockingCoverageReport.txt). Exact
machine-readable before and after results are stored in
[`mockingBaselineCoverage.json`](testCoverage/mockingBaselineCoverage.json) and
[`mockingCoverage.json`](testCoverage/mockingCoverage.json).

