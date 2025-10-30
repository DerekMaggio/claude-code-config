#!/bin/bash
# delete_tag.sh
# Deletes a local tag from a repository
# Usage: ./delete_tag.sh <repo_path> <tag_name>
# Exit code: 0 if successful, 1 if failed

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
tag_name="$2"

require_args 2 "$repo_path" "$tag_name"
cd_repo "$repo_path"
git tag -d "$tag_name"
