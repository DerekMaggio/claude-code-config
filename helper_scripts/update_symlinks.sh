#!/bin/bash

# helper_scripts/update_symlinks.sh
# This script ensures that the local Claude configuration (~/.claude/) 
# is properly symlinked to this repository.

set -e

# Get the absolute path to the repository root
REPO_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CLAUDE_CONFIG_DIR="$HOME/.claude"

echo "Updating Claude Code symlinks from $REPO_PATH..."

# Ensure ~/.claude directory exists
mkdir -p "$CLAUDE_CONFIG_DIR"

# --- AGENTS ---
mkdir -p "$CLAUDE_CONFIG_DIR/agents"
agent_count=0
if [ -d "$REPO_PATH/agents" ]; then
  for subdir in "$REPO_PATH"/agents/*/; do
    [ -e "$subdir" ] || continue
    subdir_name=$(basename "$subdir")
    target="$CLAUDE_CONFIG_DIR/agents/$subdir_name"
    if [ -d "$target" ] && [ ! -L "$target" ]; then
      backup_path="${target}.backup.$(date +%Y%m%d_%H%M%S)"
      echo "  [WARN] Backing up existing $target → $backup_path"
      mv "$target" "$backup_path"
    fi
    [ -L "$target" ] && rm "$target"
    ln -s "$subdir" "$target"
    agent_count=$((agent_count + 1))
  done
fi
echo "  [OK] agents/ — $agent_count group(s) linked"

# --- SKILLS ---
mkdir -p "$CLAUDE_CONFIG_DIR/skills"
skill_count=0
if [ -d "$REPO_PATH/skills" ]; then
  for skill in "$REPO_PATH"/skills/*/; do
    [ -e "$skill" ] || continue
    skill_name=$(basename "$skill")
    target="$CLAUDE_CONFIG_DIR/skills/$skill_name"
    if [ -d "$target" ] && [ ! -L "$target" ]; then
      backup_path="${target}.backup.$(date +%Y%m%d_%H%M%S)"
      echo "  [WARN] Backing up existing $target → $backup_path"
      mv "$target" "$backup_path"
    fi
    [ -L "$target" ] && rm "$target"
    ln -s "$skill" "$target"
    skill_count=$((skill_count + 1))
  done
fi
echo "  [OK] skills/ — $skill_count skill(s) linked"

# --- MCP SERVERS ---
if [ -f "$REPO_PATH/.mcp.json" ]; then
  target="$CLAUDE_CONFIG_DIR/.mcp.json"
  if [ -f "$target" ] && [ ! -L "$target" ]; then
    backup_path="${target}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "  [WARN] Backing up existing $target → $backup_path"
    mv "$target" "$backup_path"
  fi
  ln -sf "$REPO_PATH/.mcp.json" "$target"
fi

claude mcp remove gemini-bridge --scope user 2>/dev/null || true
claude mcp add --scope user --transport http gemini-bridge http://localhost:8000/mcp > /dev/null
claude mcp remove pr-index --scope user 2>/dev/null || true
claude mcp add --scope user --transport http pr-index http://localhost:8001/mcp > /dev/null
echo "  [OK] MCP servers — gemini-bridge, pr-index registered (user scope)"

# --- STATUSLINE ---
if [ -f "$REPO_PATH/statusline-command.sh" ]; then
  ln -sf "$REPO_PATH/statusline-command.sh" "$CLAUDE_CONFIG_DIR/statusline-command.sh"
fi

# --- CLAUDE.md ---
ln -sf "$REPO_PATH/CLAUDE.md" "$CLAUDE_CONFIG_DIR/CLAUDE.md"

# --- SETTINGS ---
if [ -f "$REPO_PATH/settings.json" ]; then
  ln -sf "$REPO_PATH/settings.json" "$CLAUDE_CONFIG_DIR/settings.json"
fi

# --- SETUP SCRIPT ---
ln -sf "$REPO_PATH/setup.sh" "$CLAUDE_CONFIG_DIR/setup.sh"

# --- DEVOPS CONFIG ---
if [ -f "$REPO_PATH/config/devops.json" ]; then
  ln -sf "$REPO_PATH/config/devops.json" "$CLAUDE_CONFIG_DIR/devops.json"
else
  echo "  [WARN] No config/devops.json found — copy config/devops.example.json and fill in values"
fi

# --- INJECT SCRIPT ---
ln -sf "$REPO_PATH/helper_scripts/inject_devops_config.sh" "$CLAUDE_CONFIG_DIR/inject_devops_config.sh"

# --- HOOKS ---
if [ -d "$REPO_PATH/hooks" ]; then
  target="$CLAUDE_CONFIG_DIR/hooks"
  if [ -d "$target" ] && [ ! -L "$target" ]; then
    backup_path="${target}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "  [WARN] Backing up existing $target → $backup_path"
    mv "$target" "$backup_path"
  fi
  [ -L "$target" ] && rm "$target"
  ln -s "$REPO_PATH/hooks" "$target"
  hook_count=$(find "$REPO_PATH/hooks" -maxdepth 1 \( -name "*.sh" -o -name "*.py" \) | wc -l | tr -d ' ')
  echo "  [OK] hooks/ — $hook_count hook(s) linked"
fi

echo ""
echo "[OK] Symlinks updated"
echo "     Tip: run 'git submodule update --init' if you added new private agents"
