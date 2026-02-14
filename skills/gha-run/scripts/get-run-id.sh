#!/bin/bash
# Get the Run ID for a triggered workflow

set -euo pipefail

WORKFLOW_FILE="$1"
BRANCH="$2"

echo "Waiting 5 seconds for workflow to be registered..."
sleep 5

RUN_ID=$(gh run list --workflow="${WORKFLOW_FILE}" --branch="${BRANCH}" --json databaseId --limit 1 --jq '.[0].databaseId')

if [[ -z "${RUN_ID}" || "${RUN_ID}" == "null" ]]; then
  echo "[!] ERROR: No Run ID found for '${WORKFLOW_FILE}' on branch '${BRANCH}'." >&2
  exit 0
fi

echo "RUN_ID=${RUN_ID}"
echo "${RUN_ID}"
