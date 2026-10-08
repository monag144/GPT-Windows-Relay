# Archived source fragment 2/3 — 2026-10-08T0752Z

- Historical screenshots, including PCE10.025, recorded specific ChatGPT conversation URLs, but **do not hard-code those old IDs as the current engineering chat**. The next agent must derive and positively verify the *present* conversation identity; chat rotation can change the URL.
- These profile/extension facts were **proven historically**, not freshly read at PCE10.037. Do **not** pretend the old addon ID, tab title, internal UUID, process PID, or URL is necessarily today's active instance. The current Firefox PID and exact tab URL are explicitly **UNVERIFIED**.

**The current diagnosis is NOT "we don't know how to use Firefox."** It is: approved source built green; existing adapter `resolve-conversation-tab` returned zero on a named live-identity gate. We know exactly where the filter and comparison are and how to test it; do not start from browser installation, deep profile database inspection, stale title matching, or another random window enumeration.

## 4. Next safe engineering operation: PCE10.038

**Goal:** discriminating, genuinely observational Firefox identity inventory that explains PCE10.037's zero-match before any live mutation. It must remain a fresh unique `PCE10.038`, not a repeat of a potentially executed earlier packet.

1. Read all five governance controls; run `engineering_preflight(repo,38,10)`. The .030–.034 audit exists at `docs/audits/AUDIT_2026-10-08T0624Z_PCE10_OPERATIONS_030_034.md`, synchronized and accepted by `GOV-AUDIT-030-034-SYNC`. Inspect current branch/head/clean checkout. Do not preemptively modify the runtime.
2. Collect **bounded** newest backend browser events and state (e.g., `content_script_started`, `content_port_connected`, `relay_packet_discovered`, tab/conversation metadata and actual loaded runtime version if emitted). Correlate to the **current** chat owner, not an earlier conversation's UUID. Avoid dumping full logs or unrelated tab URLs.
3. Query Firefox process/tree, visible windows, **currently selected** accessible tab and its URL readback without switching tabs. If profile/process binding is required, use the established managed adapter and prior evidence; don't spawn broad new desktop scrapers. Check whether the .037 caller supplied a stale/wrong `--conversation-url` and whether the specific `IsOffscreen`/parent filter hid a valid tab.
4. Distinguish and report **one** root-cause class with evidence: wrong URL, visibility/filter defect, tab accessibility absent, stale process/profile binding, or current target actually missing. If evidence remains ambiguous, say `IDENTITY_UNVERIFIED` and **stop**, rather than loading the addon into an uncertain browser.
5. When the resolver code is defective, fix it on GitHub first (not in Windows live), add a focused regression, verify remote SHA, have Windows `git pull --ff-only`, and rerun relevant/full test gates. Prefer read-only identity collection and exact tab-ID verification to repeatedly selecting every tab just to inspect URL. No hidden tab focus/selection side effects advertised as purely read-only.
6. If the target can be proven with existing source and no code change, proceed **in a subsequent operation**, after explicit operator/backup checks, to a **controlled, narrowly scoped, reversible activation**. Never treat "identity found" as automatic permission to stage and reload everything.

**Forbidden approaches right now:** rerun the same `resolve-conversation-tab` with the same guessed URL; an unscoped `list-tabs`; rebuild every PID/profiles fact; paste giant UIA scripts into the relay; terminate all Firefox processes; automatically refresh or reload the addon before exact target proof; replay PCE10.018/.021/.025; conclude `no Firefox` from `MATCH_COUNT_0`.

## 5. Safe deployment once and ONLY once identity is proven

