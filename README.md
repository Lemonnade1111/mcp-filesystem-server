# StartFilesystemMCP

A sandboxed **filesystem MCP server** written in Python (FastMCP). It gives an AI agent safe file, search, git-lite and handoff tools inside one workspace folder, and doubles as shared memory between sessions through a Handoff Protocol (`PROJECT_STATE`, `PLAN_LOG`, `CHECKPOINTS`, `DECISIONS`).

Course project: *Midterms Pt 1 - Build Your Own* (Model Context Protocol).

## Features

- **Sandboxed workspace root.** Every path is resolved against the workspace; `..\` traversal, absolute paths and prefix tricks (`MCP-activity-evil`) are rejected.
- **14 tools**: file ops, search, git-lite and handoff tools (table below).
- **Two transports**: stdio (Claude Desktop) and streamable HTTP.
- **HTTPS through a Cloudflare tunnel**, kept alive by Windows services (NSSM).
- **Token auth** for the HTTP endpoint (`MCP_TOKEN`).
- **Version locking** (`if_version`) so one session cannot overwrite another's changes.
- **Handoff Protocol** so a new session can resume work from the files alone.

## Requirements

- Windows 10/11
- Python 3.10+ with the `mcp` package: `pip install mcp`
- Git for Windows (for the git-lite tools)
- Claude Desktop (MCP client)
- For the HTTPS part: `cloudflared` and NSSM (`winget install Cloudflare.cloudflared` and `winget install NSSM.NSSM`)

## Setup

1. Clone the repo into the workspace folder, or copy `mcp_server.py` there.
2. Set `WORKSPACE_ROOT` at the top of `mcp_server.py` to your folder (default: `C:\Users\Colee\MCP-activity`).
3. Make sure the four handoff files exist in that folder.

### Run over stdio (Claude Desktop)

Add this to `claude_desktop_config.json` and restart Claude Desktop:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "C:\\PYTHON314\\PYTHON.EXE",
      "args": ["C:\\Users\\Colee\\MCP-activity\\mcp_server.py"]
    }
  }
}
```

### Run over HTTP

```powershell
$env:MCP_TOKEN = -join ((48..57)+(97..122) | Get-Random -Count 24 | % {[char]$_})
$env:MCP_TOKEN                      # copy this value
python mcp_server.py --http         # serves http://127.0.0.1:8000/mcp
```

Without a token the endpoint is open to anyone who has the URL, so always set one.

### Expose it over HTTPS (Cloudflare quick tunnel)

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

The command prints an address like `https://<random-words>.trycloudflare.com`. In Claude Desktop add a **custom connector** named `filesystem-http` with the URL:

```
https://<random-words>.trycloudflare.com/mcp?token=<YOUR-TOKEN>
```

Quick tunnel addresses change every time the tunnel restarts.

### Keep it alive (NSSM, run in an Administrator PowerShell)

```powershell
nssm install McpServer "C:\PYTHON314\PYTHON.EXE" "C:\Users\Colee\MCP-activity\mcp_server.py --http"
nssm set McpServer AppDirectory "C:\Users\Colee\MCP-activity"
nssm set McpServer AppEnvironmentExtra "MCP_TOKEN=$env:MCP_TOKEN"
nssm set McpServer Start SERVICE_AUTO_START
nssm start McpServer

$cf = (Get-Command cloudflared).Source
nssm install CloudflaredTunnel $cf "tunnel --url http://127.0.0.1:8000"
nssm set CloudflaredTunnel AppStderr "C:\Users\Colee\cloudflared.log"
nssm set CloudflaredTunnel Start SERVICE_AUTO_START
nssm start CloudflaredTunnel
```

Find the current tunnel address after a restart:

```powershell
Select-String -Path "C:\Users\Colee\cloudflared.log" -Pattern "https://.*trycloudflare.com" | Select-Object -Last 1
```

Check both services:

```powershell
Get-Service McpServer, CloudflaredTunnel
```

One-time git setting, because the service runs under a different Windows account than your own:

```powershell
git config --system --add safe.directory "C:/Users/Colee/MCP-activity"
```

## Tools

| Group | Tool | What it does |
|---|---|---|
| Files | `list_files` | List a directory (folders end with `/`) |
| Files | `read_file` | Read a text file |
| Files | `write_file` | Write a file, creating folders; optional `if_version` |
| Files | `str_replace` | Replace text that must occur exactly once; optional `if_version` |
| Files | `delete_file` | Delete a file |
| Files | `file_version` | Return a file's version hash for `if_version` |
| Search | `search_files` | Find files by name |
| Search | `search_code` | Search inside files (`path:line: text`, max 50) |
| Git-lite | `git_init` | Initialize a repository |
| Git-lite | `git_status` | Short status |
| Git-lite | `git_commit` | Stage everything and commit |
| Git-lite | `git_log` | Last N commits (max 50) |
| Handoff | `read_handoff` | Read one of the four handoff docs |
| Handoff | `append_handoff` | Append a timestamped entry to a handoff doc |

Errors (missing file, sandbox escape, version conflict) are returned as readable messages, not crashes.

## Handoff Protocol

| File | Purpose |
|---|---|
| `PROJECT_STATE.md` | Where the project stands right now and the next step |
| `PLAN_LOG.md` | Append-only record of plans |
| `CHECKPOINTS.md` | Append-only record of what each session finished and what is pending |
| `DECISIONS.md` | Append-only record of design decisions, reasons and rejected alternatives |

A new session starts by reading these four files and continues from the last checkpoint. Only these four names are accepted by `read_handoff` / `append_handoff` (fixed allowlist).

## Demo task (2 sessions)

1. **Session 1:** read `PROJECT_STATE`, log a plan, create `notes/summary.md`, search for "sandbox", commit with git-lite, write a checkpoint that leaves one step pending.
2. **Session 2 (new chat):** resume only from the handoff files, finish the pending step (`notes/architecture.md`), commit, log a decision, and run a version-conflict demo (`notes/demo.md`): a write with a stale `if_version` is rejected.

The tool-call transcripts are in [`transcripts/`](transcripts/) (`session1.md`, `session2.md`). The sandbox test (`..\..\Windows\win.ini`) returned `Access Denied: Sandbox escape attempt rejected.`

## Security notes

- **Sandbox:** `os.path.commonpath` on normalized absolute paths, checked before every file access.
- **Token auth:** HTTP requests need `Authorization: Bearer <token>` or `?token=<token>`; otherwise 401. A token in the URL can end up in logs and screenshots, so rotate it after demos.
- **Host check relaxed in HTTP mode:** the tunnel changes the `Host` header, so the localhost-only DNS-rebinding check is turned off. The token is what protects the endpoint.
- **Quick tunnels** have no uptime guarantee and the address changes on restart; a named tunnel with a Cloudflare account would be the production option.
- **Known gap:** `append_handoff` does not use `if_version`, so two agents appending at the same moment could interleave.

## Repository layout

```
mcp_server.py        the MCP server
PROJECT_STATE.md     handoff: current state
PLAN_LOG.md          handoff: plans
CHECKPOINTS.md       handoff: checkpoints
DECISIONS.md         handoff: decisions
notes/               files created during the demo (summary, architecture, demo)
transcripts/         tool-call transcripts of the two demo sessions
```
