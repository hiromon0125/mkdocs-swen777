#!/usr/bin/env -S uv run --script
import logging
import subprocess
import sys
from pathlib import Path

this_dir = Path(__file__).resolve().parent
project_ws = this_dir.parent.parent

coverage_report_file = this_dir / "coverage_report.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run_hatch(args, ignore_errors=False):
    """Run a hatch command in the project workspace."""
    report = subprocess.run(
        ["uv", "tool", "run", "hatch", "run", "+py=3.12", *args],
        cwd=project_ws,
        capture_output=True,
        text=True,
    )
    if not ignore_errors and report.returncode != 0:
        logging.error(
            f"Command uv tool run hatch run {' '.join(args)} failed with return code {report.returncode}"
        )
        sys.exit(report.returncode)
    return report


logging.info("Running tests to get stats...")
stats = run_hatch(["test:test", "-v"], ignore_errors=True)
# get the last 4 lines of the output to extract the test summary
summary_lines = stats.stderr.strip().splitlines()[-4:]
summary_lines = [
    line.strip() for line in summary_lines if line.strip()
]  # Remove empty lines and whitespace
summary_lines.insert(1, "Total tests executed:")
summary_lines.append(summary_lines[0])  # append the dividing line again for clarity
logging.info("Test summary:\n" + "\n".join(summary_lines))

logging.info("Generating coverage report...")
run_hatch(["test:with-coverage"], ignore_errors=True)

logging.info("Extracting report...")
report = run_hatch(["test:coverage", "report"])

with open(coverage_report_file, "w") as f:
    f.write("Test stats\n")
    f.write("\n".join(summary_lines) + "\n")
    f.write("Codecov Report\n")
    f.write(report.stdout)

logging.info(f"Coverage report written to {coverage_report_file}")
