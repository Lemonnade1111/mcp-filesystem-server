# PROJECT_STATE

## Goal
Sandboxed filesystem MCP server (Python / FastMCP) used as shared memory between me and my agents.

## Current status
- stdio server working in Claude Desktop
- HTTP transport + tunnel: working - server reachable from Claude Desktop through a Cloudflare quick tunnel (trycloudflare.com URL changes on restart)
- notes/summary.md and notes/architecture.md written and committed (session 2)
- Demo task: done - version-conflict demo (notes/demo.md): a stale `if_version` write is rejected

## Next step
No steps pending. Decide whether to extend the demo (e.g. test the HTTP tunnel with `MCP_TOKEN` set) or close out the project.

## Open questions
- none yet
