#!/usr/bin/env python3
"""
Counts lines of code and comment lines per file.

LOC = non-blank lines
Comment line = a line whose first character is '#' or is a docstring (triple-quoted string)

Usage: python metrics.py <path-to-package>
"""

import csv
import sys
from pathlib import Path


def measure(path):

    loc = 0
    comments = 0
    in_docstring = False

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():

        stripped = line.strip()

        if not stripped:
            continue
        
        loc += 1

        # Count the number of triple quote markers on this line
        quotes = stripped.count('"""') + stripped.count("'''")

        # Need to count the docstring comments as well
        if in_docstring:
            comments += 1
            if quotes % 2 == 1:
                in_docstring = False
            continue

        if quotes % 2 == 1:
            in_docstring = True
            comments += 1
            continue

        if stripped.startswith("#"):
            comments += 1

    return loc, comments


def main():

    # Gets the path from the argument
    root = Path(sys.argv[1])
    rows = []

    # Goes through every directory and subdirectory and grabs any .py file
    for path in sorted(root.rglob("*.py")):

        loc, comments = measure(path)

        # Append file path, test/prod tag, line counts, comments, and comment density
        rows.append({
            "file": str(path.relative_to(root)),
            "type": "test" if "tests" in path.parts else "production",
            "loc": loc,
            "comments": comments,
            "comment_density": round(comments / loc, 3) if loc else 0,
        })

    with open("metrics.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    for label in ("production", "test"):

        # Filter by type (production or test)
        group = [r for r in rows if r["type"] == label]

        # Total lines of code across every file in the group
        loc = sum(r["loc"] for r in group)

        # Total comments across every file in the group
        comments = sum(r["comments"] for r in group)

        print(f"\n{label.upper()}")
        print(f"  files           : {len(group)}")
        print(f"  LOC             : {loc}")
        print(f"  comment lines   : {comments}")
        print(f"  comment density : {comments / loc:.1%}")
        print(f"  avg LOC/file    : {loc // len(group)}")

    print("\nWrote metrics.csv")


if __name__ == "__main__":
    main()
