---
name: gha-analyze
description: Perform root cause analysis on a GitHub workflow run. Fetches logs, identifies failure points, and suggests fixes.
argument-hint: [run-id]
---

SKIP MODE SELECTION

RUN_ID="${0:-}"

if [[ -z "$RUN_ID" ]]; then
  echo "ERROR: Run ID required for analysis"
  echo "Usage: /gha-analyze <run-id>"
  exit 1
fi

echo "=== WORKFLOW FAILURE ANALYSIS ==="
echo ""
echo "Analyzing run ID: $RUN_ID"
echo ""

# Fetch comprehensive workflow metadata
echo "=== WORKFLOW METADATA ==="
gh run view "$RUN_ID" --json name,conclusion,status,headBranch,headSha,event,createdAt,displayTitle,workflowName,url 2>/dev/null || {
  echo "ERROR: Could not fetch workflow details. Check that run ID $RUN_ID exists."
  exit 1
}

echo ""
echo "=== FAILURE SUMMARY ==="
./skills/gha-analyze/scripts/summarize-failures.sh "$RUN_ID"

echo ""
echo "=== FILTERED ERROR LOGS ==="
echo "(Highlighting key failure patterns)"
echo ""
gh run view "$RUN_ID" --log-failed 2>/dev/null | ./skills/gha-analyze/scripts/filter-errors.sh || {
  echo "No failed logs available (workflow may still be running or succeeded)"
}

echo ""
echo "=== ERROR CONTEXT ==="
echo "(Showing lines surrounding failure points)"
echo ""
gh run view "$RUN_ID" --log-failed 2>/dev/null | ./skills/gha-analyze/scripts/extract-context.sh

echo ""
echo "=== ANALYSIS REQUIRED ==="
echo ""
echo "Please analyze the above workflow failure and provide:"
echo "1. ROOT CAUSE: What specifically caused the failure?"
echo "2. EXPLANATION: Why did this happen?"
echo "3. FIX: What concrete steps should be taken to resolve it?"
echo ""
echo "If this is a test failure, infrastructure issue, or deployment problem,"
echo "identify the specific component, service, or configuration at fault."
echo ""

exit 0
