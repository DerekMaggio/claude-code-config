#!/bin/bash
# Extracts lines around failure points to provide context for the RCA.

# Usage: extract-context.sh <log_file>

LOG_FILE=$1

if [[ -z "$LOG_FILE" ]]; then
  # Read from stdin if no file provided
  LOG_FILE="/dev/stdin"
fi

# Find line numbers of errors, then show 3 lines before and 2 lines after
grep -niE "error|fail|exception|fatal" "$LOG_FILE" | cut -d: -f1 | sort -u | 
while read line; do
  echo "--- Context around line $line ---"
  sed -n "$((line-3)),$((line+2))p" "$LOG_FILE"
  echo ""
done | 
sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+Z //'
