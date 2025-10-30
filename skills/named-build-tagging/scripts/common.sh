#!/bin/bash
# common.sh
# Common functions and utilities for named-build-tagging scripts
# Source this file at the beginning of other scripts

# Validates that a path is absolute
# Usage: validate_absolute_path <path>
# Exit: 1 if path is not absolute
validate_absolute_path() {
    local path="$1"
    if [[ "$path" != /* ]]; then
        echo "Error: Path must be absolute: $path" >&2
        exit 1
    fi
}

# Validates that required arguments are provided
# Usage: require_args <arg_count> <arg1> <arg2> ...
# Exit: 1 if any required argument is missing
require_args() {
    local required_count="$1"
    shift
    local provided_count="$#"
    
    if [ "$provided_count" -lt "$required_count" ]; then
        echo "Error: Missing required arguments" >&2
        exit 1
    fi
    
    for arg in "$@"; do
        if [ -z "$arg" ]; then
            echo "Error: Empty argument provided" >&2
            exit 1
        fi
    done
}

# Changes to a repository directory with validation
# Usage: cd_repo <repo_path>
# Exit: 1 if path is invalid or not a git repo
cd_repo() {
    local repo_path="$1"
    validate_absolute_path "$repo_path"
    
    if [ ! -d "$repo_path" ]; then
        echo "Error: Repository path does not exist: $repo_path" >&2
        exit 1
    fi
    
    if [ ! -d "$repo_path/.git" ]; then
        echo "Error: Not a git repository: $repo_path" >&2
        exit 1
    fi
    
    cd "$repo_path"
}
