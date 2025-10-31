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

# Get the remote name
remote=$(get_remote)

# Fetch latest
git fetch "$remote" --quiet 2>&1

if [ -z "$ref" ]; then
    # Get default branch
    git remote set-head "$remote" --auto 2>&1 >/dev/null
    ref=$(git symbolic-ref "refs/remotes/$remote/HEAD" | sed "s@^refs/remotes/$remote/@@")
    ref="$remote/$ref"
else
    # Always use remote - prefix with remote/ if not already a remote ref
    if [[ ! "$ref" =~ / ]]; then
        ref="$remote/$ref"
    fi
fi

# Get commit info
git rev-parse --short "$ref"
git log -1 --pretty="%s" "$ref"
git log -1 --pretty="%an on %ad" --date=short "$ref"
echo "$ref"
