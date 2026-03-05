# Agents

Claude Code subagents. Automatically available in all sessions via symlinks in `~/.claude/agents/`.

Agents are split into `public/` (shareable) and `private/` (personal, gitignored submodule).

## Public Agents

### Project Management
| Agent | Description |
|---|---|
| `triage-sheriff` | Transforms ambiguous DevOps requests into bounded, justified Parent MVRs |
| `task-architect` | Decomposes an approved Parent MVR into discrete, 8-hour, verifiable Child MVTs |

### Python
| Agent | Description |
|---|---|
| `python-class-architect` | Design and implement Python classes with OOP best practices |
| `python-refactoring-specialist` | Refactor Python code for clarity, maintainability, and testability |
| `python-test-architect` | Generate comprehensive pytest coverage with dependency injection patterns |

### Testing
| Agent | Description |
|---|---|
| `goss-test-architect` | Create and maintain Goss YAML test suites for infrastructure validation |

### Utility
| Agent | Description |
|---|---|
| `brain-dump-refiner` | Structure messy technical thoughts into clear, actionable specs |
| `install4j-doc-expert` | Tiered install4j documentation lookup (quick → detailed → source) |
| `subagent-architect` | Design and write new Claude Code subagent definitions to disk |
| `voice-transcription-cleaner` | Clean speech-to-text transcriptions of technical content |

## Private Agents

Stored in `agents/private/` (gitignored submodule). Includes:

| Agent | Description |
|---|---|
| `ansible-architect` | Design and implement production-grade Ansible playbooks and roles |
| `interview-prep` | Prepare for job interviews — research, practice questions, STAR responses |
| `project-summarizer` | Generate professional project descriptions for resumes, LinkedIn, portfolios |
