---
name: sonarqube-report-summarizer
description: Generate weekly SonarQube summary reports from downloaded JSON exports. Runs summarize.py across all dated report folders and produces Obsidian-formatted markdown summaries with week-over-week diffs.
allowed-tools: [Bash, Read]
---

SKIP MODE SELECTION

## Step 1: Resolve Paths

Set the following constants:

- `VAULT_DIR` — `vault_path` from devops config
- `WORKFLOW_DIR` — `$VAULT_DIR/Workflows/sonarqube-report-summarizer`

## Step 2: Verify Report Data Exists

Check that at least one dated folder (`MM-DD-YYYY-sonarqube-report/`) exists in `$WORKFLOW_DIR` and contains a `reports/` subdirectory with JSON files.

```bash
ls -d "$WORKFLOW_DIR"/*-sonarqube-report/reports/ 2>/dev/null
```

If no folders are found, output:
> `[!] No report folders found in $WORKFLOW_DIR. Download SonarQube reports first into a folder named MM-DD-YYYY-sonarqube-report/reports/`

Then stop.

## Step 3: Run the Summarizer

```bash
cd "$WORKFLOW_DIR" && python3 summarize.py
```

If the script exits non-zero, output the error and stop.

## Step 4: Identify the Latest Summary

Find the most recent dated folder and its generated summary file:

```bash
ls -d "$WORKFLOW_DIR"/*-sonarqube-report | sort | tail -1
```

The summary will be at: `<latest-folder>/<date>-sonarqube-summary.md`

## Step 5: Confirm

Output:
```
[+] Summaries generated for all report folders.
[+] Latest: <latest-folder>/<date>-sonarqube-summary.md
```

Then read and display the **Overall Summary** and **Overall New Issues This Week** sections from the latest summary file to give the user a quick view of the results.
