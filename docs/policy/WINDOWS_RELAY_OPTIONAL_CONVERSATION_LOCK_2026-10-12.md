# Conversation owner lock is optional — 2026-10-12

**User direction:** The persistent per-conversation owner lock was slowing handoffs. Make it a toggle in the canonical Windows Relay HUD and default it to **OFF**. This change is developer source on `wip/windows-relay-rebuilt-resynced-2047-101026`, not proof the installed backend, running HUD, or Firefox add-on has been updated.

## Semantics

- **OWNER LOCK OFF (default):** The persistent conversation-key/session/tab binding is not required for each new conversation. Each action must still originate from the currently active Firefox tab showing `chatgpt.com`; the background worker compares sender URL, declared conversation URL, and active tab ID before dispatch.
- **OWNER LOCK ON:** The worker remembers its conversation owner. The backend enforces the separately operator-approved conversation, session and tab ID. Enabling a lock clears the previously bound backend owner; the worker also clears any stale owner when the backend lock epoch changes. A native YES/NO operator authorization is required for the new owner.
- **HUD:** An independent `OWNER LOCK: OFF/ON` setting alongside (not replacing) the five existing START, STOP, RESTART, OFF, KILL controls. Switching the setting requires a local native Windows confirmation (default NO) and persists in relay state.
- **Never toggled:** Bearer pairing, operator START/STOP/arming, exact packet-hash issuance validation, required positive tab ID, issuance journal identity, and duplicate-execution barriers.
- **Risk accepted in this setting:** With LOCK OFF, any eligible *focused* ChatGPT conversation can issue commands while the relay is armed; owner-specific isolation is reduced. STOP remains the immediate global interlock.
- Backend service and Firefox extension must be updated together. Source-only commit or checkout fast-forward does **not** change code already running in memory; do not restart/reload production until offline native tests pass and the operator authorizes deployment.
- The annotated v0.3.18 October 12 live-verified tag stays untouched.

## Tests and acceptance

Source adds Windows transport and HTTP tests for default-OFF, ON/OFF transitions, denial, invalid inputs, unchanged arming, focused-tab enforcement, and epoch invalidation. Run project health and unit test sweeps on Windows before any runtime reload. Native live cross-conversation behavior remains unverified until separate approved canaries demonstrate it.

**No local backup copies, alternate runtime, or destructive cleanup.**