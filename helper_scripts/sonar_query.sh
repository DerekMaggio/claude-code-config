#!/bin/bash

# SonarQube Cloud API Query Script
# Usage: cat token_file | ./sonar_query.sh --host <host> --project <key> --pr <number> [options]

set -e

# Read token from stdin
SONAR_TOKEN=$(cat)

# Default values
SONAR_HOST="https://sonarcloud.io"

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            SONAR_HOST="$2"
            shift 2
            ;;
        --project)
            PROJECT_KEY="$2"
            shift 2
            ;;
        --pr)
            PR_NUMBER="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --rules)
            RULES="$2"
            shift 2
            ;;
        --new-only)
            NEW_ONLY="true"
            shift
            ;;
        -h|--help)
            cat << EOF
Usage: cat token_file | $0 [options]

Options:
    --host          SonarQube host (default: https://sonarcloud.io)
    --project       Project key
    --pr            Pull request number
    --branch        Branch name
    --rules         Comma-separated rule keys
    --new-only      Only show new issues (sets sinceLeakPeriod=true)
    -h, --help      Show this help message

Examples:
    cat token.txt | $0 --project myorg_myrepo --pr 123
    cat token.txt | $0 --project myorg_myrepo --branch develop
    cat token.txt | $0 --project myorg_myrepo --pr 123 --new-only
    cat token.txt | $0 --project myorg_myrepo --pr 123 --rules java:S1234,python:S5678
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Build query string conditionally
QUERY_PARAMS=""

if [ -n "$PROJECT_KEY" ]; then
    QUERY_PARAMS="${QUERY_PARAMS}&componentKeys=${PROJECT_KEY}"
fi

if [ -n "$PR_NUMBER" ]; then
    QUERY_PARAMS="${QUERY_PARAMS}&pullRequest=${PR_NUMBER}"
fi

if [ -n "$BRANCH" ]; then
    QUERY_PARAMS="${QUERY_PARAMS}&branch=${BRANCH}"
fi

if [ -n "$RULES" ]; then
    QUERY_PARAMS="${QUERY_PARAMS}&rules=${RULES}"
fi

if [ "$NEW_ONLY" = "true" ]; then
    QUERY_PARAMS="${QUERY_PARAMS}&sinceLeakPeriod=true"
fi

# Add resolved=false as default
QUERY_PARAMS="${QUERY_PARAMS}&resolved=false"

# Remove leading & if present
QUERY_PARAMS="${QUERY_PARAMS#&}"

# Pagination logic
PAGE=1
PAGE_SIZE=500
ALL_ISSUES="[]"
FIRST_RESPONSE=""

while true; do
    # Make request with pagination
    RESPONSE=$(curl --silent --fail-with-body \
        --request GET \
        --url "${SONAR_HOST}/api/issues/search?${QUERY_PARAMS}&ps=${PAGE_SIZE}&p=${PAGE}" \
        --header "Authorization: Bearer ${SONAR_TOKEN}")

    # Save first response to get metadata
    if [ "$PAGE" -eq 1 ]; then
        FIRST_RESPONSE="$RESPONSE"
    fi

    # Extract issues from current page and merge using stdin to avoid arg length limits
    ALL_ISSUES=$(printf '%s\n%s' "$ALL_ISSUES" "$(echo "$RESPONSE" | jq -c '.issues')" | jq -c -s '.[0] + .[1]')

    # Check if there are more pages
    TOTAL=$(echo "$RESPONSE" | jq -r '.paging.total')
    CURRENT_COUNT=$((PAGE * PAGE_SIZE))

    if [ "$CURRENT_COUNT" -ge "$TOTAL" ]; then
        break
    fi

    PAGE=$((PAGE + 1))
done

# Output combined result with original structure but all issues
printf '%s\n%s' "$FIRST_RESPONSE" "$ALL_ISSUES" | jq -s '.[0] as $resp | .[1] as $issues | $resp | .issues = $issues | .paging.pageSize = ($issues | length)'
