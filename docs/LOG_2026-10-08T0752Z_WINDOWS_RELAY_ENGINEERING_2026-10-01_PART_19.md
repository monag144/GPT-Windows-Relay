# Archived source fragment 19/23 — 2026-10-08T0752Z

2. already exactly delivered drafts are cleared without resend and cannot reacquire/retain the global owner;
3. no-draft stale owners are released only with exact matching user-result evidence; unresolved owners remain observable for bounded supervisor recovery;
4. preserve backend exact-once behavior and do not solve this by blindly clearing owners;
5. add regression coverage and live-prove consecutive packets after a delivered result without re-execution;
6. replace repeated active-owner defer spam with a bounded watchdog/recovery state.


## PCE7.402 delayed out-of-order execution — 2026-10-06T0329Z

PCE7.402 was emitted around 03:09Z, then the Director had to navigate back from an unintended generic ChatGPT screen. PCE7.403 proved at 03:22:40Z that PCE7.402 still had no backend record/result. PCE7.404 executed at 03:24:12Z–03:24:13Z. Only afterward, PCE7.402 finally executed at 03:24:18Z.

This is direct proof of unique-ID delayed/out-of-order ingestion: operation 402 executed after operations 403 and 404. It was read-only, so no harmful side effect occurred.

Reliability implication:
- backend exact-once protection prevents duplicate execution of the same ID but does not prevent an obsolete unique side-effecting packet from executing late;
- the existing rotation ordinal parser records delivered counts/100-operation rotation but does not enforce a monotonic operation cursor;
- a parseable older operation from the same/superseded engineering series must be classed as `LATE_PACKET` and suppressed before backend execution once a newer operation cursor has been accepted;
- series parsing must be dynamic and generation-aware (for example A6 -> PCE7) rather than hard-coded to one agent label;
- arbitrary packet IDs that do not match the explicit engineering-series grammar must not be assigned a misleading ordinal.

PCE7.405 had already been emitted when the delayed PCE7.402 result arrived. Do not issue a duplicate PCE7.405; allow exact backend evidence to determine whether it executes.

### PCE7.405 500-second no-action watchdog failure — 2026-10-06T0340Z

Observed live by the operator after issuing `PCENG-PCE7.405-r29-checkout-runtime-map`: the HUD reached about **500 seconds since last action detected** and no PCE7.405 result arrived. PCE7.405 is read-only, so a later execution is not side-effect dangerous, but the absence is direct evidence that the documented 15-second recovery scan plus ~5-minute deadman did not restore forward progress.

Source inspection found a concrete redundancy hole in `windows-relay/extension/content.js`:

- `forceRecoveryPacketInspect()` called `resetRecoveryPacketWatch()` whenever `newestRelayCommandUnit()` returned no currently materialized command. A packet temporarily absent because of ChatGPT DOM virtualization/remount therefore lost its recovery deadline.
- The deadman also refused page-refresh recovery whenever `activeRelayOperationId` was non-null. PCE7.401–PCE7.404 already proved that a stale owner can survive after backend completion/result delivery and block later operations, so this condition could disable the deadman indefinitely.
- A visible 5-minute constant was therefore not equivalent to a durable 5-minute recovery obligation.

Hardening committed on r29:

- `104f9e80d0f9fa8670cfb4f49bc5dd55abe2e010` — persist the recovery packet obligation in session storage across DOM disappearance/remount, retain its original first-seen deadline, rate-limit recovery reloads, and give stale operation ownership a bounded lease that releases into exact-once replay after the watchdog interval.
- `2917a8b1d6737f2593773e7df7528145969c87c3` — regression contract proving the durable-obligation and stale-owner-lease markers/semantics remain present.

This is source hardening only until the Windows r29 checkout is synced, tests/syntax pass there, and the exact live Firefox add-on is reloaded. Do not call the incident closed before live proof. Because PCE7.405 never returned, it remains **stranded/unknown** rather than “failed in backend.”

### PCE7.406 validation gate stopped staging — 2026-10-06T0343Z

`PCENG-PCE7.406-sync-test-stage-redundancy-hardening` reached backend execution promptly and failed in 4.990 s with `RuntimeError: node_not_found`. The operation had already located/synced the exact r29 checkout, but the script intentionally placed live backup/copy after JavaScript syntax validation; therefore the live Firefox extension was **not staged or reloaded** by PCE7.406.

