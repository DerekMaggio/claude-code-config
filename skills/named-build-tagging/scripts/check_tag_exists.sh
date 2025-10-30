#!/bin/bash
# check_tag_exists.sh
# Checks if a tag exists in a repository and optionally gets its commit SHA
# Usage: ./check_tag_exists.sh <repo_path> <tag_name>
# Exit code: Always 0
# Output: "FOUND <SHA>" if tag exists, "NOT_FOUND" if not

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
tag_name="$2"

require_args 2 "$repo_path" "$tag_name"
cd_repo "$repo_path"

# Check if tag exists
if git tag -l "$tag_name" | grep -q "^${tag_name}$"; then
    # Get the SHA the tag points to
    sha=$(git rev-list -n 1 "$tag_name")
    echo "FOUND $sha"
else
    echo "NOT_FOUND"
fi

exit 0
