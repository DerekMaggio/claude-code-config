---
name: gha-analyze
description: Perform root cause analysis on a GitHub workflow run. Fetches logs, identifies failure points, and suggests fixes.
argument-hint: [run-id]
allowed-tools: [Bash, github.actions_get, github.actions_list, github.get_job_logs]
---

SKIP MODE SELECTION

## Arguments
- `$0` — Workflow Run ID

## Step 1: Validate Arguments

If `$0` (run ID) is missing, output:
> "ERROR: Run ID required."
> Usage: `/gha-analyze <run-id>`

Then stop.

## Step 2: Detect Repository

Run via Bash:
```bash
git remote get-url origin
```

Parse `owner` and `repo` from the URL:
- SSH: `git@github.com:owner/repo.git`
- HTTPS: `https://github.com/owner/repo.git`

## Step 3: Fetch Run Metadata

Use `mcp__github__actions_get` with:
- `method`: `get_workflow_run`
- `owner`: detected owner
- `repo`: detected repo
- `resource_id`: `$0`

Display: workflow name, conclusion, branch, commit SHA, event type, and run URL.

## Step 4: List Jobs

Use `mcp__github__actions_list` with:
- `method`: `list_workflow_jobs`
- `owner`: detected owner
- `repo`: detected repo
- `resource_id`: `$0`

Display each job: name, conclusion, and any failed steps with exit codes.

## Step 5: Fetch Failed Logs

Use `mcp__github__get_job_logs` with:
- `owner`: detected owner
- `repo`: detected repo
- `run_id`: `$0` (as a number)
- `failed_only`: `true`
- `return_content`: `true`

## Step 6: Root Cause Analysis

Analyze the metadata, job results, and logs. Provide:

1. **ROOT CAUSE**: What specifically caused the failure?
2. **EXPLANATION**: Why did this happen?
3. **FIX**: What concrete steps should be taken to resolve it?

If this is a test failure, infrastructure issue, or deployment problem, identify the specific component, service, or configuration at fault.
