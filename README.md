# Claude Code Configuration Manager

> **Summary:** A centralized, version-controlled repository for managing Claude Code agents, skills, and configuration.

This repository is designed to make your Claude Code environment **reproducible**, **shareable**, and **reliable**. It manages global instructions (`CLAUDE.md`), specialized sub-agents, and workflow skills.

## 🚀 Quick Start

To set up your Claude environment using this configuration:

1. **Clone the repository** (include private submodules):
   ```bash
   git clone --recurse-submodules https://github.com/DerekMaggio/claude-code-config.git ~/workspace/claude-code-config
   cd ~/workspace/claude-code-config
   ```

2. **Initialize and Link**:
   Run the automated setup script to create symlinks from `~/.claude/` to this repository:
   ```bash
   ./helper_scripts/update_symlinks.sh
   ```

3. **Verify**:
   Run `claude` and check if it picks up your custom agents and skills.

## 🏗️ Repository Structure

- `agents/`: Specialized AI assistants with separate context windows.
  - `public/`: Publicly available agents.
  - `private/`: Private agents managed via Git submodule.
- `skills/`: Reusable capability packages (e.g., PR generation, tagging).
- `helper_scripts/`: Maintenance scripts for the configuration.
- `CLAUDE.md`: Global instructions and operational policies for Claude.
- `.claudeignore`: Patterns to exclude from Claude's context.

## 🛠️ Maintenance

### Adding New Skills/Agents
Simply add them to the respective directories and run the update script:
```bash
./helper_scripts/update_symlinks.sh
```

### Updating Private Agents
```bash
git submodule update --remote --merge
```

## 📜 Workflow Principles

For a reliable experience with Claude Code:
1. **Script-Based Skills**: Keep execution logic in bash scripts and instructions in `SKILL.md`.
2. **Atomic Commits**: Follow the conventional commit policy defined in `CLAUDE.md`.
3. **Context Management**: Use `.claudeignore` and specialized agents to keep your context window clean.
4. **Zero-Analysis Rule**: Use the `@gemini-bridge` agent for discovery tasks involving many files.

---
*Created with the help of Claude Code.*
