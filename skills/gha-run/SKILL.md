---
name: gha-run
description: Trigger and monitor a GH workflow. If the workflow fails, the agent will offer to perform root cause analysis using the gha-analyze skill.
argument-hint: [workflow-file] [branch] [optional: inputs]
context: fork
disable-model-invocation: false
---

SKIP MODE SELECTION

# 1. Validation
if [ -z "$0" ] || [ -z "$1" ]; then
  echo "[!] ERROR: Workflow and Branch required."
  exit 0
fi

# 2. Trigger
bash skills/gha-run/scripts/trigger.sh "$0" "$1" "$ARGUMENTS[2]" || true

# 3. ID Retrieval
sleep 5
RUN_ID=$(bash skills/gha-run/scripts/get-run-id.sh "$0" "$1" || echo "")

# 4. Monitor

if [ -n "$RUN_ID" ] && [ "$RUN_ID" != "null" ]; then

  bash skills/gha-run/scripts/monitor.sh "${RUN_ID}" || true

fi



# The agent will see the RUN_ID and can fetch the final status itself.

echo "FINISHED_RUN_ID=${RUN_ID}"
