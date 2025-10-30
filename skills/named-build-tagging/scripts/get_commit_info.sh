#!/bin/bash
# get_commit_info.sh
# Gets commit information from a repository's default branch or specified ref
# Usage: ./get_commit_info.sh <repo_path> [branch_or_commit]
# If branch_or_commit is not provided, uses the default branch
# Output format (one per line):
#   Short SHA
#   Commit message (first line)
#   Author and date
#   Branch/ref name used

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
ref="${2:-}"

require_args 1 "$repo_path"
cd_repo "$repo_path"

# Fetch latest
git fetch --quiet 2>&1

if [ -z "$ref" ]; then
    # Get default branch
    git remote set-head origin --auto 2>&1 >/dev/null
    ref=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
fi

# Get commit info
git rev-parse --short "$ref"
git log -1 --pretty="%s" "$ref"
git log -1 --pretty="%an on %ad" --date=short "$ref"
echo "$ref"