This is a correct fail-closed validation outcome, not a relay-ingestion failure. Next recovery must use an actually available JavaScript parser/runtime (including a Chromium V8 syntax harness if Node is absent), preserve the Python contract-test gate, and only then stage the live extension.

### PCE7.407 hardening staged after independent V8 + contract validation — 2026-10-06T0346Z

`PCENG-PCE7.407-v8-validate-and-stage-hardening` completed OK in 17.441 s. The exact r29 checkout was `C:\\Users\\<LOCAL_USER>\\Downloads\\Dev\\GPT\\GPT-Termux-Relay-consumer`, fast-forwarded to `9b0fbeef353e9cf82e9fa93aa1164fb453e9b6b0`. The ChatGPT content contract passed. Because Node was unavailable, Microsoft Edge's installed Chromium/V8 engine independently parsed both staged JavaScript files successfully.

A rollback snapshot was created at `C:\\Users\\<LOCAL_USER>\\Downloads\\Dev\\GPT\\Client\\Relay\\rollback\\PCE7.407-20261006T034645Z`. Source and live SHA-256 matched for both staged files:

- `content.js`: `9aa16685c3695ca1bf81c194ab3e117b4579aa81fe6f60d39ab987b0b27cb54f`
- `service_worker.js`: `4053c08842cea815eb375f953e0026e682d070ca89f9fa5a957834e6ff6fa8be`

State at this point: **STAGED_NOT_RELOADED**. Live acceptance still requires the exact Firefox add-on reload, current-chat refresh/rebind, exact-result replay proof, and follow-up telemetry inspection.

### PCE7.408 live cutover stranded backend-OK result — 2026-10-06T0355Z

The operator reported `PCENG-PCE7.408-live-firefox-cutover-and-rebind` locked at **STARTING for 425 seconds**. Screenshot evidence at ~417 s showed `Relay ONLINE • ARMED • pending 0`, `Firefox IDLE • action_received`, and `LAST PCENG-PCE7.408-live-firefox-cutover-and-rebind / OK`, while no exact 408 result had appeared as a ChatGPT user turn.

This is a failed live cutover/rebind acceptance even if backend execution is terminal OK: the result was not reconciled/delivered after the add-on/page remount. Treat 408 as backend-state-known-only-from-HUD until independent readback confirms processed/result-file state. Incident: `docs/INCIDENT_2026-10-06T0355Z_PCE7_408_STARTING_STUCK_AFTER_CUTOVER.md`.



### PCE7.410–PCE7.415 HUD startup/diagnostic regression — 2026-10-06T0455Z

The relay bridge resumed backend execution, but the HUD recovery path exposed a separate regression. PCE7.410 timed out calling `hud.py --once`; direct r29 inspection proved current `hud.py` ignored `--once` and always entered the Tk mainloop, despite the earlier P1 log explicitly recording a successful `--once` diagnostic. PCE7.415 then launched the HUD but failed its own overly strict raw-process-count assertion after seeing two `hud.py` processes. Because the venv launcher is known to create a shim→real-interpreter pair for the relay server, this is not yet evidence of two logical HUDs.

Source commit `e3e0126b1605dd84d6c344a84ebbea4f107846c6` restores JSON snapshot-and-exit behavior; `069efb1391e1375e5958b90c545cd0596ab6a168` adds a behavioral test. Live staging, PID/PPID topology, actual startup wiring, automatic relay+HUD recovery, and stale-STARTING lifecycle handling remain open. Incident: `docs/INCIDENT_2026-10-06T0455Z_HUD_STARTUP_AND_ONCE_CONTRACT_DRIFT.md`.


### PCE7 GitHub approval blocker escalated — 2026-10-06T0528Z

Director screenshot evidence showed the native ChatGPT GitHub approval card visibly blocking the current engineering loop: `Allow ChatGPT to use GitHub?` with `Always allow`, `Deny`, and `Allow once`. The relay HUD independently detected the same state as `APPROVAL REQUIRED • ChatGPT tool approval • GitHub`, proving detection already worked while action was absent.

Per Director authorization, r29 commit `dc5afa8fab1b182de64a3537e2f52da40e4087b6` adds a narrowly gated auto-click of `Always allow` only for that exact GitHub surface when all expected controls are present and the relevant scroll root is at bottom. Commit `5a5d0cd2077c91d2a6d1e2328cb970a1c137810c` adds a regression assertion. Unknown/other providers remain fail-closed. Live Firefox staging/reload and telemetry proof are still required.


### PCE7.425 post-refresh replay duplicated visible result — 2026-10-06T0537Z

