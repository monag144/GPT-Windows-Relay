# Windows Relay HUD conversation controls — 2026-10-10

**Status: DESIGN REQUEST ONLY — not implemented, installed, tested, or approved for live deployment.**
**Canonical project:** `monag144/GPT-Windows-Relay` (`main`); live `Client/Relay` is a separate, currently divergent installation.
**Source:** Operator request dated October 10, 2026 Pacific. User explicitly wants these as **visible HUD functions/buttons**, not a shell or relay FORCE command. **No relay access or browser intervention is authorized by this document.**

## Operator problem and intended workflow

The Windows Relay can reject operations when the active Firefox ChatGPT tab is not the conversation legitimately bound to the relay, including diagnostics such as `relay_owner_unclaimed_inactive_tab` and `relay_owner_transfer_requires_claim`. Prior troubleshooting advice told the operator to:

> Bring this exact ChatGPT conversation to the foreground in Firefox.
> Open the Windows Relay extension or controls.
> Look for an option to Claim, Connect, or select the active conversation, if available.

That advice describes desirable UI, **not proof that those buttons currently exist**. Make that workflow discoverable directly in the Windows Relay HUD instead of asking the operator to search for hidden extension controls or type a FORCE command.

## Proposed HUD interface

Preserve all **five proven Client controls** unchanged: **START · STOP · RESTART · OFF · KILL**. Retain a distinct **RETRY** action as separately tested/planned; it is not FORCE, CLAIM, or the STOP override. Internal authenticated backend `armed` is a permission/quiescence state, **not an extra ARM button**.

Add these explicit, plainly labeled HUD interactions:

1. **FOCUS CHAT** — Bring the *verified bound Firefox tab and exact ChatGPT conversation* into the foreground. Resolve the target from real tab/conversation identity, not a guessed title, the newest ChatGPT tab, or any Firefox window. Show the selected tab and conversation identity in the HUD. If missing or ambiguous, ask the user to choose; do not focus a random conversation. Focusing alone **does not claim ownership** and **does not send a message**.
2. **SELECT CHAT / CLAIM–CONNECT** — Display the current *active* Firefox ChatGPT conversation and the recorded relay owner/session side by side. Provide an operator-clickable **SELECT CHAT** action when multiple candidates exist and a **CLAIM / CONNECT** action for the chosen, active exact conversation. Positively verify active/focused tab and conversation key, invoke only an existing or reviewed, authorized ownership-claim protocol, then show acknowledged owner/session/connection or the exact rejection reason. No silent ownership takeover, owner-record editing, spoofing, implicit force-arm, cross-chat packet reuse, or bypass of `relay_owner_transfer_requires_claim`. If a legitimate transfer is not safely supported, visibly block and describe the required user step; do **not** pretend claiming succeeded.
3. **FORCE** — A **visible clickable HUD button, not a command to type or a generic FORCE shell/relay action**. Its purpose is an immediate, **bounded reinspection of the current verified ChatGPT conversation's currently visible Windows Relay packet**, useful when a scanner appears stuck. It must not automatically reload Firefox, create/switch ChatGPT conversations, press Send, clear attempted/durable action IDs, resend uncertain output, replay a completed command, or evade STOP/ownership/session/collision rules. Only a previously unseen, authorized packet may proceed through the normal deduplicated execution path; otherwise show `already handled`, `in flight`, `no eligible packet`, `not connected`, or a precise guarded reason. Provide an observable result/status after the click; do not hide it behind a continually running background command.

### Placement and state

Place **FOCUS CHAT**, **SELECT/CLAIM–CONNECT**, and **FORCE** in the visible operator HUD near existing controls, using a compact layout that doesn't displace START/STOP/RESTART/OFF/KILL. Show: bound conversation (short identity), focused tab (or missing), ownership status (`connected / unclaimed / another conversation / transfer requires claim`), scanner state, last FORCE outcome, and whether STOP is active. Make buttons disabled with a reason when their preconditions fail. A user-initiated FOCUS/SELECT/CLAIM operation must be distinguishable from automated agent handoff.

## Safety invariants and exclusions

- **STOP / OFF / KILL always win**; no FORCE or claim may activate command execution through a stopped/disarmed runtime. Preserve generation/quiescence and the durable backend processed-action ledger.
- Never infer that matching extension version `1.1.0`, a file on disk, GitHub `main`, or a visible tab proves the actually loaded add-on/runtime or authorization. Loaded-code provenance and explicit owner acknowledgment are acceptance requirements.
- Guard active-tab focus, owner changes, scanner reinspection and action dispatch separately. Surface mismatches instead of resetting owner data. Never automatically take ownership from a different conversation.
- **RETRY is separate**: the development implementation currently refreshes a selected engineering tab. Its eventual behavior must remain explicit and guarded; clicking FORCE must not implicitly call RETRY or initiate a refresh.
- **No automatic new-chat/agent rotation**, new-agent navigation or scheduled ownership takeover. The only approved agent *handoff* is the existing one-shot `Run-Copy-Contents.cmd`, triggered when the user explicitly asks, per `docs/policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md`. Bringing an existing bound conversation into focus is not a new-chat handoff.
- Existing installed Client has START/STOP/RESTART/OFF/KILL while GitHub Main HUD has START/STOP/RETRY: **do not bulk-copy the Main HUD over the Client**. Merge selectively after review, test and rollback preparation.
- No modification to the current running Client, extension, Firefox tab, mission queue, or ownership record is requested by this design note.

## Future acceptance checklist (not yet complete)

- [ ] Verify exact-window/tab/conversation targeting, including multiple Firefox and ChatGPT tabs, closed/virtualized tabs, and owner mismatch.
- [ ] Positive operator-mediated CLAIM acknowledgment; reject unclaimed inactive tab, transfer without explicit claim, and ownership collision without execution.
- [ ] Click FORCE on an eligible *unattempted* current-chat packet: at most one normal execution/receipt. Click FORCE repeatedly on a completed/inflight/uncertain packet: zero additional side effects.
- [ ] Click FORCE while STOP/disarmed or while owner is another conversation: no execution, refresh, claim or navigation.
- [ ] Preserve all five installed buttons, distinct RETRY, visible feedback, and negative error diagnostics.
- [ ] Confirm actual loaded Firefox add-on identity and backend state before any rollout; perform isolated tests, rollback-backed staged merge, a live canary, and real receipt verification.
- [ ] Record results in the standard audit/incident process. **No feature is marked complete by creating this design document.**

## Related authoritative references

- `docs/roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md` (P1 HUD and failure detection).
- `docs/roadmap/WINDOWS_RELAY_MISSION_AND_PRIORITIES_2026-10-09.md`.
- `docs/facts/WINDOWS_RELAY_OPERATING_SAFETY_2026-10-09.md`.
- `docs/incidents/DND_WINDOWS_064_CODEX_RELAY_OWNERSHIP_TRANSFER_REQUIRED_2026-10-10.md` (actual owner-claim failure).
- `docs/policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md` (permanently retired automatic agent switching).
