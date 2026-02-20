"""Minimal MCP server wrapping the Gemini CLI."""

import asyncio
import json
import logging
import os
from enum import Enum
from typing import Optional

from fastmcp import FastMCP

DEBUG = os.environ.get("GEMINI_BRIDGE_DEBUG", "").lower() in ("1", "true", "yes")
log = logging.getLogger("gemini-bridge")
log.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [GEMINI-BRIDGE] %(levelname)s %(message)s"))
log.addHandler(handler)
log.propagate = False

mcp = FastMCP("gemini-bridge")

FALLBACK_CHAIN = [
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]


class GeminiModel(str, Enum):
    PRO_3 = "gemini-3-pro-preview"
    PRO_2_5 = "gemini-2.5-pro"
    FLASH_2_5 = "gemini-2.5-flash"


class ApprovalMode(str, Enum):
    YOLO = "yolo"
    AUTO_EDIT = "auto_edit"
    PLAN = "plan"


async def _run_gemini(
    prompt: str,
    model: str,
    approval_mode: str = "yolo",
    include_dir: Optional[str] = None,
) -> tuple[int, str, str]:
    """Execute gemini CLI and return (returncode, stdout, stderr)."""
    cmd = [
        "gemini",
        "-m", model,
        "--output-format", "json",
        "--approval-mode", approval_mode,
    ]
    if include_dir:
        cmd.extend(["--include-directories", include_dir])
    cmd.extend(["-p", prompt])

    log.debug("Executing: %s", " ".join(cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    log.debug("Exit code: %d", proc.returncode)
    log.debug("Stdout (%d bytes): %s", len(stdout), stdout[:500])
    log.debug("Stderr (%d bytes): %s", len(stderr), stderr[:500])
    return proc.returncode, stdout.decode(), stderr.decode()


@mcp.tool
async def gemini_query(
    prompt: str,
    model: GeminiModel = GeminiModel.PRO_3,
    approval_mode: ApprovalMode = ApprovalMode.YOLO,
    include_directory: Optional[str] = None,
    auto_fallback: bool = True,
) -> str:
    """Send a prompt to Gemini CLI and return the raw response.

    Args:
        prompt: The prompt to send to Gemini.
        model: Which Gemini model to use. Defaults to gemini-3-pro-preview.
        approval_mode: Controls tool approval. yolo=auto-approve all, auto_edit=auto-approve edits only, plan=read-only, default=prompt for approval.
        include_directory: Optional directory outside the workspace to include.
        auto_fallback: If True, automatically retry with cheaper models on quota exhaustion.
    """
    log.debug("gemini_query called: model=%s, approval_mode=%s, auto_fallback=%s, prompt=%s", model, approval_mode, auto_fallback, prompt[:100])
    suffix = " Return results as a raw JSON object. No conversational text."
    full_prompt = prompt + suffix

    models_to_try = (
        FALLBACK_CHAIN[FALLBACK_CHAIN.index(model.value):]
        if auto_fallback
        else [model.value]
    )

    log.debug("Models to try: %s", models_to_try)

    last_error = ""
    for m in models_to_try:
        log.debug("Trying model: %s", m)
        rc, stdout, stderr = await _run_gemini(full_prompt, m, approval_mode.value, include_directory)

        if rc == 0 and stdout.strip():
            log.debug("Success with model %s", m)
            return stdout.strip()

        if rc == 53 or "exhausted your capacity" in stderr:
            last_error = f"Quota exhausted for {m}"
            log.debug("Quota exhausted for %s, falling back", m)
            continue

        if rc != 0:
            return json.dumps({
                "error": True,
                "model": m,
                "exit_code": rc,
                "stderr": stderr.strip(),
            })

    return json.dumps({
        "error": True,
        "message": f"All models exhausted. Last: {last_error}",
    })


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
