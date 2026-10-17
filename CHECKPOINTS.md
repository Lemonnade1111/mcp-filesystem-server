# CHECKPOINTS
Append-only. Record what is finished at the end of each agent session, so the next session can resume.

## 2026-10-17 10:33
Checkpoint (session 1): steps 1-5 done (read PROJECT_STATE, logged plan in PLAN_LOG, created notes/summary.md, searched "sandbox", git init + commit "session 1: notes + plan"). Step 6 (add notes/architecture.md) is still pending.

## 2026-10-17 10:42
Checkpoint (session 2): Step 6 done. Created notes/architecture.md (sandbox design, tool list, transports) from mcp_server.py and committed as "session 2: add architecture notes" (6eb6c79). Commit also picked up transcripts/session1.md. No steps pending; next is the demo task.

## 2026-10-17 10:43
Checkpoint (session 2, final): pending step finished. The demo task was an unfilled placeholder, so I defined it as a version-conflict demo: created notes/demo_target.txt, wrote with the correct if_version (accepted), then with a stale one (rejected with a version conflict). Results recorded in notes/demo.md. Added a DECISIONS entry (handoff allowlist + append-only logs) and updated PROJECT_STATE. All work committed. No steps pending.
