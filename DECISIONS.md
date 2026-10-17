# DECISIONS
Append-only. Format: decision, reason, alternatives rejected.

## Initial decisions
- Python + FastMCP: small API, supports both stdio and streamable HTTP.
- Sandbox via os.path.commonpath on a normalized root: rejects ../ and prefix tricks.
- Version hashes (if_version) on writes: stops one session overwriting another's changes.

## 2026-10-17 10:43
Decision: handoff docs (PROJECT_STATE, PLAN_LOG, CHECKPOINTS, DECISIONS) are reachable only through a fixed allowlist (`HANDOFF_DOCS`) in `read_handoff` / `append_handoff`, and the log docs are append-only with an automatic timestamp.
Reason: sessions and agents resume from these files, so they must not be redirected to arbitrary paths or have history rewritten. The allowlist rejects any other name, and the server-added timestamp keeps entries ordered without each agent formatting its own.
Alternatives rejected: letting agents edit these files with the general `write_file` (a stale or careless write could wipe the history; `if_version` is opt-in, so it doesn't prevent that); accepting any filename in `append_handoff` (adds nothing over `write_file` and weakens the protocol).
Known gap: `append_handoff` does not use `if_version`, so two agents appending at the same moment could interleave. Acceptable for now since appends only add lines.
