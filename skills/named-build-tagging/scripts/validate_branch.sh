#!/bin/bash
# validate_branch.sh
# Validates that a branch exists in a repository
# Usage: ./validate_branch.sh <repo_path> <branch_name>
# Exit code: 0 if branch exists, 1 if not

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
branch_name="$2"

require_args 2 "$repo_path" "$branch_name"
cd_repo "$repo_path"
git rev-parse --verify "$branch_name" >/dev/null 2>&1
