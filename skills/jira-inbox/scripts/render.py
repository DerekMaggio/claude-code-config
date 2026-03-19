#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jinja2"]
# ///
"""Render a Jira inbox digest from bucketed query results.

Usage:
    # Default: signals + bucket summary counts (used by /jira-inbox)
    uv run render.py /tmp/jira-inbox.json --signals signals.json --agent-flags flags.txt

    # Single bucket table
    uv run render.py /tmp/jira-inbox.json --bucket my_work

    # Full dump — all buckets expanded (legacy mode)
    uv run render.py /tmp/jira-inbox.json --signals signals.json --agent-flags flags.txt --full
"""

import json
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

SIGNALS_TEMPLATE = """\
## Needs Your Attention ({{ signal_count }} signals)

{% if action_required -%}
### Action Required
| Key | Summary | Signal | Reason |
|:---|:---|:---|:---|
{% for i in action_required -%}
| {{ i.key }} | {{ i.summary }} | {{ i.signal }} | {{ i.reason }} |
{% endfor -%}
{% endif -%}

{% if awareness -%}
### Awareness
| Key | Summary | Signal | Detail |
|:---|:---|:---|:---|
{% for i in awareness -%}
| {{ i.key }} | {{ i.summary }} | {{ i.signal }} | {{ i.detail }} |
{% endfor -%}
{% endif -%}

{% if ticket_quality -%}
### Ticket Quality
| Key | Summary | Flag | Reason |
|:---|:---|:---|:---|
{% for i in ticket_quality -%}
| {{ i.key }} | {{ i.summary }} | {{ i.flag }} | {{ i.reason }} |
{% endfor -%}
{% endif -%}

{% if not action_required and not awareness and not ticket_quality -%}
*Your inbox is clean — no signals detected.*
{% endif %}
"""

BUCKET_SUMMARY_TEMPLATE = """\
---

## Buckets — {{ today }}

- **My Work**: {{ counts.my_work }}
- **Mentioned**: {{ counts.mentions }}
- **Watching**: {{ counts.watching }}
- **Delegated**: {{ counts.delegated }}
- **Cross-Project**: {{ counts.cross_project }}
- **Activity This Week**: {{ counts.activity }}
- **Unassigned Backlog**: {{ counts.backlog }}
- **Completed This Month**: {{ counts.completed }}

*Ask to drill into any bucket (e.g. "show my_work" or "show activity").*
"""

# Per-bucket templates keyed by bucket name
BUCKET_TEMPLATES = {
    "my_work": """\
### My Work ({{ issues | length }} active)

{% if issues -%}
| Key | Summary | Status | Priority | Project | Updated |
|:---|:---|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.status }} | {{ i.priority }} | {{ i.project }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*No active work assigned to you.*
{% endif %}
""",
    "mentions": """\
### Mentioned ({{ issues | length }})

{% if issues -%}
| Key | Summary | Status | Assignee | Project | Updated |
|:---|:---|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.status }} | {{ i.assignee }} | {{ i.project }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*No unresolved mentions.*
{% endif %}
""",
    "watching": """\
### Watching ({{ issues | length }})

{% if issues -%}
| Key | Summary | Status | Assignee | Project | Updated |
|:---|:---|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.status }} | {{ i.assignee }} | {{ i.project }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*Nothing watched.*
{% endif %}
""",
    "delegated": """\
### Delegated ({{ issues | length }})

{% if issues -%}
| Key | Summary | Status | Assignee | Project | Updated |
|:---|:---|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.status }} | {{ i.assignee }} | {{ i.project }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*No delegated work outstanding.*
{% endif %}
""",
    "cross_project": """\
### Cross-Project DevOps Work ({{ issues | length }})

{% if issues -%}
| Key | Summary | Status | Assignee | Project | Updated |
|:---|:---|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.status }} | {{ i.assignee }} | {{ i.project }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*No cross-project DevOps tickets.*
{% endif %}
""",
    "activity": """\
### DEVOPS Activity This Week ({{ issues | length }})

{% if issues -%}
| Key | Summary | Status | Assignee | Updated |
|:---|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.status }} | {{ i.assignee }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*No DEVOPS status changes this week.*
{% endif %}
""",
    "backlog": """\
### Unassigned DEVOPS Backlog ({{ issues | length }})

{% if issues -%}
| Key | Summary | Priority | Updated |
|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.priority }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*No unassigned DEVOPS tickets.*
{% endif %}
""",
    "completed": """\
### Recently Completed This Month ({{ issues | length }})

{% if issues -%}
| Key | Summary | Status | Project | Updated |
|:---|:---|:---|:---|:---|
{% for i in issues -%}
| {{ i.key }} | {{ i.summary }} | {{ i.status }} | {{ i.project }} | {{ i.updated }} |
{% endfor -%}
{% else -%}
*Nothing completed this month yet.*
{% endif %}
""",
}


# ---------------------------------------------------------------------------
# Signal + agent-flag merging
# ---------------------------------------------------------------------------

def parse_agent_flags(text: str) -> dict[str, tuple[str, str]]:
    """Parse pipe-delimited agent output into {key: (verdict, reason)}."""
    flags: dict[str, tuple[str, str]] = {}
    for line in text.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            key, verdict, reason = parts[0], parts[1], parts[2]
            flags[key] = (verdict, reason)
    return flags


