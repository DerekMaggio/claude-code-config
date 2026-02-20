#!/usr/bin/env bash
# Setup script for the gemini-bridge MCP server.
#
# Builds and starts the Docker-based Gemini CLI MCP server, then registers it
# with Claude Code so it is available as mcp__gemini-bridge.
#
# Usage:
#   ./setup.sh [--workspace <path>] [--skip-register]
#
# Options:
#   --workspace <path>   Directory to mount into the container as /workspace
#                        (overrides $WORKSPACE_MOUNT env var, required if neither is set)
#   --skip-register      Skip updating ~/.claude/settings.json
#
# Prerequisites:
#   - Docker with the Compose plugin (docker compose)
#   - Gemini CLI authenticated (run `gemini` once to complete OAuth)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETTINGS_FILE="$HOME/.claude/settings.json"
MCP_SERVER_NAME="gemini-bridge"
MCP_URL="http://localhost:8000/mcp"

WORKSPACE_MOUNT="${WORKSPACE_MOUNT:-}"
SKIP_REGISTER=false

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace)
            WORKSPACE_MOUNT="$2"
            shift 2
            ;;
        --skip-register)
            SKIP_REGISTER=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--workspace <path>] [--skip-register]"
            exit 1
            ;;
    esac
done

echo "=== gemini-bridge MCP server setup ==="
echo ""

# --- Prerequisite checks ---
check_prereq() {
    local cmd="$1" hint="$2"
    if ! command -v "$cmd" &>/dev/null; then
        echo "[ERROR] '$cmd' not found. $hint"
        exit 1
    fi
}

check_prereq docker "Install Docker: https://docs.docker.com/get-docker/"
if ! docker compose version &>/dev/null; then
    echo "[ERROR] Docker Compose plugin not found. Install it: https://docs.docker.com/compose/install/"
    exit 1
fi
check_prereq jq "Install jq: sudo apt-get install -y jq"

echo "[OK] Prerequisites satisfied"

# --- Gemini CLI auth check ---
GEMINI_DIR="$HOME/.gemini"
if [[ ! -d "$GEMINI_DIR" ]]; then
    echo ""
    echo "[WARN] ~/.gemini not found — Gemini CLI may not be authenticated."
    echo "       Run 'gemini' once interactively to complete OAuth, then re-run this script."
    read -rp "Continue anyway? [y/N] " cont
    [[ "${cont,,}" == "y" ]] || exit 1
else
    echo "[OK] ~/.gemini exists"
fi

# --- Workspace mount ---
if [[ -z "$WORKSPACE_MOUNT" ]]; then
    echo ""
    read -rp "Enter the workspace directory to mount into the container: " WORKSPACE_MOUNT
fi

WORKSPACE_MOUNT="$(realpath "$WORKSPACE_MOUNT")"

if [[ ! -d "$WORKSPACE_MOUNT" ]]; then
    echo "[ERROR] Workspace directory does not exist: $WORKSPACE_MOUNT"
    exit 1
fi

echo "[OK] Workspace: $WORKSPACE_MOUNT"

# --- Build and start ---
echo ""
echo "[BUILD] Building gemini-bridge Docker image..."
WORKSPACE_MOUNT="$WORKSPACE_MOUNT" docker compose -f "$SCRIPT_DIR/docker-compose.yml" build --quiet

echo "[START] Starting gemini-bridge container..."
WORKSPACE_MOUNT="$WORKSPACE_MOUNT" docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d

echo "[OK] Container started"

# --- Health check ---
echo ""
echo "[CHECK] Waiting for MCP server to be ready..."
for i in $(seq 1 15); do
    if curl -sf "http://localhost:8000/" &>/dev/null; then
        echo "[OK] MCP server is ready at $MCP_URL"
        break
    fi
    if [[ $i -eq 15 ]]; then
        echo "[WARN] Server did not respond within 15s — check logs:"
        echo "       docker compose -f $SCRIPT_DIR/docker-compose.yml logs"
    fi
    sleep 1
done

# --- Register with Claude Code ---
if [[ "$SKIP_REGISTER" == false ]]; then
    echo ""
    echo "[REGISTER] Adding $MCP_SERVER_NAME to $SETTINGS_FILE..."

    if [[ ! -f "$SETTINGS_FILE" ]]; then
        echo "{}" > "$SETTINGS_FILE"
    fi

    # Merge the mcpServers entry using jq, preserving all existing config
    local_settings=$(cat "$SETTINGS_FILE")
    updated=$(echo "$local_settings" | jq \
        --arg name "$MCP_SERVER_NAME" \
        --arg url "$MCP_URL" \
        '.mcpServers[$name] = {"type": "http", "url": $url}')

    echo "$updated" > "$SETTINGS_FILE"
    echo "[OK] Registered as mcp__${MCP_SERVER_NAME}"
    echo ""
    echo "  Restart Claude Code (or run /mcp refresh) for the server to appear."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "  Container:    docker compose -f $SCRIPT_DIR/docker-compose.yml ps"
echo "  Logs:         docker compose -f $SCRIPT_DIR/docker-compose.yml logs -f"
echo "  Stop:         docker compose -f $SCRIPT_DIR/docker-compose.yml down"
echo "  MCP endpoint: $MCP_URL"
