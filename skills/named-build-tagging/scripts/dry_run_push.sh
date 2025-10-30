#!/bin/bash
# dry_run_push.sh
# Performs a dry run push of a tag to validate it will succeed
# Usage: ./dry_run_push.sh <repo_path> <tag_name>
# Exit code: 0 if dry run succeeds, 1 if failed
# Output: The output from git push --dry-run

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

repo_path="$1"
tag_name="$2"

require_args 2 "$repo_path" "$tag_name"
cd_repo "$repo_path"
git push --dry-run origin "$tag_name"
