# Architecture

StartFilesystemMCP is a single-file Python server (`mcp_server.py`) built on FastMCP. It exposes a sandboxed workspace folder to MCP clients so that I and my agents can share files, notes, and handoff state.

## Sandbox design
- **Single root:** all paths are resolved against `WORKSPACE_ROOT` (`C:\Users\Colee\MCP-activity`).
- **Resolution:** `get_safe_path()` joins the requested path to the root and normalizes it with `os.path.abspath`, which collapses `..` segments.
- **Escape check:** both the root and the target are case-normalized (`os.path.normcase`), and `os.path.commonpath([root, target])` must equal the root. This rejects `../` traversal and prefix tricks such as `MCP-activity-evil`, which a plain `startswith` check would let through. A failure raises `PermissionError("Access Denied: Sandbox escape attempt rejected.")`.
- **Error handling:** file tools catch `PermissionError`, `FileNotFoundError`, and similar exceptions and return an `Error: ...` string instead of crashing.
- **Concurrency safety:** `file_version` returns a short SHA-256 hash. `write_file` and `str_replace` accept `if_version` and reject the write on a mismatch, so one session cannot overwrite another's changes.
- **Search scope:** `search_files` and `search_code` walk the workspace and skip `.git`.

## Tool list
| Group | Tools |
|---|---|
| File ops | `list_files`, `read_file`, `write_file`, `delete_file`, `str_replace`, `file_version` |
| Search | `search_files` (by name), `search_code` (by content, optional extension, max 50 hits) |
| Git-lite | `git_init`, `git_status`, `git_commit` (stages everything), `git_log` (max 50) |
| Handoff Protocol | `read_handoff`, `append_handoff` (limited to `PROJECT_STATE.md`, `PLAN_LOG.md`, `CHECKPOINTS.md`, `DECISIONS.md`; appends are timestamped) |

Git commands run through `subprocess` with `cwd=WORKSPACE_ROOT` and a 30 s timeout. Commits use a fixed identity (`MCP Server`).

## Transports
- **stdio** (default): `python mcp_server.py`. Used by Claude Desktop. Nothing may be printed to stdout, since it carries the protocol.
- **Streamable HTTP:** `python mcp_server.py --http [--port N]` serves on `127.0.0.1:8000/mcp` by default.
  - **Tunnel:** claude.ai reaches the server through a Cloudflare quick tunnel. The trycloudflare.com URL changes on every restart.
  - **DNS-rebinding protection:** disabled, because the Host header is the tunnel domain rather than localhost.
  - **Auth:** optional. If the `MCP_TOKEN` environment variable is set, a middleware requires `Authorization: Bearer <token>` or `?token=<token>`, otherwise it returns 401. With the protection off and no token set, anyone with the tunnel URL can access the workspace, so setting a token is recommended whenever the tunnel is up.
