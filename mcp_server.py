"""
StartFilesystemMCP - sandboxed filesystem MCP server.

Run modes:
  python mcp_server.py                 -> stdio (what Claude Desktop uses)
  python mcp_server.py --http          -> streamable HTTP on 127.0.0.1:8000/mcp
  python mcp_server.py --http --port 9000

Optional auth for HTTP mode: set the MCP_TOKEN environment variable.
Clients must then send "Authorization: Bearer <token>" or use ?token=<token> in the URL.
"""
import argparse
import hashlib
import os
import subprocess
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Requirement 1: Sandboxed workspace root
WORKSPACE_ROOT = r"C:\Users\Colee\MCP-activity"
HANDOFF_DOCS = ["PROJECT_STATE.md", "PLAN_LOG.md", "CHECKPOINTS.md", "DECISIONS.md"]

# When served through a tunnel the Host header is the tunnel domain, so the
# localhost-only DNS-rebinding check must be relaxed (token auth protects us instead).
try:
    from mcp.server.transport_security import TransportSecuritySettings

    mcp = FastMCP(
        "StartFilesystemMCP",
        host="127.0.0.1",
        port=8000,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
except (ImportError, TypeError):
    mcp = FastMCP("StartFilesystemMCP", host="127.0.0.1", port=8000)


# ---------------------------------------------------------------- helpers
def get_safe_path(relative_path: str) -> str:
    """Resolves path against workspace and rejects escapes."""
    root = os.path.normcase(os.path.abspath(WORKSPACE_ROOT))
    target_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, relative_path))
    if os.path.commonpath([root, os.path.normcase(target_path)]) != root:
        raise PermissionError("Access Denied: Sandbox escape attempt rejected.")
    return target_path


def _sha(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def _git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", *args], cwd=WORKSPACE_ROOT, capture_output=True, text=True, timeout=30
        )
    except FileNotFoundError:
        return "Error: git is not installed or not on PATH."
    except subprocess.TimeoutExpired:
        return "Error: git command timed out."
    return (r.stdout + r.stderr).strip() or "(no output)"


# ---------------------------------------------------------------- file ops
@mcp.tool()
def list_files(path: str = "") -> list:
    """List directory contents (folders end with /)."""
    try:
        safe = get_safe_path(path)
        return [n + ("/" if os.path.isdir(os.path.join(safe, n)) else "") for n in sorted(os.listdir(safe))]
    except (PermissionError, FileNotFoundError, NotADirectoryError) as e:
        return [f"Error: {e}"]


@mcp.tool()
def read_file(filename: str) -> str:
    """Read a text file."""
    try:
        with open(get_safe_path(filename), "r", encoding="utf-8") as f:
            return f.read()
    except (PermissionError, FileNotFoundError, IsADirectoryError) as e:
        return f"Error: {e}"


@mcp.tool()
def file_version(filename: str) -> str:
    """Get a file's version hash. Pass it as if_version to write_file / str_replace."""
    try:
        return _sha(get_safe_path(filename))
    except (PermissionError, FileNotFoundError, IsADirectoryError) as e:
        return f"Error: {e}"


@mcp.tool()
def write_file(filename: str, content: str, if_version: str = "") -> str:
    """Write a file (creates folders). If if_version is given and the file changed since, the write is rejected."""
    try:
        safe = get_safe_path(filename)
        if if_version and os.path.exists(safe) and _sha(safe) != if_version:
            return f"Error: version conflict (current version is {_sha(safe)}). Re-read the file and retry."
        os.makedirs(os.path.dirname(safe), exist_ok=True)
        with open(safe, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filename} (version {_sha(safe)})"
    except (PermissionError, IsADirectoryError) as e:
        return f"Error: {e}"


@mcp.tool()
def delete_file(filename: str) -> str:
    """Delete a file."""
    try:
        os.remove(get_safe_path(filename))
        return f"Deleted {filename}"
    except (PermissionError, FileNotFoundError, IsADirectoryError) as e:
        return f"Error: {e}"


