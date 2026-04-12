"""Shared constants, types, and helpers for PreToolUse hooks.

All hooks in this directory follow the same wire contract with Claude Code:
stdin receives a JSON payload; stdout emits a structured decision JSON and
the process exits 0. (Per the hooks spec, exit 2 causes Claude Code to
ignore any JSON body — so structured denials must exit 0.)
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# ── Tool names (wire values) ──────────────────────────────────────────────────

TOOL_BASH = "Bash"
TOOL_GT_MCP = "mcp__graphite__run_gt_cmd"

# ── Hook protocol (wire values) ───────────────────────────────────────────────

HOOK_EVENT = "PreToolUse"
DECISION_DENY = "deny"

# ── Graphite ──────────────────────────────────────────────────────────────────

MESSAGE_FLAGS = ("-m", "--message")
MESSAGE_FLAG_EQ = "--message="

# ── Bypass tokens ─────────────────────────────────────────────────────────────

BYPASS_RAW_GIT = "[raw-git]"
BYPASS_DOCS_DEFAULT = "[docs-ok]"

# ── Env ───────────────────────────────────────────────────────────────────────

ENV_PROJECT_DIR = "CLAUDE_PROJECT_DIR"


class DenyMode(str, Enum):
    """Which raw action the prefer-gt hook is gating."""
    COMMIT = "commit"
    PUSH = "push"
    PR_CREATE = "pr-create"
    PR_MERGE = "pr-merge"
    GT_BASH = "gt-bash"


class GtSubcommand(str, Enum):
    """gt subcommands that produce or amend a commit."""
    CREATE = "create"
    MODIFY = "modify"


COMMIT_PRODUCING_RE = re.compile(
    r"git\s+commit|gt\s+(?:" + "|".join(s.value for s in GtSubcommand) + r")"
)


def is_commit_producing(command: str) -> bool:
    return bool(COMMIT_PRODUCING_RE.search(command))


_BASH_HEREDOC_MSG_RE = re.compile(
    r"""-m\s+"\$\(cat\s+<<'?EOF'?\s*\n(.*?)\n\s*EOF""",
    re.DOTALL,
)
_BASH_DOUBLE_QUOTED_MSG_RE = re.compile(r'-m\s+"([^"]+)"')
_BASH_SINGLE_QUOTED_MSG_RE = re.compile(r"-m\s+'([^']+)'")


def _extract_bash_commit_message(command: str) -> str | None:
    if not is_commit_producing(command):
        return None
    for pattern in (
        _BASH_HEREDOC_MSG_RE,
        _BASH_DOUBLE_QUOTED_MSG_RE,
        _BASH_SINGLE_QUOTED_MSG_RE,
    ):
        m = pattern.search(command)
        if m:
            return m.group(1).strip()
    return None


@dataclass(frozen=True)
class HookInput:
    """Parsed stdin payload with unified access across tool shapes."""
    tool_name: str
    tool_input: dict

    @classmethod
    def from_stdin(cls) -> HookInput | None:
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError:
            return None
        return cls(
            tool_name=data.get("tool_name", ""),
            tool_input=data.get("tool_input", {}),
        )

    @property
    def bash_command(self) -> str:
        return self.tool_input.get("command", "")

    @property
    def gt_args(self) -> list[str]:
        return self.tool_input.get("args", []) or []

    @property
    def is_gt_mcp(self) -> bool:
        return self.tool_name == TOOL_GT_MCP

    def normalized_command(self) -> str:
        """Return a shell-like command string for either tool shape."""
        if self.is_gt_mcp:
            args = self.gt_args
            return "gt " + " ".join(shlex.quote(a) for a in args) if args else ""
        return self.bash_command

    def gt_message(self) -> str | None:
        """Extract -m/--message from gt create/modify (MCP form)."""
        args = self.gt_args
        if not args or args[0] not in {s.value for s in GtSubcommand}:
            return None
        for i, a in enumerate(args):
            if a in MESSAGE_FLAGS and i + 1 < len(args):
                return args[i + 1].strip()
            if a.startswith(MESSAGE_FLAG_EQ):
                return a.split("=", 1)[1].strip()
        return None

    def commit_message(self) -> str | None:
        """Commit message from either Bash (-m / heredoc) or MCP (args)."""
        if self.is_gt_mcp:
            return self.gt_message()
        return _extract_bash_commit_message(self.bash_command)

    def bypass_haystack(self) -> str:
        """Text to scan for bypass tokens — covers both command and message."""
        return self.normalized_command() + " " + (self.commit_message() or "")


@dataclass(frozen=True)
class DocsCheckConfig:
    """Shape of .claude/docs-check.json."""
    doc_file: str
    bypass_token: str = BYPASS_DOCS_DEFAULT
    safe_pattern: str = ""
    custom_instructions: str = ""

    @classmethod
    def load(cls, path: Path) -> DocsCheckConfig | None:
        try:
            with path.open() as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        doc_file = raw.get("doc_file", "")
        if not doc_file:
            return None
        return cls(
            doc_file=doc_file,
            bypass_token=raw.get("bypass_token", BYPASS_DOCS_DEFAULT),
            safe_pattern=raw.get("safe_pattern", ""),
            custom_instructions=raw.get("custom_instructions", ""),
        )


def project_root() -> str:
    return os.environ.get(ENV_PROJECT_DIR) or os.getcwd()


def deny(reason: str) -> None:
    """Emit structured deny and exit 0. JSON is ignored on exit 2."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": DECISION_DENY,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def staged_files() -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            cwd=project_root(), text=True, stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line for line in out.splitlines() if line]
