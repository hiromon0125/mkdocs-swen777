"""Sample an exact child process tree; no Docker socket or host PID access."""
import argparse
import csv
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a child command is required")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    child = subprocess.Popen(command, start_new_session=True)

    def stop(signum, frame):
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    root = psutil.Process(child.pid)
    sampler = psutil.Process()
    known = {}
    started = time.monotonic()
    with args.output.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=[
            "timestamp", "elapsed_s", "cpu_percent", "rss_mib", "threads", "processes",
            "sampler_cpu_percent", "sampler_rss_mib", "cgroup_throttled_usec", "cgroup_memory_bytes",
            "max_process_cpu_percent",
        ])
        writer.writeheader()
        sampler.cpu_percent()
        while child.poll() is None:
            cpu = rss = threads = 0
            max_process_cpu = 0
            live = []
            try:
                processes = [root, *root.children(recursive=True)]
            except psutil.NoSuchProcess:
                break
            for proc in processes:
                try:
                    # Reuse Process objects: cpu_percent stores its previous sample.
                    identity = (proc.pid, proc.create_time())
                    proc = known.setdefault(identity, proc)
                    process_cpu = proc.cpu_percent()
                    cpu += process_cpu
                    max_process_cpu = max(max_process_cpu, process_cpu)
                    rss += proc.memory_info().rss
                    threads += proc.num_threads()
                    live.append(identity)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            known = {key: value for key, value in known.items() if key in live}
            throttled = memory = ""
            try:
                stats = dict(line.split() for line in Path("/sys/fs/cgroup/cpu.stat").read_text().splitlines())
                throttled = stats.get("throttled_usec", "")
                memory = Path("/sys/fs/cgroup/memory.current").read_text().strip()
            except (OSError, ValueError):
                pass
            writer.writerow({
                "timestamp": time.time(), "elapsed_s": round(time.monotonic() - started, 3),
                "cpu_percent": round(cpu, 2), "rss_mib": round(rss / 1024**2, 3),
                "max_process_cpu_percent": max_process_cpu,
                "threads": threads, "processes": len(live),
                "sampler_cpu_percent": sampler.cpu_percent(),
                "sampler_rss_mib": round(sampler.memory_info().rss / 1024**2, 3),
                "cgroup_throttled_usec": throttled, "cgroup_memory_bytes": memory,
            })
            output.flush()
            time.sleep(1)
    return child.wait()


if __name__ == "__main__":
    raise SystemExit(main())