1. Verify current repository HEAD is GitHub-committed, Windows checkout fast-forwarded to exact SHA, full tests still green for **that source**, and live staging paths explicitly enumerated. **Do not use an older stale live copy of `sync-live.py` for an unreviewed broad sync.**
2. Prove operator STOP/ARM/stop-generation state at the time of activation. PCE10.036/.037 recorded `armed=True` and `stop_generation=7`, but these can change. A prior ARMED screenshot/result is not fresh authorization for risky mutation.
3. Preserve every existing backup. Make a new timestamped, exact-byte, SHA-256 verified backup of **each file to be changed** plus a machine-actionable restore manifest. Do not overwrite the PCE10.026 forensic snapshot or the PCE10.020 original-content backup.
4. Stage only vetted files through a helper with rollback, prove exact source/live hashes and path scope, activate/reload the **identified** addon and specific ChatGPT tab without affecting unrelated profiles/tabs, and prove a fresh `content_script_started` after reload with version identity. Disk SHA matching alone is insufficient.
5. One harmless *fresh unique ID* end-to-end canary must traverse `DISCOVERED -> authenticated backend reservation/action -> saved result -> visible correctly parsed user result`. Separately verify the 5s settling lease and independent <=45s STOP-aware scanner recovery, including no duplicate action, no accidental clearing on false replay suppression, and **visible** continuation.
6. On failure, hold and restore from an independently verified rollback. Do not promote a candidate unless source acceptance, identity, STOP, runtime revision, both canaries and performance/latency are evidenced.
7. Only then close the composite discovery incident, reduce excess `GET /status` traffic if still measured, and consider `main` merge and product lifecycle gates.

## 6. Backups: what they are, and what they are NOT

**PCE10.026 forensic snapshot:** `%LOCALAPPDATA%\GPTWindowsRelay\backups\BROKEN-PCE10.026-2026-10-08T055125Z`. All **658 files** were re-hashed successfully in PCE10.036. It includes program files, source bundle, and best-effort state/config captures. Manifest SHA256 `5d67ffb068e12cabfab7c2c2b58ebd4a3c9236aaf856fb37da1137d874650563`. **Label: BROKEN — DO NOT PROMOTE.** It is a recoverable forensic snapshot, not an established working production release; it excludes historical backup/log/cache directories.

**PCE10.020 pre-stage originals:** `%LOCALAPPDATA%\GPTWindowsRelay\backups\PCE10.020-20261008T031613Z\manifest.json`. Three original content files; PCE10.036 confirmed three and 0 hash failures. This is a **partial rollback**, not a full prior working installation.

**Codex-reported stage backup:** `Client\Relay\backups\pce10-replay-suppression-repair-20261007-224256`. Existence/restore coverage was separately reported but **not independently certified** in the PCE10.036 proof. Do not silently treat it as a complete rollback.

**Critical:** No confirmed **known-good complete previous live build** exists in the provided acceptance results. "We have a backup" is not the same as "we have a working known-good version." Treat any rollback as a decision based on exact manifest and current runtime state.

## 7. Failure patterns and expensive repetitions — DO NOT REPEAT

**A. Endless Firefox identity archaeology.** The earlier PCE9 audit found **at least 25** operation slots revisiting Firefox restart/continuity/no-reload facts. Facts remain valid until a state-changing event contradicts them. Re-probe only when (i) browser state actually changed, (ii) contradictory evidence appeared, or (iii) a named acceptance requires it. Right now .037 supplies a **specific contradictory resolver result** permitting a *bounded, targeted identity diagnostic*—not a restart of all past investigations.

**B. Treating "ONLINE/ARMED/heartbeat" as command execution.** Server can respond HTTP 200 while `DISCOVERED` is stuck for thousands of seconds; prior watchdog stopped scanning when port 8766 listened. Require packet-specific state and fresh actual browser runtime.

**C. False result acknowledgement from an ID mention.** Original code accepted `elementText(...).includes(packetId)` on generic user-message wrappers. Session `attempted` history preserved false suppression. Older workers cleared watchdog on `relay_result_replay_suppressed` as if success. Source changes address these, but live proof remains absent. No speculative replay.

**D. Rewriting tests to pass without examining safety semantics.** We found stale selectors, old poll intervals, forbidden alarm assertions, and literal-adjacency tests; modified them in GitHub only where implementation evidence justified it. Full green tests at PCE10.035 matter, but aren't a deployed-system result.

