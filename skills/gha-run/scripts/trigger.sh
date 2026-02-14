#!/bin/bash
# Trigger a GitHub Actions workflow

set -euo pipefail

WORKFLOW_FILE="$1"
BRANCH="$2"
INPUTS="${3:-}"

echo "[+] Triggering: ${WORKFLOW_FILE} (${BRANCH})"

if [[ -z "${INPUTS}" ]]; then
  gh workflow run "${WORKFLOW_FILE}" --ref "${BRANCH}" || echo "[!] FAILED: workflow trigger."
else
  # Parse inputs in format "key1=value1 key2=value2" and convert to -f flags
  INPUT_FLAGS=""
  for input in ${INPUTS}; do
    INPUT_FLAGS="${INPUT_FLAGS} -f ${input}"
  done
  gh workflow run "${WORKFLOW_FILE}" --ref "${BRANCH}" ${INPUT_FLAGS} || echo "[!] FAILED: workflow trigger."
fi

echo "[+] Trigger sequence complete"
exit 0
