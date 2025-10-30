#!/bin/bash
# validate_commit.sh
# Validates that a commit SHA exists in a repository
# Usage: ./validate_commit.sh <repo_path> <commit_sha>
# Exit code: 0 if commit exists, 1 if not

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
commit_sha="$2"

require_args 2 "$repo_path" "$commit_sha"
cd_repo "$repo_path"
git rev-parse --verify "$commit_sha" >/dev/null 2>&1