def build_signal_sections(
    signals: list[dict],
    agent_flags: dict[str, tuple[str, str]],
    inbox_data: dict,
) -> dict:
    """Merge deterministic signals + agent verdicts into render-ready sections."""
    # Build a summary lookup from all buckets
    summary_lookup: dict[str, str] = {}
    for bucket in inbox_data.values():
        if not isinstance(bucket, dict):
            continue
        for issue in bucket.get("issues", []):
            summary_lookup[issue.get("key", "")] = issue.get("summary", "")

    action_required: list[dict] = []
    awareness: list[dict] = []
    ticket_quality: list[dict] = []
    seen_keys: set[str] = set()

    # Agent flags: ACTION NEEDED, BULLSHIT, UNACTIONABLE (skip SKIP and KNOWN GOOD)
    for key, (verdict, reason) in agent_flags.items():
        if verdict in ("SKIP", "KNOWN GOOD"):
            continue
        summary = summary_lookup.get(key, "")
        if verdict == "ACTION NEEDED":
            action_required.append({"key": key, "summary": summary, "signal": "ACTION NEEDED", "reason": reason})
            seen_keys.add(key)
        elif verdict == "BULLSHIT":
            ticket_quality.append({"key": key, "summary": summary, "flag": "BULLSHIT", "reason": reason})
            seen_keys.add(key)
        elif verdict == "UNACTIONABLE":
            ticket_quality.append({"key": key, "summary": summary, "flag": "UNACTIONABLE", "reason": reason})
            seen_keys.add(key)

    # Deterministic signals
    for sig in signals:
        key = sig["key"]
        if key in seen_keys:
            continue
        seen_keys.add(key)
        summary = sig.get("summary", "") or summary_lookup.get(key, "")
        signal_type = sig.get("signal", "")

        if signal_type == "BLOCKED ON YOU":
            blocking = ", ".join(sig.get("blocking_keys", []))
            action_required.append({"key": key, "summary": summary, "signal": "BLOCKED ON YOU", "reason": f"Blocked by your tickets: {blocking}"})
        elif signal_type == "ORPHANED":
            awareness.append({"key": key, "summary": summary, "signal": "ORPHANED", "detail": f"Priority: {sig.get('priority', '')}, created: {sig.get('created', '')}, 0 comments"})
        elif signal_type == "NEW SUBTASK":
            awareness.append({"key": key, "summary": summary, "signal": "NEW SUBTASK", "detail": f"Under your epic {sig.get('parent', '')}"})
        elif signal_type == "DEVOPS-TAGGED":
            awareness.append({"key": key, "summary": summary, "signal": "DEVOPS-TAGGED", "detail": f"Project: {sig.get('project', '')}"})

    signal_count = len(action_required) + len(awareness) + len(ticket_quality)

    return {
        "action_required": action_required,
        "awareness": awareness,
        "ticket_quality": ticket_quality,
        "signal_count": signal_count,
    }


# ---------------------------------------------------------------------------
# Dedup + main
# ---------------------------------------------------------------------------

def dedup_bucket(issues: list[dict], seen: set[str]) -> tuple[list[dict], int]:
    """Remove issues already shown in a prior bucket. Returns (filtered, removed_count)."""
    filtered = []
    removed = 0
    for issue in issues:
        key = issue.get("key", "")
        if key in seen:
            removed += 1
        else:
            seen.add(key)
            filtered.append(issue)
    return filtered, removed


def render_full(data: dict, signals_output: str, env: Environment) -> str:
    """Full dump — signals + all bucket tables (legacy mode)."""
    seen: set[str] = set()
    parts: list[str] = [signals_output, "---", "", f"## Jira Inbox — {date.today().isoformat()}", ""]

    for bucket_name, template_str in BUCKET_TEMPLATES.items():
        issues = data.get(bucket_name, {}).get("issues", [])
        if bucket_name not in ("activity", "backlog", "completed"):
            issues, _ = dedup_bucket(issues, seen)
        template = env.from_string(template_str)
        parts.append(template.render(issues=issues))
        parts.append("")

    return "\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: render.py <input.json> [--signals <signals.json>] [--agent-flags <flags.txt>] [--bucket <name>] [--full]", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    signals_path: str | None = None
    agent_flags_path: str | None = None
    bucket_name: str | None = None
    full_mode = False

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--signals" and i + 1 < len(args):
            signals_path = args[i + 1]
            i += 2
        elif args[i] == "--agent-flags" and i + 1 < len(args):
            agent_flags_path = args[i + 1]
            i += 2
        elif args[i] == "--bucket" and i + 1 < len(args):
            bucket_name = args[i + 1]
            i += 2
        elif args[i] == "--full":
            full_mode = True
            i += 1
        else:
            i += 1

    env = Environment(autoescape=False, keep_trailing_newline=True)

    # Single bucket mode — render one bucket table and exit
    if bucket_name:
        if bucket_name not in BUCKET_TEMPLATES:
            print(f"Unknown bucket: {bucket_name}. Valid: {', '.join(BUCKET_TEMPLATES.keys())}", file=sys.stderr)
            sys.exit(1)
        issues = data.get(bucket_name, {}).get("issues", [])
        template = env.from_string(BUCKET_TEMPLATES[bucket_name])
        print(template.render(issues=issues))
        return

    # Build signals output
    signals_output = ""
    if signals_path:
        signals_data = json.loads(Path(signals_path).read_text())
        agent_flags = parse_agent_flags(Path(agent_flags_path).read_text()) if agent_flags_path else {}
        sections = build_signal_sections(
            signals_data.get("signals", []),
            agent_flags,
            data,
        )
        signals_template = env.from_string(SIGNALS_TEMPLATE)
        signals_output = signals_template.render(**sections)

    if full_mode:
        print(render_full(data, signals_output, env))
    else:
        # Default: signals + bucket summary counts
        summary_template = env.from_string(BUCKET_SUMMARY_TEMPLATE)
        counts = {k: len(data.get(k, {}).get("issues", [])) for k in BUCKET_TEMPLATES}
        print(signals_output + summary_template.render(today=date.today().isoformat(), counts=counts))


if __name__ == "__main__":
    main()