@mcp.tool()
def str_replace(filename: str, old_str: str, new_str: str, if_version: str = "") -> str:
    """Replace a string that must appear exactly once in a file."""
    try:
        safe = get_safe_path(filename)
        if if_version and _sha(safe) != if_version:
            return f"Error: version conflict (current version is {_sha(safe)}). Re-read the file and retry."
        with open(safe, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(old_str)
        if count != 1:
            return f"Error: old_str must appear exactly once (found {count})."
        with open(safe, "w", encoding="utf-8") as f:
            f.write(content.replace(old_str, new_str))
        return f"Replaced text in {filename} (version {_sha(safe)})"
    except (PermissionError, FileNotFoundError, IsADirectoryError) as e:
        return f"Error: {e}"


# ---------------------------------------------------------------- search
@mcp.tool()
def search_files(query: str) -> list:
    """Search for files by name (case-insensitive)."""
    results = []
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            if query.lower() in name.lower():
                results.append(os.path.relpath(os.path.join(root, name), WORKSPACE_ROOT))
    return results


@mcp.tool()
def search_code(query: str, extension: str = "") -> list:
    """Search inside files for text. Optional extension filter like '.py'. Returns 'path:line: text' (max 50)."""
    results = []
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            if extension and not name.lower().endswith(extension.lower()):
                continue
            full = os.path.join(root, name)
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            rel = os.path.relpath(full, WORKSPACE_ROOT)
                            results.append(f"{rel}:{i}: {line.strip()[:200]}")
                            if len(results) >= 50:
                                return results
            except OSError:
                continue
    return results


# ---------------------------------------------------------------- git-lite
@mcp.tool()
def git_init() -> str:
    """Git-lite: initialize a real git repository in the workspace."""
    return _git("init")


@mcp.tool()
def git_status() -> str:
    """Git-lite: show short status."""
    return _git("status", "--short", "--branch")


@mcp.tool()
def git_commit(message: str) -> str:
    """Git-lite: stage everything and commit with the given message."""
    if not message.strip():
        return "Error: commit message required."
    add = _git("add", "-A")
    if add.startswith("Error"):
        return add
    return _git("-c", "user.name=MCP Server", "-c", "user.email=mcp@local", "commit", "-m", message)


@mcp.tool()
def git_log(count: int = 10) -> str:
    """Git-lite: show the last N commits (max 50)."""
    return _git("log", "--oneline", f"-{max(1, min(count, 50))}")


# ---------------------------------------------------------------- handoff protocol
@mcp.tool()
def read_handoff(doc_name: str) -> str:
    """Read a Handoff Protocol document (PROJECT_STATE, PLAN_LOG, CHECKPOINTS, DECISIONS)."""
    if doc_name not in HANDOFF_DOCS:
        return f"Invalid handoff document. Choose from: {', '.join(HANDOFF_DOCS)}"
    return read_file(doc_name)


@mcp.tool()
def append_handoff(doc_name: str, entry: str) -> str:
    """Append a timestamped entry to a Handoff Protocol document."""
    if doc_name not in HANDOFF_DOCS:
        return f"Invalid handoff document. Choose from: {', '.join(HANDOFF_DOCS)}"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(get_safe_path(doc_name), "a", encoding="utf-8") as f:
        f.write(f"\n## {stamp}\n{entry.strip()}\n")
    return f"Appended entry to {doc_name}"


# ---------------------------------------------------------------- entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="serve over streamable HTTP instead of stdio")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.http:
        import uvicorn
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import JSONResponse

        token = os.environ.get("MCP_TOKEN", "")
        app = mcp.streamable_http_app()

        if token:

            class TokenAuth(BaseHTTPMiddleware):
                async def dispatch(self, request, call_next):
                    ok = (
                        request.headers.get("authorization") == f"Bearer {token}"
                        or request.query_params.get("token") == token
                    )
                    if not ok:
                        return JSONResponse({"error": "unauthorized"}, status_code=401)
                    return await call_next(request)

            app.add_middleware(TokenAuth)

        uvicorn.run(app, host="127.0.0.1", port=args.port)
    else:
        # stdio: never print to stdout here, it carries the protocol
        mcp.run(transport="stdio")
