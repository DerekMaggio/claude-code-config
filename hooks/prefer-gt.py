#!/usr/bin/env python3
"""PreToolUse hook — enforce graphite (gt) over raw git for commit/push.

Runs on every Bash call and self-detects which commit/push/PR command the
user is running. Denies with the mode-appropriate message.

Bypass with [raw-git] in the command for intentional raw-git use (recovery,
setup).
"""

from __future__ import annotations

import re
import sys

from _hook_utils import (
    BYPASS_RAW_GIT,
    DenyMode,
    HookInput,
    deny,
)

# Match a subcommand only at a shell-command boundary (start of line, after
# ;, &, |, (, &&, ||, $(, or newline). Avoids false positives from the
# substring appearing inside a string literal or unrelated command.
_BOUNDARY = r"(?:^|[;&|(\n]|&&|\|\||\$\()\s*"

PATTERNS: dict[DenyMode, re.Pattern[str]] = {
    DenyMode.COMMIT:    re.compile(_BOUNDARY + r"git\s+commit\b"),
    DenyMode.PUSH:      re.compile(_BOUNDARY + r"git\s+push\b"),
    DenyMode.PR_CREATE: re.compile(_BOUNDARY + r"gh\s+pr\s+create\b"),
    DenyMode.PR_MERGE:  re.compile(_BOUNDARY + r"gh\s+pr\s+merge\b"),
    DenyMode.GT_BASH:   re.compile(_BOUNDARY + r"gt\s+(?:create|modify|submit)\b"),
}

_BYPASS_SUFFIX = (
    f" If you truly need the raw CLI (recovery, setup), include "
    f"{BYPASS_RAW_GIT} in the command."
)

MESSAGES: dict[DenyMode, str] = {
    DenyMode.COMMIT: (
        "Use 'gt create --all -m \"…\"' instead of 'git commit'. Raw git "
        "bypasses graphite stack tracking and can desync your stack."
        + _BYPASS_SUFFIX
    ),
    DenyMode.PUSH: (
        "Use 'gt submit --no-interactive' instead of 'git push'. Raw git "
        "bypasses graphite stack tracking." + _BYPASS_SUFFIX
    ),
    DenyMode.PR_CREATE: (
        "Use 'gt submit --no-interactive' instead of 'gh pr create'. "
        "Creating PRs directly bypasses graphite's stack linkage — the "
        "resulting PR won't be marked as stacked on its parent." + _BYPASS_SUFFIX
    ),
    DenyMode.PR_MERGE: (
        "Avoid 'gh pr merge' in a stacked workflow. Merge the bottom PR via "
        "graphite (merge-when-ready on submit, or the Graphite web UI) so "
        "the rest of the stack is rebased onto main correctly." + _BYPASS_SUFFIX
    ),
    DenyMode.GT_BASH: (
        "Prefer the graphite MCP tool (mcp__graphite__run_gt_cmd) for "
        "commit-producing 'gt' commands. Its structured 'args' array avoids "
        "shell-quoting landmines in commit messages (backticks, newlines, $). "
        "Read-only gt commands (log, ls, checkout, pr) via Bash are fine."
        + _BYPASS_SUFFIX
    ),
}


def detect_mode(command: str) -> DenyMode | None:
    for mode, pattern in PATTERNS.items():
        if pattern.search(command):
            return mode
    return None


def main() -> None:
    payload = HookInput.from_stdin()
    if payload is None:
        sys.exit(0)

    command = payload.bash_command
    if not command or BYPASS_RAW_GIT in command:
        sys.exit(0)

    mode = detect_mode(command)
    if mode is None:
        sys.exit(0)

    deny(MESSAGES[mode])


if __name__ == "__main__":
    main()
