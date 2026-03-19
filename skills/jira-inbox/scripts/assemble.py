#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Assemble jira-inbox bucket parts into a single JSON file.

Reads /tmp/jira-inbox-parts/<bucket>.json files written by the
filter-jira-search.py hook and combines them into /tmp/jira-inbox.json.
"""

import json
import sys
from pathlib import Path

PARTS_DIR = Path("/tmp/jira-inbox-parts")
OUTPUT_PATH = Path("/tmp/jira-inbox.json")

EXPECTED_BUCKETS = [
    "my_work",
    "mentions",
    "watching",
    "delegated",
    "cross_project",
    "activity",
    "backlog",
    "completed",
    "blocked_candidates",
    "my_epics",
    "recent_subtasks",
    "broad_cross_project",
]


def main() -> None:
    if not PARTS_DIR.is_dir():
        print(f"Error: {PARTS_DIR} not found", file=sys.stderr)
        sys.exit(1)

    combined: dict = {}
    missing: list[str] = []

    for bucket in EXPECTED_BUCKETS:
        part_file = PARTS_DIR / f"{bucket}.json"
        if part_file.exists():
            combined[bucket] = json.loads(part_file.read_text())
        else:
            missing.append(bucket)
            combined[bucket] = {"issues": [], "total": 0, "isLast": True}

    OUTPUT_PATH.write_text(json.dumps(combined, indent=2))

    total_issues = sum(b.get("total", 0) for b in combined.values())
    present = len(EXPECTED_BUCKETS) - len(missing)
    print(f"Assembled {present}/{len(EXPECTED_BUCKETS)} buckets, {total_issues} total issues → {OUTPUT_PATH}")
    if missing:
        print(f"  Missing: {', '.join(missing)}")


if __name__ == "__main__":
    main()
