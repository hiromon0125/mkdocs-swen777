"""Run one isolated Locust profile and monitor its process separately."""
import argparse
import bisect
import csv
import gzip
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from importlib.metadata import version
from pathlib import Path


def merge_workers(output):
    rows, user_samples = [], {}
    counters = {"requests": 0, "failures": 0}
    for index in [1, 2]:
        with (output / f"worker-{index}-requests.csv").open(newline="") as source:
            worker_rows = list(csv.DictReader(source))
        native = json.loads((output / f"worker-{index}-final.json").read_text())
        if native != {"requests": len(worker_rows), "failures": sum(r["success"] == "0" for r in worker_rows)}:
            raise RuntimeError(f"worker {index} request log disagrees with Locust's native counters")
        for key in counters:
            counters[key] += native[key]
        rows.extend(worker_rows)
        with (output / f"worker-{index}-users.csv").open(newline="") as source:
            samples = list(csv.DictReader(source))
        user_samples[str(index)] = (
            [float(row["timestamp"]) for row in samples], [int(row["users"]) for row in samples])
    rows.sort(key=lambda row: float(row["timestamp"]))
    columns = list(rows[0]) + ["worker_users"]
    with gzip.open(output / "requests.csv.gz", "wt", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            row["worker_users"] = row["users"]
            users = int(row["users"])
            for worker, (timestamps, counts) in user_samples.items():
                if worker == row["worker"]:
                    continue
                sample = bisect.bisect_right(timestamps, float(row["timestamp"])) - 1
                users += counts[sample] if sample >= 0 else 0
            row["users"] = users
            writer.writerow(row)
    (output / "locust-final.json").write_text(json.dumps(counters, indent=2) + "\n")
    for index in [1, 2]:
        (output / f"worker-{index}-requests.csv").unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=["load", "stress", "spike"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scale", type=float, default=1)
    args = parser.parse_args()
    if not 0.01 <= args.scale <= 10:
        parser.error("--scale must be between 0.01 and 10")
    if not args.run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.run_id):
        parser.error("--run-id may contain only letters, digits, hyphens and underscores")
    output = Path("/results") / args.run_id
    output.mkdir(parents=True, exist_ok=True)
    if (output / "metadata.json").exists():
        parser.error("run already exists; choose a new --run-id")
    stages = json.loads(Path("/bench/profiles.json").read_text())[args.type]
    # Validate the actual measured endpoints before generating any traffic.
    for path in ["/", "/page-00/", "/css/base.css", "/search/search_index.json"]:
        with urllib.request.urlopen("http://app:8000" + path, timeout=5) as response:
            if response.status != 200 or not response.read():
                raise RuntimeError(f"endpoint validation failed: {path}")
    environment = {
        **os.environ, "RUN_ID": args.run_id, "TEST_TYPE": args.type,
        "DURATION_SCALE": str(args.scale),
    }
    shutil.copy("/bench/environment.txt", output / "environment.txt")
    shutil.copy("/fixture/manifest.json", output / "fixture-manifest.json")
    metadata = {
        "python": sys.version, "platform": platform.platform(),
        "locust": version("locust"), "psutil": version("psutil"), "mkdocs": version("mkdocs"),
        "test_type": args.type, "run_id": args.run_id, "scale": args.scale,
        "nominal_seconds": sum(s["seconds"] for s in stages) * args.scale,
        "app_cpu_limit": 1, "app_memory_mib": 512,
        "runner_cpu_limit": 2, "runner_memory_mib": 1024,
        "locust_workers": 2,
        "started_at": time.time(),
    }
    metadata["runner_cgroup"] = {
        name: Path("/sys/fs/cgroup", name).read_text().strip()
        for name in ["cpu.max", "memory.max", "memory.swap.max", "pids.max"]
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    command = [
        sys.executable, "/bench/monitor.py", "--output", str(output / "generator-resources.csv"),
        "--", sys.executable, "-m", "locust", "-f", "/bench/locustfile.py",
        "--host", "http://app:8000", "--headless", "--only-summary",
        "--processes", "2", "--expect-workers", "2",
        "--csv", str(output / "locust"), "--csv-full-history", "--stop-timeout", "5",
        "--html", str(output / "locust.html"),
    ]
    # A wall-clock bound also covers infrastructure errors that could stall a shape.
    with (output / "locust.log").open("w") as log:
        try:
            result = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=metadata["nominal_seconds"] + 90)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    metadata.update({"finished_at": time.time(), "exit_code": code})
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    if code in (0, 1):
        merge_workers(output)
    print(json.dumps(metadata, indent=2), flush=True)
    # Locust's exit code 1 can represent measured HTTP failures, not a broken harness.
    # The outer suite verifies timing, data, and exceptions before accepting that case.
    return code


if __name__ == "__main__":
    raise SystemExit(main())
