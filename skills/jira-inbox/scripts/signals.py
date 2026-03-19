#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Deterministic signal filter for /jira-inbox v2.

Reads /tmp/jira-inbox.json (bucketed query results), applies four signal
detectors and a global 60-day staleness suppression, then writes
/tmp/jira-inbox-signals.json.

Signals:
  1. orphaned_high_priority — backlog issues: High+ priority, 0 comments, >14d old
  2. blocked_on_you        — blocked_candidates whose issuelinks reference my_work keys
  3. subtasks_under_epics  — recent_subtasks whose parent is in my_epics
  4. broad_cross_project   — broad_cross_project issues deduped against cross_project

Also builds analysis_requests for the analyst agent:
  - action_request: mentions tickets (for action-vs-FYI determination)
  - unactionable: backlog tickets with 0 comments (weak description candidates)
  - bullshit_request: mentions from reporters NOT on the no-bullshit-list
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

INPUT_PATH = Path("/tmp/jira-inbox.json")
OUTPUT_PATH = Path("/tmp/jira-inbox-signals.json")
STALENESS_DAYS = 60
ORPHAN_AGE_DAYS = 14
HIGH_PRIORITIES = {"Highest", "High", "Critical", "Blocker"}
NO_BULLSHIT_LIST_PATH = Path.home() / ".claude" / "no-bullshit-list.txt"


def load_no_bullshit_list() -> set[str]:
    """Load trusted reporter names from the no-bullshit-list file."""
    try:
        text = NO_BULLSHIT_LIST_PATH.read_text()
        return {line.strip() for line in text.splitlines() if line.strip()}
    except FileNotFoundError:
        return set()


def is_stale(issue: dict, cutoff: str) -> bool:
    """True if issue.updated < cutoff date string (YYYY-MM-DD)."""
    updated = issue.get("updated", "")
    return updated < cutoff if updated else True


def detect_orphaned_high_priority(backlog: list[dict], cutoff_created: str) -> list[dict]:
    """Backlog issues: High+ priority, 0 comments, created >14d ago."""
    signals = []
    for issue in backlog:
        created = issue.get("created", "")
        priority = issue.get("priority", "")
        comment_count = issue.get("commentCount", 0)
        if (
            priority in HIGH_PRIORITIES
            and comment_count == 0
            and created
            and created < cutoff_created
        ):
            signals.append({
                "key": issue["key"],
                "signal": "ORPHANED",
                "summary": issue.get("summary", ""),
                "priority": priority,
                "created": created,
            })
    return signals


def detect_blocked_on_you(blocked_candidates: list[dict], my_work_keys: set[str]) -> list[dict]:
    """Blocked issues whose issuelinks contain a key that's in my_work."""
    signals = []
    for issue in blocked_candidates:
        links = issue.get("issuelinks", [])
        blocking_keys = []
        for link in links:
            linked_key = link.get("key", "")
            if linked_key in my_work_keys:
                blocking_keys.append(linked_key)
        if blocking_keys:
            signals.append({
                "key": issue["key"],
                "signal": "BLOCKED ON YOU",
                "summary": issue.get("summary", ""),
                "blocking_keys": blocking_keys,
            })
    return signals


def detect_subtasks_under_epics(recent_subtasks: list[dict], my_epic_keys: set[str]) -> list[dict]:
    """Recent subtasks whose parent key is in my_epics."""
    signals = []
    for issue in recent_subtasks:
        parent = issue.get("parent", "")
        if parent in my_epic_keys:
            signals.append({
                "key": issue["key"],
                "signal": "NEW SUBTASK",
                "summary": issue.get("summary", ""),
                "parent": parent,
            })
    return signals


def detect_broad_cross_project(broad: list[dict], cross_project_keys: set[str]) -> list[dict]:
    """Broad cross-project issues deduped against the existing cross_project bucket."""
    signals = []
    for issue in broad:
        if issue["key"] not in cross_project_keys:
            signals.append({
                "key": issue["key"],
                "signal": "DEVOPS-TAGGED",
                "summary": issue.get("summary", ""),
                "project": issue.get("project", ""),
            })
    return signals


MENTION_RECENCY_DAYS = 14
UNACTIONABLE_PRIORITIES = {"Highest", "High", "Critical", "Blocker"}


