#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""PostToolUse hook — Slim Jira search results before they enter context.

Fires on mcp__atlassian__searchJiraIssuesUsingJql and replaces the full
Jira API response (~80KB) with a compact version (~3KB) containing only
the fields needed for triage and display.

When /tmp/jira-inbox-parts/ exists (created by the /jira-inbox skill),
the hook saves each slimmed result to disk keyed by bucket name and
returns only a minimal confirmation to context — keeping query data out
of the LLM context window entirely.

Handles three response shapes:
  1. Inline list  — [{type: "text", text: "{issues: [...]}"}]
  2. Inline dict  — {issues: [...]}
  3. Oversized str — "Error: result ... saved to /path/to/file.txt"

If parsing fails, emits a [HOOK WARNING] as the tool output.
"""

import json
import re
import sys
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Inbox parts mode — save to disk instead of loading into context
# ---------------------------------------------------------------------------

PARTS_DIR = Path("/tmp/jira-inbox-parts")

# Ordered from most specific to least specific so early matches win.
JQL_BUCKET_PATTERNS: list[tuple[str, str]] = [
    ("mentions", "comment ~"),
    ("watching", "watcher = currentUser()"),
    ("delegated", "reporter = currentUser()"),
    ("blocked_candidates", "status = Blocked"),
    ("my_epics", "issuetype = Epic"),
    ("recent_subtasks", "subTaskIssueTypes()"),
    ("completed", 'statusCategory = "Done"'),
    ("backlog", "assignee is EMPTY"),
    ("activity", "status changed DURING"),
    ("cross_project", "project in (CO"),
    ("broad_cross_project", "project not in (DEVOPS)"),
    ("my_work", "assignee = currentUser()"),
]


def jql_to_bucket(jql: str) -> str | None:
    """Map a JQL query string to its inbox bucket name, or None."""
    for bucket, pattern in JQL_BUCKET_PATTERNS:
        if pattern in jql:
            return bucket
    return None


def try_read_saved_file(text: str) -> str | None:
    """Recover Jira JSON from a file when Claude Code persisted an oversized response."""
    match = re.search(r"saved to[:\s]+(/[^\s]+)", text)
    if not match:
        return None

    raw_path = match.group(1).rstrip(".,;:")
    try:
        file_path = Path(raw_path).resolve(strict=True)
    except (OSError, ValueError):
        return None

    if not file_path.is_file() or file_path.suffix not in (".txt", ".json"):
        return None

    try:
        data = json.loads(file_path.read_text())
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and "text" in entry:
                    try:
                        parsed = json.loads(entry["text"])
                        if isinstance(parsed, dict) and "issues" in parsed:
                            return entry["text"]
                    except (json.JSONDecodeError, TypeError):
                        continue
        if isinstance(data, dict) and "issues" in data:
            return json.dumps(data)
    except Exception:
        pass

    return None


def extract_rich_text(value: object, max_chars: int = 500) -> str:
    """Extract plain text from a rich text field (markdown string or ADF object)."""
    if isinstance(value, str):
        return value[:max_chars]
    if not isinstance(value, dict):
        return ""

    # ADF: recursively collect text nodes
    texts: list[str] = []

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for child in node.get("content", []):
                _walk(child)

    _walk(value)
    return " ".join(texts)[:max_chars]


def extract_issue(issue: dict) -> dict:
    """Pull only the fields we care about from a Jira issue.

    Core fields are always included.  Optional fields (reporter, created,
    issuetype, commentCount, parent, labels, components, issuelinks,
    description, ac, comments) are only added when present in the raw data
    so existing queries that don't request them produce identical output.
    """
    fields = issue.get("fields", {})
    assignee = fields.get("assignee") or {}
    status = fields.get("status") or {}
    project = fields.get("project") or {}
    priority = fields.get("priority") or {}
    updated = fields.get("updated", "")

    slim: dict = {
        "key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "status": status.get("name", "Unknown"),
        "statusCategory": (status.get("statusCategory") or {}).get("name", ""),
        "assignee": assignee.get("displayName", "Unassigned"),
        "project": project.get("key", ""),
        "priority": priority.get("name", ""),
        "updated": updated[:10] if updated else "",
    }

    # --- Optional fields (only when present in raw data) ---

    reporter = fields.get("reporter")
    if reporter and isinstance(reporter, dict):
        slim["reporter"] = reporter.get("displayName", "")

    created = fields.get("created")
    if created:
        slim["created"] = created[:10]

    issuetype = fields.get("issuetype")
    if issuetype and isinstance(issuetype, dict):
        slim["issuetype"] = issuetype.get("name", "")

    # Description snippet (when requested via fields)
    description = fields.get("description")
    if description:
        slim["description"] = extract_rich_text(description, 500)

    # Acceptance Criteria snippet (customfield_10037)
    ac = fields.get("customfield_10037")
    if ac:
        slim["ac"] = extract_rich_text(ac, 500)

    # Comments: always extract count, plus last 5 summaries when comments exist
    comment = fields.get("comment")
    if comment and isinstance(comment, dict):
        slim["commentCount"] = comment.get("total", 0)
        raw_comments = comment.get("comments", [])
        if raw_comments:
            recent = raw_comments[-5:]
            slim_comments = []
            for c in recent:
                if not isinstance(c, dict):
                    continue
                author = (c.get("author") or {}).get("displayName", "")
                c_created = (c.get("created") or "")[:10]
                body = c.get("body", "")
                text = extract_rich_text(body, 300)
                slim_comments.append({
                    "author": author,
                    "created": c_created,
                    "text": text,
                })
            slim["comments"] = slim_comments

    parent = fields.get("parent")
    if parent and isinstance(parent, dict):
        slim["parent"] = parent.get("key", "")

    labels = fields.get("labels")
    if labels and isinstance(labels, list):
        slim["labels"] = labels

    components = fields.get("components")
    if components and isinstance(components, list):
        slim["components"] = [c.get("name", "") for c in components if isinstance(c, dict)]

    issuelinks = fields.get("issuelinks")
    if issuelinks and isinstance(issuelinks, list):
        slim_links = []
        for link in issuelinks:
            if not isinstance(link, dict):
                continue
            link_type = (link.get("type") or {}).get("name", "")
            if "outwardIssue" in link:
                target = link["outwardIssue"]
                slim_links.append({
                    "type": link_type,
                    "direction": "outward",
                    "key": target.get("key", ""),
                    "status": ((target.get("fields") or {}).get("status") or {}).get("name", ""),
                })
            elif "inwardIssue" in link:
                target = link["inwardIssue"]
                slim_links.append({
                    "type": link_type,
                    "direction": "inward",
                    "key": target.get("key", ""),
                    "status": ((target.get("fields") or {}).get("status") or {}).get("name", ""),
                })
        if slim_links:
            slim["issuelinks"] = slim_links

    return slim


def filter_response(raw_text: str) -> str | None:
    """Parse a Jira search response and return a slim version."""
    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict) or "issues" not in data:
        return None

    slim: dict = {
        "issues": [extract_issue(i) for i in data["issues"]],
        "total": len(data["issues"]),
        "isLast": data.get("isLast", True),
    }

    if data.get("nextPageToken"):
        slim["nextPageToken"] = data["nextPageToken"]

    return json.dumps(slim)


def get_slim_json(tool_response: object) -> str | None:
    """Extract and slim a Jira search response regardless of input shape."""
    if isinstance(tool_response, list):
        for entry in tool_response:
            if not isinstance(entry, dict) or entry.get("type") != "text":
                continue
            slim = filter_response(entry.get("text", ""))
            if slim is not None:
                return slim
        return None

    if isinstance(tool_response, dict) and "issues" in tool_response:
        return filter_response(json.dumps(tool_response))

    if isinstance(tool_response, str):
        recovered = try_read_saved_file(tool_response)
        if recovered is not None:
            return filter_response(recovered)

    return None


def emit(entries: list[dict]) -> None:
    """Write the hook output and exit."""
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedMCPToolOutput": entries}},
        sys.stdout,
    )
    sys.exit(0)


def emit_warning(reason: str, detail: str = "") -> None:
    """Emit a warning as the tool output so Claude knows the filter broke."""
    msg = f"[HOOK WARNING] filter-jira-search.py: {reason}"
    if detail:
        msg += f" | {detail[:200]}"
    emit([{"type": "text", "text": msg}])


def handle_list(tool_response: list) -> None:
    """Handle inline MCP response: [{type: "text", text: "..."}]."""
    filtered: list[dict] = []
    found_issues = False

    for entry in tool_response:
        if not isinstance(entry, dict) or entry.get("type") != "text":
            filtered.append(entry)
            continue

        text = entry.get("text", "")
        slim = filter_response(text)
        if slim is not None:
            found_issues = True
            filtered.append({"type": "text", "text": slim})
        elif len(text) > 200:
            filtered.append({"type": "text", "text": text[:200] + "..."})
        else:
            filtered.append(entry)

    if not found_issues:
        emit_warning(
            "No parseable issues in MCP response array",
            f"{len(tool_response)} entries, none with 'issues' key",
        )

    emit(filtered)


def handle_dict(tool_response: dict) -> None:
    """Handle inline dict response: {issues: [...]}."""
    slim = filter_response(json.dumps(tool_response))
    if slim is not None:
        emit([{"type": "text", "text": slim}])
    else:
        emit_warning("tool_response has 'issues' key but filter_response failed")


def handle_str(tool_response: str) -> None:
    """Handle oversized response saved to disk."""
    recovered = try_read_saved_file(tool_response)
    if recovered is not None:
        slim = filter_response(recovered)
        if slim is not None:
            emit([{"type": "text", "text": slim}])
        else:
            emit_warning("Recovered file but failed to filter", recovered[:200])
    else:
        emit_warning("Could not recover saved file", tool_response[:200])


def main() -> None:
    try:
        raw_input = sys.stdin.read()
    except Exception as e:
        emit_warning("Could not read stdin", str(e))

    try:
        hook_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        emit_warning("stdin is not valid JSON", str(e))

    tool_response = hook_data.get("tool_response")
    if tool_response is None:
        emit_warning("No tool_response in hook input", f"keys: {list(hook_data.keys())}")

    # Inbox parts mode: save to disk, return minimal confirmation to context
    jql = hook_data.get("tool_input", {}).get("jql", "")
    if PARTS_DIR.is_dir() and jql:
        bucket = jql_to_bucket(jql)
        if bucket is not None:
            slim_json = get_slim_json(tool_response)
            if slim_json is not None:
                dest = PARTS_DIR / f"{bucket}.json"
                dest.write_text(slim_json)
                issue_count = json.loads(slim_json).get("total", 0)
                emit([{"type": "text", "text": f"✓ {bucket} ({issue_count} issues) → {dest}"}])

    # Default: slim data in context (non-inbox queries or fallback)
    if isinstance(tool_response, list):
        handle_list(tool_response)
    elif isinstance(tool_response, dict) and "issues" in tool_response:
        handle_dict(tool_response)
    elif isinstance(tool_response, str):
        handle_str(tool_response)
    else:
        emit_warning(
            f"Unexpected tool_response type: {type(tool_response).__name__}",
            str(tool_response)[:200],
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        msg = f"[HOOK WARNING] filter-jira-search.py crashed: {e}\n{tb}"
        json.dump(
            {"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedMCPToolOutput": [{"type": "text", "text": msg}]}},
            sys.stdout,
        )
        sys.exit(0)
