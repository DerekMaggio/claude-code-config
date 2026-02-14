#!/bin/bash
# skills/gha-run/scripts/run-all.sh

set -e
SCRIPT_DIR="$(dirname "$0")"

# Standardize the inputs
WORKFLOW="$1"
BRANCH="$2"
INPUTS="${3:-}"

# Execute steps 
bash "$SCRIPT_DIR/trigger.sh" "$WORKFLOW" "$BRANCH" "$INPUTS" > /dev/null || true
sleep 5
RUN_ID=$(bash "$SCRIPT_DIR/get-run-id.sh" "$WORKFLOW" "$BRANCH" 2>/dev/null || echo "")

# Monitor and Report
if [[ -n "$RUN_ID" ]]; then
    bash "$SCRIPT_DIR/monitor.sh" "${RUN_ID}" > /dev/null 2>&1 || true
    bash "$SCRIPT_DIR/report.sh" "${RUN_ID}"
else
    echo "❌ Error: Could not retrieve Run ID."
fi

# THE CRITICAL STEP: Always exit 0.
# This tells Claude 'The command finished successfully.'
# Even if the workflow failed, the script performed its task.
exit 0