def build_analysis_requests(
    data: dict,
    no_bullshit_list: set[str],
    staleness_cutoff: str,
    my_work_keys: set[str],
) -> list[dict]:
    """Build candidate tickets for the analyst agent to inspect.

    Filters aggressively so the agent only gets tickets that genuinely
    need an LLM to read comments/descriptions:

      - Skip known-good tickets (already in my_work) entirely
      - action_request: only trusted-reporter mentions updated in last 14d
      - bullshit_request: all untrusted-reporter mentions (always worth checking)
      - unactionable: only High+ priority backlog with 0 comments
    """
    requests = []
    seen_keys: set[str] = set()
    recency_cutoff = (
        date.today() - timedelta(days=MENTION_RECENCY_DAYS)
    ).isoformat()

    # Mentions: filter by reporter trust and recency
    for issue in data.get("mentions", {}).get("issues", []):
        key = issue["key"]
        if key in seen_keys or key in my_work_keys:
            continue
        seen_keys.add(key)
        reporter = issue.get("reporter", "")
        updated = issue.get("updated", "")

        # Pre-digested ticket data from hook (rides along with the search result)
        ticket_data = {
            "description": issue.get("description", ""),
            "ac": issue.get("ac", ""),
            "comments": issue.get("comments", []),
        }

        if reporter and reporter not in no_bullshit_list:
            # Untrusted reporter — always send for bullshit check
            requests.append({
                "key": key,
                "type": "bullshit_request",
                "summary": issue.get("summary", ""),
                "reporter": reporter,
                **ticket_data,
            })
        elif updated and updated >= recency_cutoff:
            # Trusted reporter, recently updated — worth checking for action
            requests.append({
                "key": key,
                "type": "action_request",
                "summary": issue.get("summary", ""),
                **ticket_data,
            })
        # else: trusted reporter, stale mention — skip (almost certainly FYI)

    # unactionable: only High+ priority backlog with 0 comments
    for issue in data.get("backlog", {}).get("issues", []):
        key = issue["key"]
        if key in seen_keys or key in my_work_keys:
            continue
        comment_count = issue.get("commentCount", 0)
        priority = issue.get("priority", "")
        if comment_count == 0 and priority in UNACTIONABLE_PRIORITIES:
            seen_keys.add(key)
            requests.append({
                "key": key,
                "type": "unactionable",
                "summary": issue.get("summary", ""),
                "description": issue.get("description", ""),
                "ac": issue.get("ac", ""),
            })

    return requests


def apply_staleness_suppression(signals: list[dict], data: dict, cutoff: str) -> list[dict]:
    """Remove signals for issues whose updated date is older than the staleness cutoff.

    Activity-bucket issues are exempt from suppression.
    """
    activity_keys = {i["key"] for i in data.get("activity", {}).get("issues", [])}

    # Build a lookup of updated dates from all buckets
    updated_lookup: dict[str, str] = {}
    for bucket in data.values():
        if not isinstance(bucket, dict):
            continue
        for issue in bucket.get("issues", []):
            key = issue.get("key", "")
            updated = issue.get("updated", "")
            if key and updated:
                updated_lookup[key] = updated

    filtered = []
    for sig in signals:
        key = sig["key"]
        if key in activity_keys:
            filtered.append(sig)
            continue
        updated = updated_lookup.get(key, "")
        if updated and updated >= cutoff:
            filtered.append(sig)
    return filtered


def main() -> None:
    if not INPUT_PATH.exists():
        print(f"Error: {INPUT_PATH} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(INPUT_PATH.read_text())
    today = date.today()
    staleness_cutoff = (today - timedelta(days=STALENESS_DAYS)).isoformat()
    orphan_cutoff = (today - timedelta(days=ORPHAN_AGE_DAYS)).isoformat()
    no_bullshit_list = load_no_bullshit_list()

    # Extract key sets for cross-referencing
    my_work_keys = {i["key"] for i in data.get("my_work", {}).get("issues", [])}
    my_epic_keys = {i["key"] for i in data.get("my_epics", {}).get("issues", [])}
    cross_project_keys = {i["key"] for i in data.get("cross_project", {}).get("issues", [])}

    # Detect signals
    orphaned = detect_orphaned_high_priority(
        data.get("backlog", {}).get("issues", []), orphan_cutoff
    )
    blocked = detect_blocked_on_you(
        data.get("blocked_candidates", {}).get("issues", []), my_work_keys
    )
    subtasks = detect_subtasks_under_epics(
        data.get("recent_subtasks", {}).get("issues", []), my_epic_keys
    )
    broad = detect_broad_cross_project(
        data.get("broad_cross_project", {}).get("issues", []), cross_project_keys
    )

    all_signals = orphaned + blocked + subtasks + broad

    # Apply 60-day staleness suppression
    all_signals = apply_staleness_suppression(all_signals, data, staleness_cutoff)

    # Build analysis requests for the analyst agent
    analysis_requests = build_analysis_requests(data, no_bullshit_list, staleness_cutoff, my_work_keys)

    output = {
        "signals": all_signals,
        "analysis_requests": analysis_requests,
        "no_bullshit_list": sorted(no_bullshit_list),
        "my_work_keys": sorted(my_work_keys),
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"Wrote {len(all_signals)} signals, {len(analysis_requests)} analysis requests to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
