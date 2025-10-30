#!/bin/bash
# validate_repositories.sh
# Validates that all repository paths exist and are valid git repositories
# Usage: ./validate_repositories.sh "path1" "path2" "path3" ...
# Exit code: 0 if all valid, 1 if any invalid
# Output: "OK: <path>" for valid repos, "MISSING: <path>" or "NOT A GIT REPO: <path>" for invalid

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

has_error=0

for repo in "$@"; do
    validate_absolute_path "$repo"

    if [ ! -d "$repo" ]; then
        echo "MISSING: $repo"
        has_error=1
    elif [ ! -d "$repo/.git" ]; then
        echo "NOT A GIT REPO: $repo"
        has_error=1
    else
        echo "OK: $repo"
    fi
done

exit $has_error
