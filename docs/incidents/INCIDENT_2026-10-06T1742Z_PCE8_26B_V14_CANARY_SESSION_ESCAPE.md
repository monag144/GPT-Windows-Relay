# Incident — 2026-10-06T1742Z — PCE8.26B v14 canary escaped managed conversation

**Status:** OPEN for deterministic managed-conversation reacquisition. Immediate live safety was restored automatically.

## Summary

PCE8.26B successfully activated the repaired v14 content runtime in the managed ChatGPT conversation. During the canary wait, an hours-old durable recovery obligation for `PCE8.6-restore-live-browser-content-to-verified-pre-spam` was restored from sessionStorage and repeatedly requested page refreshes.

The second stale recovery sequence ended at generic `https://chatgpt.com/` instead of the managed engineering conversation. The Director observed Firefox stranded on the home/new-chat screen while the HUD still appeared online and armed. Manual navigation back to the engineering conversation was required. Under the reliability roadmap, this is a failed browser takeover and an engineering incident.

## Evidence

- 17:42:18Z — fresh v14 runtime proven in `/c/6ac461e9-2940-83e8-b930-5d6a087da606`.
- 17:42:23Z — stale PCE8.6 recovery obligation stalled at age 25,878,710 ms.
- 17:42:27Z — first stale-obligation refresh requested.
- 17:47:24Z — the same stale PCE8.6 obligation stalled again.
- 17:47:27Z — second stale-obligation refresh requested.
- 17:47:35Z — v14 started at generic `https://chatgpt.com/`.
- 17:52:18Z — guarded canary timed out waiting for a future PCE8.27 packet that had not yet been issued and initiated rollback.
- 17:52:29Z — rollback activated proven v11.
- PCE8.27 verified all three live content copies at SHA-256 `26CE6B9BCD63EF5ACB2043BEF0216EBA5D42623AEAF733C98DF264E183F83ED5`.

## Root causes

1. Durable recovery state had packet identity and timestamps but no conversation identity and no maximum lifetime.
2. A legacy PCE8.6 obligation could therefore survive for hours and act inside a later runtime.
3. Runtime-start proof did not prove that Firefox remained attached to the intended managed conversation.
4. The canary waited for a future packet which had not been emitted, making its round-trip acceptance design invalid.

## Containment and repair

- Automatic rollback restored proven v11.
- `093604a` retires a backend-completed action before browser delivery begins.
- `4bf8b4d` identifies that repaired candidate as v14.
- `f888464` adds conversation scoping and expiry to durable recovery obligations and identifies source as v15.
- The field-derived recovery tests went red then green; the full suite is 271/271.
- v15 remains source-only. No new live deployment has occurred.

## Required acceptance before another live browser candidate

1. Positively identify and reacquire the exact managed conversation after extension reload, page reload, rollback, and tab/context loss.
2. Treat generic ChatGPT home, another conversation, or unidentified browser context as failed recovery.
3. Make the canary own a deterministic fresh round-trip instead of waiting for a later assistant packet.
4. Require runtime identity, conversation identity, fresh packet discovery, exact-once backend settlement, exact result delivery, and continued attachment to the expected conversation.
5. On failure, restore both the previous files/runtime and the managed browser context autonomously.

The separate whole-product STOP/quiescence incident remains open.
