"""Validate campaign evidence and calculate response-tail/recovery statistics."""
import argparse
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "courseProjectDocs/performance-testing/results"


def percentile(values, quantile):
    values = sorted(values)
    position = (len(values) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    summaries = json.loads((RESULTS / f"{args.label}-summary.json").read_text())
    tails, errors, total, failures, load_slow, load_total = [], Counter(), 0, 0, 0, 0
    manifest = None
    for run in summaries:
        output = RESULTS / run["run_id"]
        with gzip.open(output / "requests.csv.gz", "rt", newline="") as source:
            rows = list(csv.DictReader(source))
        failed = sum(row["success"] == "0" for row in rows)
        final = output / "locust-final.json"
        if final.exists():
            if json.loads(final.read_text()) != {"requests": len(rows), "failures": failed}:
                raise ValueError(f"final Locust counters disagree with raw requests: {output}")
        metadata = json.loads((output / "metadata.json").read_text())
        if metadata["exit_code"] not in (0, 1):
            raise ValueError(f"infrastructure failure: {output}")
        endpoints = {row["endpoint"] for row in rows}
        if endpoints != {"document", "homepage", "stylesheet", "search-index"}:
            raise ValueError(f"unexpected/missing endpoint category: {output}")
        fixture = (output / "fixture-manifest.json").read_bytes()
        if manifest is not None and fixture != manifest:
            raise ValueError("fixture changed within campaign")
        manifest = fixture
        for phase in run["phases"]:
            subset = [row for row in rows if row["phase"] == phase["name"]]
            if phase["requests"] != len(subset):
                raise ValueError(f"phase count mismatch: {output}/{phase['name']}")
            if max(int(row["users"]) for row in subset) < phase["target_users"]:
                raise ValueError(f"user target not observed: {output}/{phase['name']}")
        total += len(rows)
        failures += failed
        errors.update(row["error"] for row in rows if row["success"] == "0")
        if run["profile"] == "load":
            steady = [row for row in rows if row["phase"] == "steady"]
            load_total += len(steady)
            load_slow += sum(float(row["response_ms"]) >= 1000 for row in steady)
        if run["profile"] == "spike":
            recovery = next(phase for phase in run["phases"] if phase["name"] == "recovery")
            if recovery["duration_s"] < 20:
                continue
            end = recovery["start_s"] + recovery["duration_s"]
            tail = [row for row in rows if end - 20 <= float(row["elapsed_s"]) < end]
            tails.append({
                "run_id": run["run_id"], "window_start_s": end - 20, "window_end_s": end,
                "requests": len(tail), "successful_rps": sum(r["success"] == "1" for r in tail) / 20,
                "failures": sum(r["success"] == "0" for r in tail),
                "p95_ms": percentile([float(r["response_ms"]) for r in tail], 0.95),
                "actual_users_min": min(int(r["users"]) for r in tail),
                "actual_users_max": max(int(r["users"]) for r in tail),
            })
    result = {
        "load_requests_over_1s": load_slow, "load_steady_requests": load_total,
        "spike_last_20_seconds": tails,
        "all_completed_requests_including_warmup_and_drain": total,
        "all_failures_including_warmup_and_drain": failures,
        "error_counts_including_warmup_and_drain": dict(errors),
    }
    (RESULTS / f"{args.label}-supplementary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Validated {len(summaries)} runs, {total:,} requests, {failures:,} measured failures")


if __name__ == "__main__":
    main()
