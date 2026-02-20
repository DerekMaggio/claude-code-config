#!/bin/bash

# helper_scripts/update_symlinks.sh
# This script ensures that the local Claude configuration (~/.claude/) 
# is properly symlinked to this repository.

set -e

# Get the absolute path to the repository root
REPO_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CLAUDE_CONFIG_DIR="$HOME/.claude"

echo "🚀 Updating Claude Code symlinks from $REPO_PATH..."

# Ensure ~/.claude directory exists
mkdir -p "$CLAUDE_CONFIG_DIR"

# --- AGENTS ---
echo "🤖 Syncing agents..."
mkdir -p "$CLAUDE_CONFIG_DIR/agents"

# Symlink each subdirectory in agents/ to ~/.claude/agents/
if [ -d "$REPO_PATH/agents" ]; then
  for subdir in "$REPO_PATH"/agents/*/; do
    [ -e "$subdir" ] || continue
    subdir_name=$(basename "$subdir")
    target="$CLAUDE_CONFIG_DIR/agents/$subdir_name"
    
    # Backup if it's a real directory and not a symlink
    if [ -d "$target" ] && [ ! -L "$target" ]; then
      backup_path="${target}.backup.$(date +%Y%m%d_%H%M%S)"
      echo "⚠️  Backing up existing directory $target to $backup_path"
      mv "$target" "$backup_path"
    fi

    # Remove existing symlink to prevent dereferencing issues
    if [ -L "$target" ]; then
      rm "$target"
    fi
    
    echo "🔗 Linking agents/$subdir_name"
    ln -s "$subdir" "$target"
  done
fi

# --- SKILLS ---
echo "🛠️  Syncing skills..."
mkdir -p "$CLAUDE_CONFIG_DIR/skills"

# Symlink each subdirectory in skills/ to ~/.claude/skills/
if [ -d "$REPO_PATH/skills" ]; then
  for skill in "$REPO_PATH"/skills/*/; do
    [ -e "$skill" ] || continue
    skill_name=$(basename "$skill")
    target="$CLAUDE_CONFIG_DIR/skills/$skill_name"
    
    # Backup if it's a real directory and not a symlink
    if [ -d "$target" ] && [ ! -L "$target" ]; then
      backup_path="${target}.backup.$(date +%Y%m%d_%H%M%S)"
      echo "⚠️  Backing up existing directory $target to $backup_path"
      mv "$target" "$backup_path"
    fi

    # Remove existing symlink to prevent dereferencing issues
    if [ -L "$target" ]; then
      rm "$target"
    fi
    
    echo "🔗 Linking skills/$skill_name"
    ln -s "$skill" "$target"
  done
fi

# --- MCP SERVERS ---
echo "🌐 Syncing MCP server config..."
if [ -f "$REPO_PATH/.mcp.json" ]; then
  target="$CLAUDE_CONFIG_DIR/.mcp.json"

  # Backup if it's a real file and not a symlink
  if [ -f "$target" ] && [ ! -L "$target" ]; then
    backup_path="${target}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "⚠️  Backing up existing file $target to $backup_path"
    mv "$target" "$backup_path"
  fi

  echo "🔗 Linking .mcp.json"
  ln -sf "$REPO_PATH/.mcp.json" "$target"
else
  echo "⏭️  No .mcp.json found in repo, skipping"
fi

# Register user-scoped MCP servers (global across all projects)
echo "🌐 Registering user-scoped MCP servers..."
claude mcp remove gemini-bridge --scope user 2>/dev/null || true
claude mcp add --scope user --transport http gemini-bridge http://localhost:8000/mcp
echo "✅ Registered gemini-bridge (user scope)"

# --- STATUSLINE ---
echo "📊 Linking statusline-command.sh..."
if [ -f "$REPO_PATH/statusline-command.sh" ]; then
  ln -sf "$REPO_PATH/statusline-command.sh" "$CLAUDE_CONFIG_DIR/statusline-command.sh"
else
  echo "⏭️  No statusline-command.sh found in repo, skipping"
fi

# --- CLAUDE.md ---
echo "📝 Linking CLAUDE.md..."
ln -sf "$REPO_PATH/CLAUDE.md" "$CLAUDE_CONFIG_DIR/CLAUDE.md"

# --- SETTINGS ---
echo "⚙️  Linking settings.json..."
if [ -f "$REPO_PATH/settings.json" ]; then
  ln -sf "$REPO_PATH/settings.json" "$CLAUDE_CONFIG_DIR/settings.json"
fi

# --- DEVOPS CONFIG ---
echo "🔐 Linking devops config..."
if [ -f "$REPO_PATH/config/devops.json" ]; then
  ln -sf "$REPO_PATH/config/devops.json" "$CLAUDE_CONFIG_DIR/devops.json"
  echo "🔗 Linked config/devops.json"
else
  echo "⚠️  No config/devops.json found. Copy config/devops.example.json to config/devops.json and fill in your values."
fi

# --- INJECT SCRIPT ---
echo "💉 Linking inject_devops_config.sh..."
ln -sf "$REPO_PATH/helper_scripts/inject_devops_config.sh" "$CLAUDE_CONFIG_DIR/inject_devops_config.sh"

echo "✅ Symlinks updated successfully!"
echo "Note: If you added new private agents, ensure submodules are initialized: git submodule update --init"
