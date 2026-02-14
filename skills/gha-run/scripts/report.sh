#!/bin/bash
# skills/gha-run/scripts/report.sh
# Deterministic report: fetch status and exit immediately.

set -uo pipefail

RUN_ID="${1:-}"

if [[ -z "$RUN_ID" ]]; then
    echo "ERROR: No Run ID provided."
    exit 0
fi

# Fetch conclusion in a single command
RESULTS=$(gh run view "$RUN_ID" --json conclusion,url,name --jq '{conclusion: .conclusion, url: .url, name: .name}' 2>/dev/null || echo '{"conclusion":"unknown","url":"unknown","name":"unknown"}')
CONCLUSION=$(echo "$RESULTS" | jq -r '.conclusion // "unknown"')
URL=$(echo "$RESULTS" | jq -r '.url // "unknown"')
NAME=$(echo "$RESULTS" | jq -r '.name // "unknown"')

# Single-line deterministic output
echo "Workflow: $NAME"
echo "Status: $CONCLUSION"
echo "Run ID: $RUN_ID"
echo "URL: $URL"

# If failed, optionally fetch logs (but format them non-analytically)
if [[ "$CONCLUSION" != "success" && "$CONCLUSION" != "unknown" ]]; then
    echo "---"
    gh run view "$RUN_ID" --log-failed 2>/dev/null || true
    echo "---"
fi

# Dead-end exit: tells Claude "no interpretation needed"
exit 0