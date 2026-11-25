# Reproducing the performance tests

Run commands from the repository root. Docker Engine/Docker Desktop, Compose supporting `healthcheck.start_interval` (recorded version: 5.7.1), and Python 3.8+ on the host are required. The host Python only orchestrates Docker; MkDocs, Locust, psutil, and plotting dependencies run inside the image. Allow at least 4 CPUs and 3 GiB RAM in the Docker VM, keep other workloads quiet, and use the same machine/VM settings for comparisons.

## Full benchmark

```sh
python3 courseProjectCode/performance-testing/run-suite.py --label baseline
```

This builds the image, runs load, stress, and spike testing three times each, and stops its containers after each run. The default run takes about 20–25 minutes. Each repetition rotates the test order. MkDocs starts fresh before every run, and each profile begins with an excluded 10-second warmup. Labels must be unique: use `--label baseline-2` for another campaign. The runner refuses to overwrite completed results.

The benchmark installs **this checkout of MkDocs**, rather than downloading MkDocs from PyPI. The base Python 3.12.12 image is pinned by digest and all Python dependencies are pinned in [`requirements.txt`](../../courseProjectCode/performance-testing/requirements.txt). The generated fixture lives in the container filesystem, avoiding host source-mount performance differences. No production application source is changed.

Generate the summaries and charts after the campaign finishes:

```sh
docker compose -p mkdocs-perf -f courseProjectCode/performance-testing/compose.yaml run --rm --no-deps runner python analyze.py --label baseline
python3 courseProjectCode/performance-testing/supplementary.py --label baseline
docker compose -p mkdocs-perf -f courseProjectCode/performance-testing/compose.yaml down --remove-orphans
```

`results/baseline-summary.md` lists every measured phase of every run. `results/baseline-summary.json` contains the same statistics with endpoint breakdowns. Each run directory contains its own chart and Locust HTML report. Changing the label requires changing it in the analysis command too. The checked-in report documents the recorded campaign; rerunning produces new measurements and does not rewrite the report narrative.

## Individual profiles and short pilot

```sh
# Only spike testing, repeated three times:
python3 courseProjectCode/performance-testing/run-suite.py --types spike --label spike-only

# Short functional pilot: every duration is 10% of the real benchmark.
python3 courseProjectCode/performance-testing/run-suite.py --label pilot-2 --scale 0.1 --repeats 1

# Reuse the already-built image only when the checkout/harness has not changed:
python3 courseProjectCode/performance-testing/run-suite.py --label repeat --skip-build
```

The pilot verifies orchestration, endpoint availability, user transitions, resource sampling, and output generation. Its short phases are **not** evidence of sustained performance. Scaling duration also inversely scales spawn rate, preserving the intended user targets. The pilot in `results/pilot-*` is retained separately from the full results.

## Workload and configuration

[`profiles.json`](../../courseProjectCode/performance-testing/profiles.json) defines all phase durations, targets, and spawn rates. [`locustfile.py`](../../courseProjectCode/performance-testing/locustfile.py) supplies the same HTTP workload for all three profiles:

- Homepage: weight 3.
- One of 20 generated documentation pages: weight 5.
- Theme CSS: weight 1.
- Generated search index: weight 1.

Each virtual user waits 0.1 seconds after a request. This is a closed workload: users wait for a response before issuing their next request, so user count is not a fixed arrival rate. A virtual user is an HTTP client, not a browser; JavaScript, rendering, and automatic asset downloads are not simulated. Request choices are seeded (`777 + repetition`), but scheduling and timings are naturally variable. Every response must have HTTP 200 and a nonempty body. Connection/read timeouts are 2/5 seconds, and retries are disabled.

| Profile | Phases after warmup | Total including warmup |
|---|---|---:|
| Load | 10 users for 60 s | 70 s |
| Stress | 10 → 25 → 50 → 100 → 200 → 400, 30 s per stage; 10-user recovery for 30 s | 220 s |
| Spike | 10 users for 30 s → 100 for 15 s → 10 for 45 s | 100 s |

The stress stage's first roughly 3–5 seconds include its gradual transition; the remaining time is a plateau. The spike uses a 400-users/s spawn rate, creating its increase within approximately one scheduler tick. Actual observed users are saved alongside targets. In-flight requests can delay ramp-down by up to the 5-second stop timeout. Locust's warning about high spawn rates is expected for the deliberate spike; CPU saturation warnings require investigation.

Change parameters before rebuilding if another configuration is needed. Record the changed configuration with a fresh label; never combine results from different configurations as repeats of one test. There is no production SLO or expected user count for this development server: ten users is an experimental baseline, and 400 users is the bounded stress ceiling. A separate wall-clock timeout terminates a stalled profile. HTTP failures are retained as test results; user-code exceptions and incomplete runs fail the suite.

## Container limits and measurement

