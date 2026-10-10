# Incident — Four Client control files lack exact known source provenance — 2026-10-10T0154Z

## Concrete observation

PCE15.021 compared 19 selected deployed Client files with exact Git blobs in historical Client commit b0a01eef1b2c19b498195d7318541782904d6c8f, common ancestor 94de291a3173b04ef23a6575e562edd8e8156993, development HEAD a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a and then-current main ee1731deae9eda398c0e77c201dc323f1fbf4d37. Fifteen files matched historical Client content; **hud.py, relay-control.ps1, relay-watchdog-loop.ps1 and sync-live.py** matched none of the four snapshots.

PCE15.022 examined these exact four paths through 18 reachable Git refs, 10/4/4/3 historical change events, and found **no exact Client content blob**, not even a matching old-side blob or local Git object. This search cannot see unreachable or missing history.

PCE15.023 inspected 49 recognized local Client/Relay/backups/sync-live-* directories, two containing all four files. 29 HUD backups (5 versions), 3 relay-control backups (3 versions), 3 watchdog backups (2 versions) and 9 sync-live backups (2 versions) **never matched the four current Client files or development equivalents**. Other backup sources remain outside scope.

PCE15.024 confirmed all four current Client, current development and latest backed-up source scripts **parse successfully**. Latest backups are close to Client by static line comparison (4/1/1/1 changed regions). Identical HUD development/Client mtime 2026-10-08T05:42:38Z does not demonstrate identical code; copy2 and other tooling may retain mtimes.

Separately, PCE15.020 observed the one active TCP 8766 backend python.exe PID 10684 launched referencing the Client/Relay tree, **not** an independently attested in-memory code hash. No 8767 listener at time of snapshot. Exact Firefox-loaded content and backend memory are UNKNOWN.

## Classification, containment and next steps

**OPEN / PROVENANCE UNVERIFIED, NOT MALICIOUSNESS ESTABLISHED.** Do not claim unauthorized editing, malware, corruption, a full mixed-code process, or who modified these files. Candidate origins include other historical commits, deployment transformations, copied scripts or out-of-repository changes. Earlier incident about XPI 0.3.17 3/5 asset mismatch and non-atomic deploy-before-test remains separately open.

All PCE15.020–.024 receipts returned OK/0 for read-only diagnostics with protected evidence and checkout unchanged. No live repairs, UI input, patch, backup restore, Git write, restart, deployment, manual rescue or ChatGPT send occurred; no rollback was needed. Preserve PCE12 untracked audit and backup SHA256 3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab. Pinned release score remains Grade F, 11/28 gates passing, G26 0/60, G27 0/2.

Next remediation is GitHub-first design/review of an explicit fully SHA-pinned complete release artifact and rollback-safe staged promotion, plus narrow independent provenance inspection. Do not copy individual development scripts into the live Client during grading. No source-code edits authorized by this incident.
