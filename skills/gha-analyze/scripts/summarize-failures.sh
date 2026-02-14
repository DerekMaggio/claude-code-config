#!/bin/bash
# Provides a concise summary of failed jobs and their specific failed steps.

RUN_ID=$1

if [[ -z "$RUN_ID" ]]; then
  echo "Usage: $0 <run-id>"
  exit 1
fi

echo "=== FAILURE SUMMARY ==="
gh run view "$RUN_ID" --json jobs --jq '.jobs[] | select(.conclusion=="failure") | "Job: \(.name)
Failed Steps: " + ([(.steps[] | select(.conclusion=="failure") | " - \(.name) (Exit Code: \(.number))")] | join("
"))'
