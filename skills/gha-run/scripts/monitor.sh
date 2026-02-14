#!/bin/bash
# skills/gha-run/scripts/monitor.sh

set -euo pipefail

RUN_ID="$1"

# Use stderr for status updates so they don't interfere with variable capture if needed
echo "[+] Monitoring Run: ${RUN_ID}" >&2
echo -n "Polling" >&2

while true; do
  STATUS=$(gh run view "${RUN_ID}" --json status --jq '.status' 2>/dev/null || echo "unknown")

  if [[ "${STATUS}" == "completed" ]]; then
    echo -e "\n[+] Workflow complete" >&2
    break
  fi

  if [[ "${STATUS}" == "unknown" ]]; then
    echo -e "\n[!] Status query failed" >&2
  fi
  
  # Heartbeat to keep the session alive and provide visual feedback
  echo -n "." >&2
  sleep 15
done

exit 0