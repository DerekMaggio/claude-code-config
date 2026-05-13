---
name: gha-assassinate
description: Watch a GitHub Actions workflow on a repo and immediately cancel any run as soon as it starts. Polls every 10 seconds until a run appears (or timeout). Use when the user wants to prevent a specific workflow from running, kill/murder/assassinate a workflow on sight, or block an automated run before it can do damage.
argument-hint: <repo> <workflow> <timeout-seconds>
allowed-tools: [Bash]
context: fork
disable-model-invocation: false
updated: 2026-05-12
---

SKIP MODE SELECTION

## Arguments
- `$0` — Repo. Either `owner/repo` or just `repo` (owner inferred from current `git remote`, else `AgreeYa-HuLoop`).
- `$1` — Workflow identifier. Filename (`deploy.yml`), numeric ID, or display name (`"Deploy to Prod"`).
- `$2` — Timeout in seconds. Total wall-clock budget for the poll loop.

## Execute

Run the bundled script via Bash:

```bash
bash "$CLAUDE_PLUGIN_ROOT/skills/gha-assassinate/assassinate.sh" "$0" "$1" "$2"
```

If `$CLAUDE_PLUGIN_ROOT` is not set, fall back to:

```bash
bash ~/.claude/skills/gha-assassinate/assassinate.sh "$0" "$1" "$2"
```

The script handles arg validation, owner/repo resolution, workflow matching (by filename, numeric id, or display name — case-insensitive), 10-second polling, 60-second heartbeats, immediate cancel-on-detection (with force-cancel fallback), and a final deterministic report.

Exit codes from the script:
- `0` — run was detected and cancellation attempted (see report), OR timeout reached with no run.
- `2` — workflow identifier matched zero workflows; script listed available workflows on stderr.
- `3` — workflow identifier matched multiple workflows; script listed candidates on stderr.

## Report

Present the script's stdout/stderr verbatim. Do NOT add analysis, RCA, or "next steps".

If exit code is `2` or `3`, use `AskUserQuestion` to let the user pick from the listed candidates, then re-invoke with the disambiguated identifier.

## Notes
- Requires `gh` CLI authenticated for the target org and `jq` on PATH.
- Cancel sequence is intentionally aggressive: `cancel` → `force-cancel`. The user's intent is to kill the run, not wind it down cleanly.
