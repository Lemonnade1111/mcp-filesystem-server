# DECISIONS
Append-only. Format: decision, reason, alternatives rejected.

## Initial decisions
- Python + FastMCP: small API, supports both stdio and streamable HTTP.
- Sandbox via os.path.commonpath on a normalized root: rejects ../ and prefix tricks.
- Version hashes (if_version) on writes: stops one session overwriting another's changes.
