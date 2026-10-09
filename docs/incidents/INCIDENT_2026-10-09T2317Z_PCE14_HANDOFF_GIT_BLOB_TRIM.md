# PCE14 handoff pre-launch Git blob mismatch — 2026-10-09T2317Z

## Actual failed attempt
Relay packet `PCE14-HANDOFF-TO-PCE15-GITHUB-PINNED-ONE-SHOT-20261009` returned `COMMAND_FAILED`, exit 1. Source and protected audit gates passed; Windows `Get-Process firefox` first visible HWND `19466700` equaled OS foreground HWND `19466700`. Next step raised `RuntimeError:HANDOFF_CONTENT_OR_BLOB_MISMATCH`, **before writing `test\Copy Contents.txt`, staging the semantic backend, writing a one-shot intent journal, or launching the sender**. Therefore no resulting handoff message was deliberately sent by this packet. Never replay this packet ID.

## Root cause
The helper `g(*args)` unconditionally returned `subprocess.stdout.strip()` **even for `git show <commit>:<file>` binary contents**. The pinned handoff GitHub blob `70dc49d242b4e3259feb8b81e814d10c664233ee` contains a final newline (verified with GitHub `fetch_file`), which `strip()` drops, changing the computed SHA-1 Git blob hash. This is a source-byte transport bug in the ephemeral one-shot command, **not a mismatch between the published GitHub file and commit**.

## Corrective bound
Create a fresh unique, non-replayed handoff attempt only after confirming absence of prior intent journal and unchanged user-proven PowerShell launcher SHA256 `e2ff24ca5b893fa6259bfdc2000872e581a512c13405cdcd6a9bc1c051b9223a`. Retrieve `git show` source bytes **exactly, without `.strip()`**, verify expected blob via `git rev-parse <sha>:<path>` and local `hashlib.sha1('blob '+len+NUL+data)`. Keep `.strip()` only for textual Git SHA/status output. Save handoff to exact `Client\Relay\test\Copy Contents.txt` with backup/readback; stage historical semantic UIA source references non-executably; log exclusive one-shot intent before invoking the validated existing GUI launcher. Guard STOP, foreground window, source/evidence SHA, never retry uncertain clicks or sends.

A launched worker is not evidence of user-role message delivered. Subsequent result and next conversation must prove that separately. This incident records **only** the pre-send failure; no repair to production relay or Firefox was made.
