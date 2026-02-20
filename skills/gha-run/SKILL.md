---
name: gha-run
description: Trigger and monitor a GH workflow. If the workflow fails, the agent will offer to perform root cause analysis using the gha-analyze skill.
argument-hint: [workflow-file] [branch] [optional: inputs]
allowed-tools: [Bash, github.actions_run_trigger, github.actions_list, github.actions_get]
context: fork
disable-model-invocation: false
---

SKIP MODE SELECTION

## Arguments
- `$0` — Workflow file name (e.g., `deploy.yml`)
- `$1` — Branch (e.g., `main`)
- `$2` — Optional workflow inputs in `key=value` format (space-separated)

## Step 1: Validate Arguments

If `$0` (workflow file) or `$1` (branch) are missing, output:
> "[!] ERROR: Workflow file and branch are required."
> Usage: `/gha-run <workflow-file> <branch> [inputs]`

Then stop.

## Step 2: Detect Repository

Run via Bash:
```bash
git remote get-url origin
```

Parse `owner` and `repo` from the URL:
- SSH: `git@github.com:owner/repo.git`
- HTTPS: `https://github.com/owner/repo.git`

## Step 3: Trigger Workflow

Use `mcp__github__actions_run_trigger` with:
- `method`: `run_workflow`
- `owner`: detected owner
- `repo`: detected repo
- `workflow_id`: `$0`
- `ref`: `$1`
- `inputs`: if `$2` is provided, parse `key=value` pairs into an object

Output: `[+] Triggered: $0 on $1`

## Step 4: Get Run ID

Wait 5 seconds via Bash (`sleep 5`), then use `mcp__github__actions_list` with:
- `method`: `list_workflow_runs`
- `owner`: detected owner
- `repo`: detected repo
- `resource_id`: `$0`
- `workflow_runs_filter.branch`: `$1`
- `per_page`: 1

Extract the `id` from the first result. If none found, output an error and stop.

## Step 5: Monitor Until Completion

Poll using `mcp__github__actions_get` with:
- `method`: `get_workflow_run`
- `owner`: detected owner
- `repo`: detected repo
- `resource_id`: run ID from Step 4

Check the `status` field:
- If `completed`: proceed to Step 6
- Otherwise: wait 15 seconds via Bash (`sleep 15`) and poll again
- Timeout after 20 attempts (~5 minutes)

## Step 6: Report Result

Output the following deterministic report and do not analyze or interpret:

```
Workflow: <name>
Status:   <conclusion>
Run ID:   <run_id>
URL:      <html_url>
```

## Step 7: RCA on Failure

If `conclusion` is not `success`, automatically invoke the `gha-analyze` skill with the run ID — do not ask first.
