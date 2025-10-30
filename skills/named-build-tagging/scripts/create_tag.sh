#!/bin/bash
# create_tag.sh
# Creates an annotated tag in a repository
# Usage: ./create_tag.sh <repo_path> <tag_name> <commit_sha> <tag_message> [--force]
# Exit code: 0 if successful, 1 if failed

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
tag_name="$2"
commit_sha="$3"
tag_message="$4"
force_flag="${5:-}"

require_args 4 "$repo_path" "$tag_name" "$commit_sha" "$tag_message"
cd_repo "$repo_path"

# Create tag with optional force flag
if [ "$force_flag" = "--force" ]; then
    git tag -f -a "$tag_name" "$commit_sha" -m "$tag_message"
else
    git tag -a "$tag_name" "$commit_sha" -m "$tag_message"
fi
