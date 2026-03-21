#!/usr/bin/env python3
"""PreToolUse hook — Conventional commit message validation.

Fires before every git commit. Validates the commit message against
the conventional commits spec with scope-sensitive misuse prevention.

Expected format: type(optional-scope): description [TICKET-ID]

Test:
    echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"feat(api): add endpoint [#7]\""}}' | python3 hooks/pre-commit-conventional-commit.py
"""

import json
import re
import sys

ALLOWED_TYPES = frozenset(
    ["fix", "feat", "ci", "docs", "chore", "refactor", "test", "perf", "build", "style"]
)

# These types must NOT appear as a scope inside another type.
# e.g. feat(ci): is invalid — use ci: directly.
STANDALONE_TYPES = frozenset(["ci", "docs", "style", "test", "perf", "build"])

# Matches: type(optional-scope): description [TICKET-ID]
# The ticket ID can be various formats: [#7], [DEVOPS-123], [GH-42], etc.
COMMIT_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[a-z0-9_/ -]+)\))?"
    r"(?P<breaking>!)?"
    r":\s+"
    r"(?P<description>.+)"
)

TICKET_RE = re.compile(r"\[.+?\]")


def deny(reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(2)


def extract_commit_message(tool_input: dict) -> str | None:
    """Extract the commit message from the git commit command."""
    command = tool_input.get("command", "")
    if not re.search(r"git\s+commit", command):
        return None

    # Try -m flag with various quoting styles
    # Handles: -m "msg", -m 'msg', -m "$(cat <<'EOF'\nmsg\nEOF\n)"
    heredoc_match = re.search(
        r"""-m\s+"\$\(cat\s+<<'?EOF'?\s*\n(.*?)\n\s*EOF""",
        command,
        re.DOTALL,
    )
    if heredoc_match:
        return heredoc_match.group(1).strip()

    quoted_match = re.search(r'-m\s+"([^"]+)"', command)
    if quoted_match:
        return quoted_match.group(1).strip()

    single_match = re.search(r"-m\s+'([^']+)'", command)
    if single_match:
        return single_match.group(1).strip()

    return None


def validate_commit_message(message: str) -> str | None:
    """Validate a commit message. Returns error string or None if valid."""
    # Take only the first line (subject line) for validation
    subject = message.split("\n")[0].strip()

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

    # Check scope-sensitive misuse: feat(ci) should be ci:
    if scope and scope in STANDALONE_TYPES:
        return (
            f"Scope-sensitive misuse: '{commit_type}({scope}):' is not allowed.\n"
            f"  '{scope}' is a standalone type — use '{scope}:' or '{scope}(sub-scope):' directly.\n"
            f"  This prevents unintended version bumps from incorrect prefixes."
        )

    # Check for ticket ID in the description
    if not TICKET_RE.search(description):
        return (
            f"Missing ticket reference in commit message.\n"
            f"  Got:      {subject}\n"
            f"  Expected: type(scope): description [TICKET-ID]\n"
            f"  Examples: [#7], [DEVOPS-123], [GH-42]"
        )

    return None


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    message = extract_commit_message(tool_input)

    # Not a git commit command — pass through
    if message is None:
        sys.exit(0)

    error = validate_commit_message(message)
    if error:
        deny(error)

    # Valid — allow the commit
    sys.exit(0)


if __name__ == "__main__":
    main()
