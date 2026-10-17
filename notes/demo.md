# Demo: version-conflict protection

Shows that `if_version` stops one session from overwriting another's changes.

| Step | Call | Result |
|---|---|---|
| 1 | `write_file notes/demo_target.txt` (no version) | Written, version `71c7bb414d4d` |
| 2 | `file_version notes/demo_target.txt` | `71c7bb414d4d` |
| 3 | `write_file` with `if_version=71c7bb414d4d` | Accepted, new version `f8026a73705a` |
| 4 | `write_file` again with the stale `if_version=71c7bb414d4d` | Rejected: `version conflict (current version is f8026a73705a). Re-read the file and retry.` |

Outcome: the file still holds the step 3 content ("demo v2"). The stale write in step 4 changed nothing.

Note: the version is a SHA-256 of the file contents, so it changes whenever the content changes. A write without `if_version` is never checked.
