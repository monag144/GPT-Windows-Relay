# Archived source fragment 3/3 — 2026-10-08T0752Z

- The named HUD mutex remains the singleton boundary and startup/reconciliation must be auditable.
- A stale browser lifecycle event such as old `action_received` must age into an explicit STALLED/STALE state rather than display STARTING indefinitely.
- Incident: `docs/INCIDENT_2026-10-06T0455Z_HUD_STARTUP_AND_ONCE_CONTRACT_DRIFT.md`.


### R2a priority escalation — 2026-10-06T0528Z

The exact GitHub ChatGPT approval surface is no longer merely low-priority annoyance. Director screenshot evidence at 05:28Z showed the engineering workflow actively blocked on the native card while the relay HUD correctly reported `APPROVAL REQUIRED • ChatGPT tool approval • GitHub`.

Immediate acceptance policy is deliberately narrow:

- exact provider/card identity: `Allow ChatGPT to use GitHub?`;
- exact controls must include `Always allow`, `Deny`, and `Allow once`;
- the approval surface's conversation scroll root must already be at the bottom;
- only the Director-preauthorized `Always allow` control may be invoked;
- Google Drive, unknown providers, ambiguous text, missing controls, disabled/hidden controls, or non-bottom state remain fail-closed;
- emit explicit auto-approval telemetry.

Implementation: `dc5afa8fab1b182de64a3537e2f52da40e4087b6`; regression assertion: `5a5d0cd2077c91d2a6d1e2328cb970a1c137810c`. Live activation/proof remains required.


### R0 operator authority over redundancy — 2026-10-06T0618Z

Reliability means **keep the relay alive at all costs unless the human explicitly says stop**. Recovery redundancy must never fight an intentional operator shutdown.

Acceptance requirements:

- one obvious HUD STOP control sets the durable `.relay-paused` interlock before stopping the backend;
- watchdog/supervisor respect that interlock and do not resurrect the relay while it is set;
- HUD remains available while paused and visibly reports PAUSED so the operator has a recovery surface;
- one obvious HUD START control and easy-to-find `START-RELAY.bat` clear the interlock and restore supervision;
- an easy-to-find `STOP-RELAY.bat` provides the same emergency stop outside the HUD;
- intentional STOP/START is distinct in telemetry/logging from crash recovery;
- no redundancy plane may override explicit operator intent.


### Operator-control UX amendment — 2026-10-06T0641Z

- The HUD must not expose hidden mouse gestures that destroy the operator recovery surface.
- In particular, right-click must not close the HUD or imply relay shutdown.
- Relay START/STOP remains explicit and visible; intentional operator STOP continues to override all redundancy planes through the durable pause interlock.
- If a HUD-only exit is ever needed, it must be an explicit labeled control whose scope is unambiguous and distinct from stopping the relay.


### Result submit-once acceptance amendment — 2026-10-06T0647Z

PCE7.429 live evidence makes result submission a state-machine boundary, not a generic retry loop:

- ChatGPT send acceptance (`generation_started` or stable `composer_cleared`) permits exactly one transition to SUBMITTED.
- SUBMITTED persists across content-script reload and immediately suppresses automatic result resend/replay for that packet.
- The next state is `WAITING FOR GPT TURN END`; this watchdog may inspect DOM state, reconcile exact result visibility, capture/recover evidence, or escalate STALLED.
- The post-submit watchdog must not contain a Send path or Windows action path. Uncertain exact-turn visibility is not permission to submit the same result again.
- Only positive exact user-result recognition emits delivery-complete/operation-counted. Rotation accounting must therefore remain downstream of exact result visibility.
- Backend exact-once remains mandatory and independent; this change strengthens the browser delivery plane without removing watchdogs, leases, durable obligations, replay safety, or recovery redundancy.


### Whole-product STOP and rollback-first amendment — 2026-10-06T0701Z

- Explicit HUD/operator STOP must quiesce browser automation as well as the Windows listener. PAUSED is not accepted as a whole-product state while content-script result send/recovery loops continue.
- Browser delivery/recovery timers, deferred work, packet discovery and autonomous Send must yield to the durable operator pause until explicit START.
- This requirement must be implemented without weakening normal keep-alive/self-healing behavior when operator pause is absent.
- Every live candidate deployment now requires a new rollback snapshot of all files it changes. If the candidate breaks, restore the preceding snapshot first; do not stack speculative live edits on the broken candidate.
- Timestamped rollback evidence is indexed in `docs/ROLLBACK_INDEX_2026-10-06T0701Z_RELAY_RECOVERY_BOUNDARIES.md`.

## PCE8 rotation-budget amendment
Marker: `PCE8_ROTATION_BUDGET_V1`
At OP077 only 23 operations remain afterward. PCE9 rotation is P0 now. The next chat must be created/selected/named exactly **💻PC Engineering 9🔧**, handed off, identity-verified, and ownership-transferred before PCE8 retires.
