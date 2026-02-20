# gemini-bridge

A minimal MCP server that wraps the [Gemini CLI](https://github.com/google-gemini/gemini-cli), exposing it as a tool Claude Code can call via the `mcp__gemini-bridge` namespace.

Runs as a Docker container. Claude sends prompts to the server; the server executes the Gemini CLI inside the container and returns the response.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Docker + Compose plugin | `docker compose version` must succeed |
| Gemini CLI OAuth | Run `gemini` once on the host to authenticate — credentials land in `~/.gemini` |
| `jq` | Used by the setup script to update `~/.claude/settings.json` |

---

## Setup

```bash
./setup.sh --workspace /path/to/your/project
```

This will:
1. Verify prerequisites
2. Build the Docker image
3. Start the container (`docker compose up -d`)
4. Wait for the server to be ready at `http://localhost:8000`
5. Register the MCP server in `~/.claude/settings.json`

After setup, restart Claude Code (or run `/mcp refresh`) for `mcp__gemini-bridge` to appear.

### Options

| Flag | Description |
|---|---|
| `--workspace <path>` | Directory mounted into the container as `/workspace` (read-only). Also accepted via `$WORKSPACE_MOUNT` env var. |
| `--skip-register` | Skip updating `~/.claude/settings.json`. |

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `WORKSPACE_MOUNT` | Yes (or `--workspace`) | Host path mounted into the container as `/workspace` |
| `GOOGLE_API_KEY` | No | API key auth. If unset, the container uses OAuth credentials from the `~/.gemini` mount. |
| `GOOGLE_CLOUD_PROJECT` | No | GCP project for Vertex AI billing, if applicable. |
| `GEMINI_BRIDGE_DEBUG` | No | Set to `true` to enable verbose server logging. |

---

## Available tools

### `gemini_query`

Sends a prompt to the Gemini CLI and returns the raw response as a JSON string.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt` | `string` | — | The prompt to send. |
| `model` | `GeminiModel` | `gemini-3-pro-preview` | Model to use. Options: `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash`. |
| `approval_mode` | `ApprovalMode` | `yolo` | Tool approval mode: `yolo` (auto-approve all), `auto_edit` (auto-approve edits only), `plan` (read-only). |
| `include_directory` | `string` | `null` | Optional directory outside `/workspace` to include. |
| `auto_fallback` | `bool` | `true` | Automatically retry with cheaper models on quota exhaustion. |

**Model fallback chain** (when `auto_fallback=true`): `gemini-3-pro-preview` → `gemini-2.5-pro` → `gemini-2.5-flash`

---

## Container management

```bash
# View running containers
docker compose ps

# Tail logs
docker compose logs -f

# Restart
docker compose restart

# Stop and remove
docker compose down
```

---

## How it works

```
Claude Code
    │
    │  MCP (HTTP/streamable)
    ▼
gemini-bridge server  (FastMCP, port 8000)
    │
    │  subprocess
    ▼
gemini CLI  (inside container, authenticated via ~/.gemini mount)
    │
    │  API
    ▼
Google Gemini
```

The container mounts `~/.gemini` from the host so OAuth credentials are shared — no re-authentication needed inside the container. `settings.json` inside `~/.gemini` is overridden with `gemini-settings.json` (enables `experimental.plan`).

---

## Troubleshooting

**Server not ready after setup**
```bash
docker compose logs gemini-bridge
```

**Gemini auth errors inside the container**
Run `gemini` on the host to refresh OAuth credentials, then restart the container:
```bash
gemini
docker compose restart
```

**Quota exhaustion**
With `auto_fallback=true` (the default), the server automatically tries cheaper models. If all models are exhausted, the tool returns a JSON error object with `"error": true`.
