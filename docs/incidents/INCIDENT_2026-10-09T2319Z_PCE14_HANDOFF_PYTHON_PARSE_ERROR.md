# PCE14 successor handoff launcher Python parse failure — 2026-10-09T2319Z

## Observed
One-shot relay ID `PCE14-HANDOFF-TO-PCE15-CORRECTED-RAW-BLOB-ONE-SHOT-20261009` returned `COMMAND_FAILED`, `exit_code=1`, total runtime 201ms. Python exited on **syntax parsing, line 11**, at the `psquote` helper: `str(s).replace("'","''')`, an unterminated string literal. The caller command did **not run**, so no preflight, handoff file write, backup, reference source staging, durable launch intent, Firefox focus, New Chat, paste or Send from this attempt. Do not replay its ID.

An earlier **distinct** one-shot ID `PCE14-HANDOFF-TO-PCE15-GITHUB-PINNED-ONE-SHOT-20261009` passed Firefox foreground identity, then failed before file write on Git object-byte mismatch because its helper stripped the newline from `git show` binary output. Both are pre-send failures. GitHub handoff document `docs/handoffs/HANDOFF_2026-10-09T2315Z_PCE14_TO_PCE15_STRICT_GRADING_SEMANTIC_BROWSER_REUSE.md` has blob `70dc49d242b4e3259feb8b81e814d10c664233ee` and trailing newline.

## Recovery direction and exact-once control
Use a **fresh unique one-shot ID**. Perform `compile()`/syntax validation of any generated worker before saving the launch intent or invoking a process. Read pinned `git show` bytes **without `.strip()`** for blob integrity, retaining `.strip()` only for textual Git metadata. Prove `Copy-Contents-To-ChatGPT.ps1` hash `e2ff24ca5b893fa6259bfdc2000872e581a512c13405cdcd6a9bc1c051b9223a`, selected Firefox HWND equals foreground, protected PCE12 original and backup SHA both `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab`, STOP not present, existing one-shot intent absent. Backup and replace **only** `Client\Relay\test\Copy Contents.txt` with pinned handoff content, stage historical UIA code as **non-executing references**, then atomically reserve a durable launch intent prior to running unchanged proven script. Worker receipt should distinguish launched, stopped before invocation, possibly submitted, and independently verified; never silently retry an uncertain send.

Keep separate the strict grading campaign: user ordered grading **without functional repairs**; an explicitly user-authorized handoff invocation is not a repair to benchmark feature source. Semantic New Chat from PCE11.076 was real but stopped before paste; PCE8 v16 was successful result delivery, not a completed New Chat+Send handoff. Do not repeat the isolated Firefox profile diagnostics or claim they are new progress.

**INCIDENT OPEN — no send from either failed one-shot.**
