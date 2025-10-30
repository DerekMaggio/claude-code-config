# Derek's Claude Configuration

## Git Workflow with GitKraken MCP
- Proactively suggest commits after completing working changes
- Use conventional commit format (feat:, fix:, docs:, refactor:, test:, chore:)
- Make commits small and logical - each representing one complete, working change
- Always ask permission before committing: "Would you like me to commit these changes with: `[conventional commit message]`?"
- Suggest commits when:
  ✅ After adding a complete feature
  ✅ After fixing a bug
  ✅ After updating documentation
  ✅ After refactoring that maintains functionality
  ❌ Never after partial/broken implementations

## GitKraken MCP Usage
- Use GitKraken MCP tools for structured Git operations when possible
- Fall back to Bash Git commands for complex operations not covered by MCP tools
- Never commit automatically - always require explicit user permission

## Pull Request Creation Policy

**CRITICAL: NEVER create pull requests without explicit user approval.**

### Required Process:
1. Draft the PR body text
2. Show it to the user with: "Here's the PR description I've drafted. Should I create it?"
3. Wait for explicit approval ("yes", "looks good", "create it", etc.)
4. Only then use `gh pr create`

### This applies to:
- ALL `gh pr create` commands
- ALL `gh pr edit` commands that modify body or title
- NO EXCEPTIONS - even for "simple" or "obvious" PRs

### Treatment:
Treat PR creation exactly like git commits - ALWAYS get approval first.

**If you find yourself about to run `gh pr create`, STOP and show the user the PR description first.**

## Documentation Style
- **Follow documentation preferences** detailed in `claude_documentation_preferences.md`
- Use consistent structure, emoji hierarchy, and technical precision
- Always include practical examples and troubleshooting sections
- Reference the preferences file when writing or updating any documentation

## Repository Structure

This repository contains both agents and skills for extending Claude Code functionality:

### Agents

Agents are specialized AI assistants with separate context windows:

- **agents/public/** - Publicly shared agents (committed to this repo)
- **agents/private/** - Private agents (Git submodule to private repository)

### Skills

Skills are reusable capability packages that Claude discovers automatically:

- **skills/** - Custom skills for workflows and procedures (committed to this repo)

### Private Agents Submodule

The private agents are stored in a separate private repository and included as a Git submodule. Users without access to the private repo will simply have an empty `agents/private/` directory.

**Initial setup of private submodule:**

```bash
# Add your private agents repo as a submodule
git submodule add https://github.com/DerekMaggio/claude-code-private-agents.git agents/private

# Commit the submodule configuration
git add .gitmodules agents/private
git commit -m "feat: add private agents submodule"
```

**Cloning this repo with private agents:**

```bash
# Clone with submodules initialized
git clone --recurse-submodules https://github.com/DerekMaggio/claude-code-config.git

# Or if already cloned, initialize submodule
git submodule update --init
```

**Updating agents:**

```bash
# Update both public agents and private submodule
git pull origin main
git submodule update --remote --merge

# Commit the updated submodule reference if changes were pulled
git add agents/private
git commit -m "chore: update private agents"
```

**Updating only private agents:**

```bash
# Pull latest changes from private agents repo
cd agents/private
git pull origin main
cd ../..

# Commit the updated submodule reference
git add agents/private
git commit -m "chore: update private agents"
```

## Setup Instructions

This repository should be symlinked to your personal Claude configuration for easy access to agents and settings.

### Required Symlinks

1. **Agents directory**: Link entire `agents/` directory structure to `~/.claude/agents/` (maintains subdirectories)
2. **Skills directory**: Link entire `skills/` directory structure to `~/.claude/skills/` (maintains subdirectories)
3. **Configuration file**: Link CLAUDE.md to `~/.claude/CLAUDE.md`

### Setup Commands

```bash
# Get the current repository path
REPO_PATH=$(pwd)

# Initialize submodules (private agents)
git submodule update --init

# Backup existing agents directory if it exists and is not a symlink
if [ -d ~/.claude/agents ] && [ ! -L ~/.claude/agents ]; then
  mv ~/.claude/agents ~/.claude/agents.backup.$(date +%Y%m%d_%H%M%S)
fi

# Create agents directory
mkdir -p ~/.claude/agents

# Create symlinks for each subdirectory (public and private)
for subdir in "$REPO_PATH"/agents/*/; do
  subdir_name=$(basename "$subdir")
  ln -sf "$subdir" ~/.claude/agents/"$subdir_name"
done

# Backup existing skills directory if it exists and is not a symlink
if [ -d ~/.claude/skills ] && [ ! -L ~/.claude/skills ]; then
  mv ~/.claude/skills ~/.claude/skills.backup.$(date +%Y%m%d_%H%M%S)
fi

# Create skills directory
mkdir -p ~/.claude/skills

# Create symlinks for each skill
for skill in "$REPO_PATH"/skills/*/; do
  skill_name=$(basename "$skill")
  ln -sf "$skill" ~/.claude/skills/"$skill_name"
done

# Create symlink for configuration file (overwrite existing)
ln -sf "$REPO_PATH/CLAUDE.md" ~/.claude/CLAUDE.md
```

### Startup Check

On each session startup, verify these symlinks exist:

- Check if `~/.claude/CLAUDE.md` is a symlink pointing to this repository
- Check if subdirectories in `~/.claude/agents/` (public/, private/) are symlinked to this repository's `agents/` subdirectories
- Check if subdirectories in `~/.claude/skills/` are symlinked to this repository's `skills/` subdirectories
- If symlinks are missing or broken, suggest the setup commands above to the user

This ensures your custom agents, skills, and configuration are always available across all Claude Code sessions.
