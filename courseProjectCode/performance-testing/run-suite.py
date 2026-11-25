#!/usr/bin/env python3
"""Build and run Compose profiles sequentially, restarting MkDocs for each run."""
import argparse
import csv
import gzip
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = ROOT / "courseProjectDocs/performance-testing/results"
COMPOSE = ["docker", "compose", "-p", "mkdocs-perf", "-f", str(HERE / "compose.yaml")]


def command(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--types", nargs="+", choices=["load", "stress", "spike"], default=["load", "stress", "spike"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--scale", type=float, default=1)
    parser.add_argument("--label", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if args.repeats < 1 or not 0.01 <= args.scale <= 10:
        parser.error("positive repeats and scale in [0.01, 10] required")
    if not args.label or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.label):
        parser.error("label must contain only letters, digits, hyphens, underscores")
    RESULTS.mkdir(parents=True, exist_ok=True)
    info = json.loads(subprocess.check_output(["docker", "info", "--format", "{{json .}}"], text=True))
    provenance = {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "docker": {k: info.get(k) for k in ["ServerVersion", "OSType", "Architecture", "NCPU", "MemTotal"]},
        "compose": subprocess.check_output(["docker", "compose", "version", "--short"], text=True).strip(),
        "arguments": vars(args),
    }
    provenance["source_files_sha256"] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT / "mkdocs").rglob("*.py"))
    }
    provenance["harness_files_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(HERE.iterdir()) if p.is_file()
    }
    suite_file = RESULTS / f"{args.label}-suite.json"
    if suite_file.exists():
        parser.error("suite label already exists")
    suite_file.write_text(json.dumps(provenance, indent=2) + "\n")
    if not args.skip_build:
        command(COMPOSE + ["build", "app"])
    provenance["image"] = json.loads(subprocess.check_output(
        ["docker", "image", "inspect", "mkdocs-swen777-performance:local"], text=True))[0]["Id"]
    suite_file.write_text(json.dumps(provenance, indent=2) + "\n")
    runs = []
    # Rotate test order across repetitions to reduce order/thermal confounding.
    for repeat in range(1, args.repeats + 1):
        order = args.types[(repeat - 1) % len(args.types):] + args.types[:(repeat - 1) % len(args.types)]
        for profile in order:
            run_id = f"{args.label}-{profile}-{repeat}"
            output = RESULTS / run_id
            if output.exists():
                parser.error(f"run directory already exists: {run_id}")
            output.mkdir()
            env = {**os.environ, "RUN_ID": run_id, "TEST_TYPE": profile,
                   "DURATION_SCALE": str(args.scale), "PERF_SEED": str(777 + repeat)}
            print(f"Starting {run_id}", flush=True)
            try:
                command(COMPOSE + ["up", "-d", "--wait", "app"], env=env)
                container_id = subprocess.check_output(
                    COMPOSE + ["ps", "-q", "app"], env=env, text=True).strip()
                inspected = json.loads(subprocess.check_output(
                    ["docker", "inspect", container_id], text=True))[0]
                settings = inspected["HostConfig"]
                (output / "container-limits.json").write_text(json.dumps({
                    key: settings[key] for key in ["NanoCpus", "Memory", "MemorySwap", "PidsLimit"]
                }, indent=2) + "\n")
                result = subprocess.run(COMPOSE + ["run", "--rm", "--no-deps", "runner"], env=env)
                if result.returncode not in (0, 1):
                    raise RuntimeError(f"runner infrastructure failure: {result.returncode}")
                metadata = json.loads((output / "metadata.json").read_text())
                timing = json.loads((output / "timing.json").read_text())
                if metadata["finished_at"] - timing["started_at"] < metadata["nominal_seconds"] - 2:
                    raise RuntimeError("profile ended before its scheduled duration")
                if not (output / "requests.csv.gz").exists():
                    raise RuntimeError("missing request measurements")
                exceptions = output / "locust_exceptions.csv"
                if exceptions.exists() and len(exceptions.read_text().strip().splitlines()) > 1:
                    raise RuntimeError("Locust user-code exception; inspect locust_exceptions.csv")
                with gzip.open(output / "requests.csv.gz", "rt", newline="") as source:
                    failures = sum(row["success"] == "0" for row in csv.DictReader(source))
                if metadata["exit_code"] == 1 and not failures:
                    raise RuntimeError("Locust failed without a measured HTTP failure")
                runs.append(run_id)
            finally:
                with (output / "app.log").open("w") as log:
                    subprocess.run(COMPOSE + ["logs", "--no-color", "app"], env=env, stdout=log, stderr=subprocess.STDOUT)
                command(COMPOSE + ["down", "--remove-orphans"], env=env)
    provenance["completed_runs"] = runs
    suite_file.write_text(json.dumps(provenance, indent=2) + "\n")
    print("Completed: " + ", ".join(runs), flush=True)


if __name__ == "__main__":
    main()
