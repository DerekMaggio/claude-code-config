#!/bin/bash
# prepare_from_urls.sh
# Clones repositories from Git URLs to a specified directory and generates a config file
# Usage: ./prepare_from_urls.sh <input_config_json> <clone_directory>
# Input JSON format:
#   {
#     "repositories": [
#       {
#         "name": "repo-name",
#         "path": "https://github.com/org/repo.git"
#       }
#     ]
#   }
# Output: Generates <input-file-name>-local.json with local paths to cloned repositories

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

input_config="$1"
clone_dir="$2"

require_args 2 "$input_config" "$clone_dir"

# Validate input file exists
if [ ! -f "$input_config" ]; then
    echo "Error: Input config file not found: $input_config" >&2
    exit 1
fi

# Validate input is valid JSON
if ! jq empty "$input_config" 2>/dev/null; then
    echo "Error: Input config is not valid JSON" >&2
    exit 1
fi

# Generate output filename
output_config="${input_config%.json}-local.json"

# Create clone directory if it doesn't exist
mkdir -p "$clone_dir"
echo "Using clone directory: $clone_dir"
echo "Cloning repositories..."
echo ""

# Build array of repository objects with local paths
repos_json="[]"

while IFS= read -r repo; do
    name=$(echo "$repo" | jq -r '.name')
    url=$(echo "$repo" | jq -r '.path')

    # Check if this is a URL (starts with http/https/git@)
    if [[ "$url" =~ ^(https?://|git@) ]]; then
        echo "Cloning $name from $url..."
        clone_path="$clone_dir/$name"

        # Clone the repository
        if git clone "$url" "$clone_path" 2>&1; then
            echo "  ✓ Cloned to: $clone_path"
            echo ""

            # Add to repos array
            repos_json=$(echo "$repos_json" | jq --arg name "$name" --arg path "$clone_path" \
                '. += [{"name": $name, "path": $path}]')
        else
            echo "  ✗ Failed to clone $name" >&2
            exit 1
        fi
    else
        # It's already a local path, just copy it over
        echo "Using local path for $name: $url"
        echo ""

        repos_json=$(echo "$repos_json" | jq --arg name "$name" --arg path "$url" \
            '. += [{"name": $name, "path": $path}]')
    fi
done < <(jq -c '.repositories[]' "$input_config")

# Create the final JSON structure
jq -n --argjson repos "$repos_json" '{"repositories": $repos}' > "$output_config"

echo "✓ Configuration file created: $output_config"
echo "✓ Repositories cloned to: $clone_dir"
