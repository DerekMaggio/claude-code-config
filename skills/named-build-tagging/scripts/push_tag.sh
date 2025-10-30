#!/bin/bash
# push_tag.sh
# Pushes a tag to the remote repository
# Usage: ./push_tag.sh <repo_path> <tag_name> [--force]
# Exit code: 0 if successful, 1 if failed

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
tag_name="$2"
force_flag="${3:-}"

require_args 2 "$repo_path" "$tag_name"
cd_repo "$repo_path"

# Push tag with optional force flag
if [ "$force_flag" = "--force" ]; then
    git push --force origin "$tag_name"
else
    git push origin "$tag_name"
fi