[`compose.yaml`](../../courseProjectCode/performance-testing/compose.yaml) gives MkDocs 1 CPU and 512 MiB RAM; Locust gets 2 CPUs and 1 GiB RAM. Swap is disabled for both, and PID limits bound runaway thread creation. Only the benchmark containers are managed under Compose project `mkdocs-perf`; no host port is published. Both services communicate over a private internal network. Avoid running two campaigns simultaneously with that project name.

Locust runs a master and **two worker processes** inside the generator container. A single Python worker can be limited by one CPU even with a larger container quota; the second worker distributes traffic generation across the allocated CPUs. Per-worker logs are merged only after measurement, and native worker counters independently validate request/failure totals. Worker seeds are the repetition seed plus worker index. Each request preserves its worker's exact user count; aggregate `users` adds the other worker's most recent user-count sample, collected nominally every 0.25 seconds. Aggregate counts therefore have sampling uncertainty during transitions. The worker sample files are retained for inspection.

[`monitor.py`](../../courseProjectCode/performance-testing/monitor.py) samples each child process tree every second using psutil. It also records the sampler's own usage, thread count, cgroup memory, and cumulative CPU throttling. The samplers share their respective container quotas, but their own CPU/RSS are excluded from the reported MkDocs/Locust process totals. Container-level cgroup measurements include sampler overhead.

- CPU **100% means one logical CPU** occupied, so MkDocs has a nominal 100% ceiling and Locust a nominal 200% ceiling. Individual one-second samples can slightly exceed these ceilings because of quota periods and sampling boundaries.
- `max_process_cpu_percent` also tracks the busiest individual process. Check this and Locust's CPU warnings: a worker can approach its single-core limit before the aggregate generator reaches its two-CPU container ceiling.
- Memory charts show process-tree RSS in MiB, not host RAM or Docker VM usage. Shared pages can be counted more than once when summing processes; cgroup memory is retained separately.
- Phase percentiles are computed from raw request durations with NumPy's linear interpolation, not averaged from time-window percentiles. Charts show p95 and successful completions in one-second buckets.
- Charts include shutdown completions and a potentially partial final request bucket. End-of-chart drops or spikes are shutdown effects; use the measured phase tables for performance comparisons.
- Requests belong to their **completion phase**, including those that started in an earlier phase. Post-profile completions are labeled `drain`, saved, and excluded from measured phase tables. Warmup is retained in raw data and charts but excluded from reported phase summaries.
- User reductions can cancel in-flight requests after the stop timeout. Requests aborted without a completion event are absent from latency/error totals; the saved figures describe completed requests.
- CPU averages and peak RSS use samples timestamped inside each phase. Each CPU sample represents the preceding approximately one-second interval, so phase boundaries have about one second of measurement uncertainty.
- Built-in Locust totals include warmup/drain and its rounded percentile buckets; the phase summary is the source for the report's phase-specific numbers.
- Native CSV snapshots can also precede final shutdown completions. `locust-final.json` sums independently accumulated native worker counters after shutdown; those totals must match the merged raw request log.

Containers standardize software and resource ceilings; they cannot eliminate host CPU speed, VM scheduling, shared-host contention, kernel, or architecture effects. Record those conditions and compare runs on the same host. A CPU quota is a ceiling, not a reservation. Monitor the generator as well: its saturation can prevent a workload from reaching the intended stress level. Results describe MkDocs's local development HTTP server with live reload disabled, not production static-site hosting or documentation build speed.

## Saved evidence

| Artifact | Purpose |
|---|---|
| `results/<label>-suite.json` | Source commit, source/harness hashes, image ID, Docker VM capacity, Compose version, completed run IDs |
| `<run>/metadata.json`, `timing.json` | Python/tool versions, effective generator cgroup limits, seed, schedule and timestamps |
| `<run>/container-limits.json` | App limits read back from Docker, rather than just declared settings |
| `<run>/fixture-manifest.json`, `environment.txt` | Fixture file hashes and installed dependency versions |
| `<run>/requests.csv.gz` | Every completed request: elapsed time, phase, sampled aggregate/target users, worker-local users, endpoint, latency, bytes, success/error |
| `<run>/worker-*-users.csv`, `worker-*-final.json`, `locust-final.json` | Worker user-count samples and independently checked native request/failure counters |
| `<run>/app-resources.csv`, `generator-resources.csv` | CPU, RSS, threads, sampler overhead, cgroup memory/throttling over time |
| `<run>/locust*.csv`, `locust.html`, `locust.log` | Native tool reports, failure details, history and execution log |
| `<run>/app.log` | Server startup, shutdown and error messages |
| `<run>/summary.json`, `timeseries.png` | Derived phase/endpoint metrics and the five-panel chart |
| `assignments.json` | One-time random assignment and commit-identity mapping |

Team ownership was randomly assigned once after matching the fork's recent/coursework commit identities with the project roster. The assignment is retained when reproducing tests; it does not rerandomize on every run.

To deliberately refresh dependencies, use `uv pip compile` with the root `pyproject.toml` and `courseProjectCode/performance-testing/requirements.in`, targeting Python 3.12 on Linux. Review and commit the resulting lock changes, rebuild, and use a new campaign label. Dependency upgrades change the tested software environment.
