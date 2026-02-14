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

# --- CLAUDE.md ---
echo "📝 Linking CLAUDE.md..."
ln -sf "$REPO_PATH/CLAUDE.md" "$CLAUDE_CONFIG_DIR/CLAUDE.md"

echo "✅ Symlinks updated successfully!"
echo "Note: If you added new private agents, ensure submodules are initialized: git submodule update --init"
