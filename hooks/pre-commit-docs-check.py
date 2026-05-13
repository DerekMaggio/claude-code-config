#!/usr/bin/env python3
"""PreToolUse hook — Documentation freshness check.

Fires before every commit-producing call: `git commit`, `gt create`, or
`gt modify` — invoked via Bash or the graphite MCP tool. Reads project-level
config from .claude/docs-check.json in the project root.

Project config schema (see DocsCheckConfig):
    {
      "doc_file":      "MAINTENANCE_NOTES.md",
      "bypass_token":  "[docs-ok]",
      "safe_pattern":  "^(MAINTENANCE_NOTES\\.md|CLAUDE\\.md|\\.claude/)"
    }

If .claude/ exists but no docs-check.json is found, denies and prompts
Claude to create the config. If no .claude/ directory exists, silently skips.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _hook_utils import (
    DocsCheckConfig,
    HookInput,
    deny,
    is_commit_producing,
    project_root,
    staged_files,
)

COMBINED_ADD_COMMIT_RE = re.compile(r"git\s+add.*&&.*git\s+commit")

CLAUDE_DIR = ".claude"
CONFIG_FILENAME = "docs-check.json"

# Root-level doc filenames (any extension variant).
DOC_CANDIDATE_NAMES = (
    "README", "CHANGELOG", "CONTRIBUTING", "CHANGES", "HISTORY",
    "NOTES", "MAINTAINERS", "AUTHORS", "NOTICE",
)
DOC_CANDIDATE_EXTS = ("", ".txt", ".markdown", ".mkd", ".md")

# Conventional docs directories — entries under these get hoisted in the
# candidate listing since they're typically the real project doc home.
DOC_DIRS = ("docs", "doc", "documentation")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}


def is_combined_add_commit(command: str) -> bool:
    # Strip everything after -m so commit-message content doesn't trip the match.
    stripped = re.sub(r"-m.*", "", command)
    return bool(COMBINED_ADD_COMMIT_RE.search(stripped))


def in_doc_dir(rel: Path) -> bool:
    return bool(rel.parts) and rel.parts[0] in DOC_DIRS


def find_doc_candidates(root: Path) -> list[str]:
    markdown: list[str] = []
    for md in root.rglob("*.md"):
        rel = md.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        markdown.append(str(rel))
    # Hoist conventional docs-dir entries first, alphabetical within each group.
    markdown.sort(key=lambda p: (not in_doc_dir(Path(p)), p))

    named = [
        f"{name}{ext}"
        for name in DOC_CANDIDATE_NAMES
        for ext in DOC_CANDIDATE_EXTS
        if (root / f"{name}{ext}").is_file()
    ]
    return list(dict.fromkeys(named + markdown))


def deny_missing_config(root: Path) -> None:
    candidates = find_doc_candidates(root)
    print("DOCS CHECK — no .claude/docs-check.json found", file=sys.stderr)
    print("Candidate doc files (docs dirs listed first):", file=sys.stderr)
    for c in candidates or ["(none found)"]:
        print(f"  {c}", file=sys.stderr)
    deny(
        "Missing .claude/docs-check.json configuration. Please create it "
        "with at minimum a 'doc_file' field pointing to the project doc to "
        "gate. See candidate files listed on stderr (docs/ entries first)."
    )


def check_freshness(cfg: DocsCheckConfig) -> None:
    staged = staged_files()
    if not staged:
        return

    if cfg.safe_pattern:
        safe_re = re.compile(cfg.safe_pattern)
        non_safe = [f for f in staged if not safe_re.search(f)]
    else:
        non_safe = list(staged)

    if not non_safe or cfg.doc_file in staged:
        return

    if cfg.custom_instructions:
        reason = (
            f"{cfg.custom_instructions} Option B: If no update is needed, "
            f"add {cfg.bypass_token} to your commit message."
        )
    else:
        reason = (
            f"Review {cfg.doc_file} before committing. Option A: Update the "
            f"doc, stage it, then retry. Option B: If no update is needed, "
            f"add {cfg.bypass_token} to your commit message."
        )
    deny(reason)


def main() -> None:
    payload = HookInput.from_stdin()
    if payload is None:
        sys.exit(0)

    command = payload.normalized_command()
    if not command or not is_commit_producing(command):
        sys.exit(0)

    if is_combined_add_commit(command):
        deny(
            "Do not combine git add and git commit in one command. Run git "
            "add first, then git commit separately so the docs check hook "
            "can inspect the staged file list."
        )

    root = Path(project_root())
    config_path = root / CLAUDE_DIR / CONFIG_FILENAME
    cfg = DocsCheckConfig.load(config_path)
    if cfg is None:
        # Missing config is an error only when .claude/ exists (project opts in).
        if (root / CLAUDE_DIR).is_dir() and not config_path.exists():
            deny_missing_config(root)
        sys.exit(0)

    if cfg.bypass_token in payload.bypass_haystack():
        sys.exit(0)

    check_freshness(cfg)


if __name__ == "__main__":
    main()
