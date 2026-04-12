#!/usr/bin/env python3
"""PreToolUse hook — Conventional commit message validation.

Fires before every commit-producing call: `git commit`, `gt create`, or
`gt modify` — invoked via Bash or the graphite MCP tool. Validates the
commit message against the conventional commits spec with scope-sensitive
misuse prevention.

Expected format: type(optional-scope): description [TICKET-ID]

Test:
    echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \\"feat(api): add endpoint [#7]\\""}}' | python3 hooks/pre-commit-conventional-commit.py
    echo '{"tool_name":"mcp__graphite__run_gt_cmd","tool_input":{"args":["create","-m","feat(api): add endpoint [#7]"]}}' | python3 hooks/pre-commit-conventional-commit.py
"""

from __future__ import annotations

import re
import sys

from _hook_utils import HookInput, deny

ALLOWED_TYPES = frozenset([
    "fix", "feat", "ci", "docs", "chore", "refactor",
    "test", "perf", "build", "style",
])

# Scope-sensitive misuse: e.g. feat(ci) should be ci: directly.
STANDALONE_TYPES = frozenset(["ci", "docs", "style", "test", "perf", "build"])

COMMIT_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[a-z0-9_/ -]+)\))?"
    r"(?P<breaking>!)?"
    r":\s+"
    r"(?P<description>.+)"
)

TICKET_RE = re.compile(r"\[.+?\]")


def validate(message: str) -> str | None:
    subject = message.split("\n", 1)[0].strip()
    match = COMMIT_RE.match(subject)
    if not match:
        return (
            f"Invalid conventional commit format.\n"
            f"  Got:      {subject}\n"
            f"  Expected: type(optional-scope): description [TICKET-ID]\n"
            f"  Allowed types: {', '.join(sorted(ALLOWED_TYPES))}"
        )

    commit_type = match.group("type")
    scope = match.group("scope")
    description = match.group("description")

    if commit_type not in ALLOWED_TYPES:
        return (
            f"Unknown commit type: '{commit_type}'.\n"
            f"  Allowed types: {', '.join(sorted(ALLOWED_TYPES))}"
        )

    if scope and scope in STANDALONE_TYPES:
        return (
            f"Scope-sensitive misuse: '{commit_type}({scope}):' is not allowed.\n"
            f"  '{scope}' is a standalone type — use '{scope}:' or "
            f"'{scope}(sub-scope):' directly.\n"
            f"  This prevents unintended version bumps from incorrect prefixes."
        )

    if not TICKET_RE.search(description):
        return (
            f"Missing ticket reference in commit message.\n"
            f"  Got:      {subject}\n"
            f"  Expected: type(scope): description [TICKET-ID]\n"
            f"  Examples: [#7], [DEVOPS-123], [GH-42]"
        )
    return None


def main() -> None:
    payload = HookInput.from_stdin()
    if payload is None:
        sys.exit(0)

    message = payload.commit_message()
    if message is None:
        sys.exit(0)

    error = validate(message)
    if error:
        deny(error)


if __name__ == "__main__":
    main()
