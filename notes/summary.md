# MCP Server Summary

A sandboxed filesystem MCP server (Python / FastMCP) that acts as shared memory between me and my agents.

## What it does
- **File operations:** read, write, delete, list, and search files by name inside a sandboxed workspace folder.
- **Code search:** search inside files for text, with an optional extension filter (max 50 results).
- **Safe edits:** `file_version` returns a version hash that can be passed as `if_version` to `write_file` / `str_replace`, so a write is rejected if the file changed in the meantime.
- **Git-lite:** `git_init`, `git_status`, `git_commit` (stages everything), and `git_log`.
- **Handoff Protocol:** `read_handoff` and `append_handoff` work with `PROJECT_STATE.md`, `PLAN_LOG.md`, `CHECKPOINTS.md`, and `DECISIONS.md` so work can continue across sessions and agents.

## Transports
- stdio: working in Claude Desktop.
- HTTP via a tunnel: exposed to claude.ai (status tracked in PROJECT_STATE.md).
