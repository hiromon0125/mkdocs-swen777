"""One HTTP workload; profiles.json controls load, stress, and spike shapes."""
import csv
import json
import os
import random
import time
from pathlib import Path

import locust.stats
import gevent
from locust import FastHttpUser, LoadTestShape, constant, events, task
from locust.runners import MasterRunner

locust.stats.CSV_STATS_INTERVAL_SEC = 1
locust.stats.CSV_STATS_FLUSH_INTERVAL_SEC = 1
PROFILE = os.environ["TEST_TYPE"]
SCALE = float(os.environ.get("DURATION_SCALE", "1"))
STAGES = json.loads(Path("/bench/profiles.json").read_text())[PROFILE]
OUTPUT = Path("/results") / os.environ["RUN_ID"]
START = 0.0
STREAM = None
WRITER = None
USER_STREAM = None
USER_SAMPLER = None
WORKER_INDEX = None
REPORTED_NATIVE = {"requests": 0, "failures": 0}
random.seed(int(os.environ.get("PERF_SEED", "777")))


def stage_at(elapsed):
    boundary = 0
    for stage in STAGES:
        boundary += stage["seconds"] * SCALE
        if elapsed < boundary:
            return stage
    return None


class DocumentationReader(FastHttpUser):
    wait_time = constant(0.1)
    connection_timeout = 2.0
    network_timeout = 5.0
    max_retries = 0

    def fetch(self, path, name):
        with self.client.get(path, name=name, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(str(response.error) if response.status_code == 0 else f"HTTP {response.status_code}")
            elif not response.content:
                response.failure("empty body")

    @task(3)
    def home(self):
        self.fetch("/", "homepage")

    @task(5)
    def document(self):
        self.fetch(f"/page-{random.randrange(20):02d}/", "document")

    @task(1)
    def stylesheet(self):
        self.fetch("/css/base.css", "stylesheet")

    @task(1)
    def search_index(self):
        self.fetch("/search/search_index.json", "search-index")


class PerformanceShape(LoadTestShape):
    def tick(self):
        stage = stage_at(self.get_run_time())
        if stage is None:
            return None
        # Scale the spawn rate too, so short smoke tests still reach each target.
        return stage["users"], stage["spawn_rate"] / SCALE


@events.test_start.add_listener
def start(environment, **kwargs):
    global START, STREAM, WRITER, USER_STREAM, USER_SAMPLER, WORKER_INDEX
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if isinstance(environment.runner, MasterRunner):
        START = time.time()
        (OUTPUT / "timing.json").write_text(json.dumps({
            "started_at": START, "profile": PROFILE, "duration_scale": SCALE,
            "seed": os.environ.get("PERF_SEED", "777"), "stages": STAGES,
            "wait_seconds": 0.1, "connection_timeout_seconds": 2,
            "network_timeout_seconds": 5, "workers": 2,
        }, indent=2) + "\n")
        return
    START = json.loads((OUTPUT / "timing.json").read_text())["started_at"]
    for index in [1, 2]:
        try:
            with (OUTPUT / f"worker-{index}.lock").open("x"):
                pass
            WORKER_INDEX = index
            break
        except FileExistsError:
            continue
    if WORKER_INDEX is None:
        raise RuntimeError("unexpected additional worker")
    random.seed(int(os.environ.get("PERF_SEED", "777")) + WORKER_INDEX)
    STREAM = (OUTPUT / f"worker-{WORKER_INDEX}-requests.csv").open("w", newline="")
    WRITER = csv.writer(STREAM)
    WRITER.writerow(["timestamp", "elapsed_s", "phase", "users", "target_users", "endpoint",
                     "response_ms", "bytes", "success", "error", "worker"])
    USER_STREAM = (OUTPUT / f"worker-{WORKER_INDEX}-users.csv").open("w", newline="")
    user_writer = csv.writer(USER_STREAM)
    user_writer.writerow(["timestamp", "users"])

    def sample_users():
        while True:
            user_writer.writerow([f"{time.time():.6f}", environment.runner.user_count])
            USER_STREAM.flush()
            gevent.sleep(0.25)

    USER_SAMPLER = gevent.spawn(sample_users)


@events.request.add_listener
def record(request_type, name, response_time, response_length, exception, **kwargs):
    if WRITER is None:
        return
    now = time.time()
    elapsed = now - START
    stage = stage_at(elapsed)
    # Shutdown requests are retained and labeled rather than silently discarded.
    runner = shape_runner()
    WRITER.writerow([f"{now:.6f}", f"{elapsed:.6f}", stage["name"] if stage else "drain",
                     runner.user_count, stage["users"] if stage else 0, name,
                     f"{response_time:.6f}", response_length, int(exception is None),
                     str(exception or ""), WORKER_INDEX])


ENVIRONMENT = None


@events.init.add_listener
def init(environment, **kwargs):
    global ENVIRONMENT
    ENVIRONMENT = environment
    def accumulate_native(client_id, data, **kwargs):
        REPORTED_NATIVE["requests"] += data["stats_total"]["num_requests"]
        REPORTED_NATIVE["failures"] += data["stats_total"]["num_failures"]
    if not isinstance(environment.runner, MasterRunner):
        environment.events.report_to_master.add_listener(accumulate_native)


def shape_runner():
    return ENVIRONMENT.runner


@events.quitting.add_listener
def close(environment, **kwargs):
    if USER_SAMPLER is not None:
        USER_SAMPLER.kill()
        USER_STREAM.close()
    total = environment.stats.total
    final = {"requests": total.num_requests, "failures": total.num_failures}
    if STREAM is not None:
        STREAM.close()
        final = {key: value + REPORTED_NATIVE[key] for key, value in final.items()}
        (OUTPUT / f"worker-{WORKER_INDEX}-final.json").write_text(json.dumps(final, indent=2) + "\n")
    elif isinstance(environment.runner, MasterRunner):
        (OUTPUT / "master-final.json").write_text(json.dumps(final, indent=2) + "\n")
