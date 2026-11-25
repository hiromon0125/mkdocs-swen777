"""Derive exact request statistics, phase summaries, and time-series charts."""
import argparse
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def read_csv(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as source:
        return list(csv.DictReader(source))


def resources(rows, start, end):
    rows = [row for row in rows if start <= float(row["timestamp"]) < end]
    def values(name):
        return [float(row[name]) for row in rows if row[name] != ""]
    if not rows:
        raise ValueError("no resource samples in measured phase")
    throttled = values("cgroup_throttled_usec")
    return {
        "cpu_mean": float(np.mean(values("cpu_percent"))),
        "cpu_max": max(values("cpu_percent")),
        "single_process_cpu_max": max(values("max_process_cpu_percent")),
        "rss_min_mib": min(values("rss_mib")), "rss_max_mib": max(values("rss_mib")),
        "threads_max": int(max(values("threads"))),
        "sampler_cpu_max": max(values("sampler_cpu_percent")),
        "throttled_seconds": (max(throttled) - min(throttled)) / 1e6 if throttled else None,
    }


def summarize(requests, duration):
    if not requests:
        raise ValueError("no requests in measured phase")
    latencies = np.array([float(row["response_ms"]) for row in requests])
    successes = sum(int(row["success"]) for row in requests)
    return {
        "requests": len(requests), "successes": successes, "failures": len(requests) - successes,
        "failure_percent": 100 * (len(requests) - successes) / len(requests),
        "successful_rps": successes / duration,
        "completed_rps": len(requests) / duration, "duration_s": duration,
        "mean_ms": float(np.mean(latencies)),
        **{f"p{percentile}_ms": float(np.percentile(latencies, percentile)) for percentile in [50, 95, 99]},
        "actual_users_min": min(int(row["users"]) for row in requests),
        "actual_users_max": max(int(row["users"]) for row in requests),
    }


def chart(output, requests, app, generator, timing):
    start = timing["started_at"]
    buckets = defaultdict(list)
    for row in requests:
        buckets[int(float(row["elapsed_s"]))].append(row)
    seconds = sorted(buckets)
    p95 = [float(np.percentile([float(r["response_ms"]) for r in buckets[s]], 95)) for s in seconds]
    rps = [sum(int(r["success"]) for r in buckets[s]) for s in seconds]
    target = [max(int(r["target_users"]) for r in buckets[s]) for s in seconds]
    users = [max(int(r["users"]) for r in buckets[s]) for s in seconds]
    fig, axes = plt.subplots(5, 1, figsize=(11, 12), sharex=True, layout="constrained")
    axes[0].step(seconds, target, where="post", label="target", color="#58508d")
    axes[0].plot(seconds, users, label="actual", alpha=0.7, color="#ff6361")
    axes[0].set_ylabel("Users")
    axes[1].plot(seconds, p95, color="#bc5090")
    axes[1].set_ylabel("p95 latency (ms)")
    axes[2].plot(seconds, rps, color="#007f86")
    axes[2].set_ylabel("Successful req/s")
    for rows, label, color in [(app, "MkDocs", "#003f5c"), (generator, "Locust", "#ffa600")]:
        rows = [r for r in rows if 0 <= float(r["timestamp"]) - start <= max(seconds) + 1]
        x = [float(r["timestamp"]) - start for r in rows]
        axes[3].plot(x, [float(r["cpu_percent"]) for r in rows], label=label, color=color)
        axes[4].plot(x, [float(r["rss_mib"]) for r in rows], label=label, color=color)
    axes[3].axhline(100, linestyle=":", color="#003f5c", alpha=0.5)
    axes[3].set_ylabel("CPU % (100 = 1 core)")
    axes[4].set_ylabel("Process RSS (MiB)")
    axes[4].set_xlabel("Seconds after workload start")
    boundary = 0
    for stage in timing["stages"]:
        end = boundary + stage["seconds"] * timing["duration_scale"]
        for ax in axes:
            ax.axvline(boundary, color="gray", linewidth=0.6, alpha=0.6)
            if stage["name"] == "warmup":
                ax.axvspan(boundary, end, color="gray", alpha=0.15)
        axes[0].text(boundary + 0.5, 1.02, stage["name"], transform=axes[0].get_xaxis_transform(),
                     fontsize=7, rotation=35)
        boundary = end
    for ax in axes:
        ax.grid(alpha=0.15)
    for ax in [axes[0], axes[3], axes[4]]:
        ax.legend(loc="upper right", fontsize=8)
    fig.suptitle(f"{output.name} — warmup shaded; 1-second request buckets", fontsize=12)
    fig.savefig(output / "timeseries.png", dpi=150)
    plt.close(fig)


def analyze(output):
    timing = json.loads((output / "timing.json").read_text())
    requests = read_csv(output / "requests.csv.gz")
    final_stats = output / "locust-final.json"
    if final_stats.exists():
        native = json.loads(final_stats.read_text())
        if native != {"requests": len(requests), "failures": sum(r["success"] == "0" for r in requests)}:
            raise ValueError(f"request log disagrees with final Locust counters: {output.name}")
    app = read_csv(output / "app-resources.csv")
    generator = read_csv(output / "generator-resources.csv")
    phases = []
    boundary = 0
    for stage in timing["stages"]:
        duration = stage["seconds"] * timing["duration_scale"]
        phase_requests = [r for r in requests if r["phase"] == stage["name"]]
        start = timing["started_at"] + boundary
        if stage["name"] != "warmup":
            stats = {"name": stage["name"], "target_users": stage["users"], "start_s": boundary,
                     **summarize(phase_requests, duration),
                     "app": resources(app, start, start + duration),
                     "generator": resources(generator, start, start + duration)}
            endpoints = {}
            for name in sorted({r["endpoint"] for r in phase_requests}):
                endpoints[name] = summarize([r for r in phase_requests if r["endpoint"] == name], duration)
            stats["endpoints"] = endpoints
            phases.append(stats)
        boundary += duration
    summary = {"run_id": output.name, "profile": timing["profile"], "scale": timing["duration_scale"],
               "phases": phases, "drain_requests": sum(r["phase"] == "drain" for r in requests)}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    chart(output, requests, app, generator, timing)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    results = Path("/results")
    suite = json.loads((results / f"{args.label}-suite.json").read_text())
    summaries = [analyze(results / run_id) for run_id in suite["completed_runs"]]
    (results / f"{args.label}-summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    lines = ["| Run | Phase | Users | Requests | Fail % | RPS (success) | p50 ms | p95 ms | p99 ms | App CPU mean % | App RSS peak MiB | Generator CPU peak % |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for summary in summaries:
        for p in summary["phases"]:
            lines.append(f"| {summary['run_id']} | {p['name']} | {p['target_users']} | {p['requests']} | "
                         f"{p['failure_percent']:.3f} | {p['successful_rps']:.2f} | {p['p50_ms']:.2f} | "
                         f"{p['p95_ms']:.2f} | {p['p99_ms']:.2f} | {p['app']['cpu_mean']:.2f} | "
                         f"{p['app']['rss_max_mib']:.2f} | {p['generator']['cpu_max']:.2f} |")
    (results / f"{args.label}-summary.md").write_text("\n".join(lines) + "\n")
    print("Analyzed " + str(len(summaries)) + " runs")


if __name__ == "__main__":
    main()
