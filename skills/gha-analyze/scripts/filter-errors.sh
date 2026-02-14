#!/bin/bash
# Filters GitHub workflow logs for error patterns and removes noise.

# Common error patterns to highlight
PATTERNS="error|fail|exception|fatal|denied|timed out|invalid|not found|conflict"

# 1. Remove timestamps (standard GH format: 2023-10-27T10:00:00.0000000Z)
# 2. Filter for lines matching patterns (case-insensitive)
# 3. Remove overly verbose lines (like progress bars)

grep -Ei "$PATTERNS" | 
sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+Z //' | 
grep -vE "\[INFO\]|Download|Extracting|Resolving|Progress:"
