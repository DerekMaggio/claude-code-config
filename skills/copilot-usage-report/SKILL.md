---
name: copilot-usage-report
description: Pulls GitHub Copilot usage metrics and seat activity for the org, compiles them into a markdown report, and saves it to the Obsidian vault.
allowed-tools: [Bash, Write]
---

SKIP MODE SELECTION

## Step 1: Resolve Paths

Set the following constants for use in subsequent steps:

- `SKILL_DIR` — the directory containing this SKILL.md file
- `VAULT_DIR` — `vault_path` from devops config
- `OUTPUT_DIR` — `$VAULT_DIR/Generated Documents/Analysis`
- `REPORT_FILE` — `$OUTPUT_DIR/GitHub_Copilot_Usage_Report_$(date +%Y-%m-%d).md`
- `TMP_METRICS` — `/tmp/copilot_metrics.json`
- `TMP_SEATS` — `/tmp/copilot_seats.json`

## Step 2: Fetch Data

Run both API calls via Bash (use `github_org` from devops config):

```bash
gh api /orgs/{github_org}/copilot/metrics > /tmp/copilot_metrics.json 2>&1
gh api /orgs/{github_org}/copilot/billing/seats > /tmp/copilot_seats.json 2>&1
```

If either file contains `"message"` at the top level (indicating a GitHub API error), output:
> `[!] ERROR: GitHub API call failed. Ensure your gh token has admin:org or manage_billing:copilot scope.`
> `Details: <message field contents>`

Then stop.

## Step 3: Build Report

Run the build script via Bash:

```bash
uv run "$SKILL_DIR/scripts/build-report.py" /tmp/copilot_metrics.json /tmp/copilot_seats.json
```

Capture the output as `REPORT_CONTENT`. If the script exits non-zero, output the error and stop.

## Step 4: Save Report

Use the **Write** tool to save `REPORT_CONTENT` to `$REPORT_FILE`.

## Step 5: Confirm

Output:
```
[+] Report saved: Generated Documents/Analysis/GitHub_Copilot_Usage_Report_<YYYY-MM-DD>.md
[+] Vault: {vault_path}
```

Then display the full report contents to the user.
