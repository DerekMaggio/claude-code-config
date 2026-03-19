---
name: jira-inbox
description: Categorized Jira inbox — signal-based triage with agent analysis, plus 7 buckets of tickets needing your attention and recent completions
mode-exempt: true
updated: 2026-03-19
---

You are generating a Jira inbox digest with signal-based triage. Follow these steps exactly.

## Prerequisites

This skill requires a **no-bullshit-list** file at `~/.claude/no-bullshit-list.txt` containing one trusted reporter name per line. If the file is missing, the analyst will treat all reporters as untrusted.

## Step 1: Run all 12 JQL queries in parallel

First, prepare the parts directory so the hook saves results to disk instead of loading them into context:
```bash
rm -rf /tmp/jira-inbox-parts && mkdir -p /tmp/jira-inbox-parts
```

Then use `mcp__atlassian__searchJiraIssuesUsingJql` with `cloudId: <jira_cloud_id>` and `maxResults: 100` for ALL queries. Run them ALL in a single parallel tool call.

**Query 1 — my_work:**
- jql: `assignee = currentUser() AND resolution = Unresolved AND statusCategory not in ("Done") ORDER BY priority DESC, updated DESC`
- fields: `["summary", "status", "project", "priority", "updated"]`

**Query 2 — mentions:**
- jql: `comment ~ "712020:c477e852-f964-4efb-a488-2338babfd3a7" AND assignee != currentUser() AND resolution = Unresolved AND statusCategory not in ("Done") ORDER BY updated DESC`
- fields: `["summary", "status", "project", "priority", "updated", "assignee", "created", "reporter", "description", "comment", "customfield_10037"]`
- responseContentFormat: `markdown`

**Query 3 — watching:**
- jql: `watcher = currentUser() AND assignee != currentUser() AND resolution = Unresolved AND statusCategory not in ("Done") ORDER BY updated DESC`
- fields: `["summary", "status", "project", "priority", "updated", "assignee"]`

**Query 4 — delegated:**
- jql: `reporter = currentUser() AND assignee != currentUser() AND resolution = Unresolved AND statusCategory not in ("Done") ORDER BY updated DESC`
- fields: `["summary", "status", "project", "priority", "updated", "assignee", "reporter"]`

**Query 5 — cross_project:**
- jql: `project in (CO, AF, JIRA, SJIRA) AND issuetype in ("Server Request", "Customer Deployment", "Engineering Task", "Support Ticket") AND resolution = Unresolved ORDER BY updated DESC`
- fields: `["summary", "status", "project", "priority", "updated", "assignee"]`

**Query 6 — activity:**
- jql: `project = DEVOPS AND status changed DURING (startOfWeek(), now()) AND assignee != currentUser() ORDER BY updated DESC`
- fields: `["summary", "status", "project", "updated", "assignee"]`

**Query 7 — backlog:**
- jql: `project = DEVOPS AND assignee is EMPTY AND resolution = Unresolved ORDER BY created DESC`
- fields: `["summary", "status", "project", "priority", "updated", "created", "comment", "description", "customfield_10037"]`
- responseContentFormat: `markdown`

**Query 8 — completed:**
- jql: `assignee = currentUser() AND statusCategory = "Done" AND updated >= startOfMonth() ORDER BY updated DESC`
- fields: `["summary", "status", "project", "updated"]`

**Query 9 — blocked_candidates:**
- jql: `status = Blocked AND project in (DEVOPS, CO, AF, JIRA, SJIRA) AND assignee != currentUser() AND resolution = Unresolved ORDER BY updated DESC`
- fields: `["summary", "status", "project", "priority", "updated", "assignee", "issuelinks"]`

**Query 10a — my_epics:**
- jql: `issuetype = Epic AND assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC`
- fields: `["summary", "status", "project"]`

**Query 10b — recent_subtasks:**
- jql: `issuetype in subTaskIssueTypes() AND assignee != currentUser() AND created >= -14d AND resolution = Unresolved AND project = DEVOPS ORDER BY created DESC`
- fields: `["summary", "status", "project", "priority", "updated", "assignee", "parent", "created"]`

**Query 11 — broad_cross_project:**
- jql: `project not in (DEVOPS) AND (labels = devops OR summary ~ "DevOps" OR component = DevOps) AND resolution = Unresolved AND statusCategory not in ("Done") ORDER BY updated DESC`
- fields: `["summary", "status", "project", "priority", "updated", "assignee", "labels", "components"]`

## Step 2: Assemble and run signal detection

The hook has already saved each slimmed query result to `/tmp/jira-inbox-parts/<bucket>.json`. Do NOT read the individual query results — run the assembly and signal scripts:

```bash
uv run ~/.claude/skills/jira-inbox/scripts/assemble.py && uv run ~/.claude/skills/jira-inbox/scripts/signals.py
```

`assemble.py` combines the parts into `/tmp/jira-inbox.json`. `signals.py` reads that and writes `/tmp/jira-inbox-signals.json`.

## Step 3: Spawn the analyst agent

Read `/tmp/jira-inbox-signals.json` and extract `analysis_requests` and `no_bullshit_list`.

If `analysis_requests` is empty, skip to Step 4 with no agent flags.

Otherwise, spawn the `jira-inbox-analyst` agent in **foreground** using the Agent tool with `subagent_type: "jira-inbox-analyst"` and `model: "sonnet"`. Pass the full JSON content of `/tmp/jira-inbox-signals.json` as the task prompt. The analysis_requests already contain pre-digested ticket data (description, ac, comments) from the search results — the agent does NOT need any tools.

The agent returns pipe-delimited lines. Save its output to `/tmp/jira-inbox-agent-flags.txt`.

## Step 4: Render signals + bucket summary

Run the renderer in default mode (signals + bucket counts):
```bash
uv run ~/.claude/skills/jira-inbox/scripts/render.py /tmp/jira-inbox.json --signals /tmp/jira-inbox-signals.json --agent-flags /tmp/jira-inbox-agent-flags.txt
```

If Step 3 was skipped (no analysis requests), omit the `--agent-flags` argument:
```bash
uv run ~/.claude/skills/jira-inbox/scripts/render.py /tmp/jira-inbox.json --signals /tmp/jira-inbox-signals.json
```

Output the rendered markdown directly. Do NOT add commentary or follow-up questions yet.

## Step 5: Interactive triage of action items

After presenting the signals + summary, walk through each **Action Required** item one at a time. For each item:

1. Present the ticket key, summary, signal, and reason
2. Include relevant context from the search data (the analyst already digested comments/description — use that)
3. Ask the user what the play is (e.g., "What's the play here?")
4. Wait for user response before moving to the next item

Once all action items are triaged, move to Step 6.

## Step 6: Per-bucket drill-down

After action items are handled, ask the user which bucket they want to see. When they name one, render it:

```bash
uv run ~/.claude/skills/jira-inbox/scripts/render.py /tmp/jira-inbox.json --bucket <bucket_name>
```

Valid bucket names: `my_work`, `mentions`, `watching`, `delegated`, `cross_project`, `activity`, `backlog`, `completed`.

Output the rendered table. Repeat for each bucket the user requests. Do NOT proactively show all buckets.
