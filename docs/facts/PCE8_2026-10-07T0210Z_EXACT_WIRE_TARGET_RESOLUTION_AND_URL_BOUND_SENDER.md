# PCE8 exact-wire outbound delivery, managed-target resolution, and URL-bound sender

Timestamp: 2026-10-07T02:10Z
Branch: `consumer/r29-firefox-offline-tray`

## Scope

This note freezes the source-accepted safety chain required before a Windows UIA outbound-delivery worker may be built. It does not enable Windows outbound ownership, start a worker, promote browser source to live, or perform a real ChatGPT send.

## Accepted chain

### 1. Crash-safe exact-wire delivery state

Commit `95b51bcff977c513cfd4766ac0097cd7622fffc7` (`relay: add crash-safe outbound delivery state foundation`) established the durable outbound-delivery phases:

- `READY`
- `SUBMITTING`
- `PRE_SUBMIT_FAILED`
- `SUBMITTED`
- `SUBMIT_UNCERTAIN`

The irreversible boundary is protected by persisting `SUBMITTING` before any future sender call can reach UIA `InvokePattern`. A process restart that finds `SUBMITTING` converts it to `SUBMIT_UNCERTAIN`; it must never automatically retry that packet.

The exact serialized `[GPT_WINDOWS_RESULT]` wire text is materialized and persisted before `READY`, and the outbound journal stores its `wire_result_path`. The worker must send that exact persisted wire text; it must not reconstruct the result from normalized or sorted JSON.

Attachment-bearing results remain ineligible for the Windows sender.

### 2. Exact-wire ordering failure that forced this design

The first PCE8.177 candidate demonstrated that reloading raw JSON through the relay's sorted `atomic_json` representation changes key order. That representation is semantically equivalent but not byte-identical to the completion-time wire result. The candidate was rejected and rolled back.

The corrected design persists the exact completion-time wire independently before publishing `READY`. This ordering is now an invariant.

### 3. Managed conversation URL is the durable target identity

Commit `013e1b663675364b5f19dcca28d7e734816e0e44` (`relay: resolve managed ChatGPT tab by conversation URL`) added `resolve-conversation-tab`.

The durable identity remains the existing managed ChatGPT conversation URL from consumer settings. An exact Firefox tab title is resolved just-in-time; no new durable tab-title setting was introduced.

Resolver requirements:

- inspect canonical Firefox `TabItem` objects only;
- canonical parent must be control type `Tab` with AutomationId `tabbrowser-tabs`;
- temporarily select candidate tabs and inspect the unique `urlbar-input`;
- normalize and compare the exact `https://chatgpt.com/c/<id>` conversation URL;
- return exactly one Firefox PID + exact tab title match;
- fail closed on zero or multiple matches, unreadable URL bar, selection failure, or restoration failure;
- restore original tab selection in `finally`;
- never touch the composer, clipboard, Send button, or any submission primitive.

### 4. Specialized sender is bound to title plus managed URL

Commit `027e9854eb2b2c55618ff7917dba01444e843c3e` (`relay: bind result sender to managed conversation URL`) hardened `send-relay-result`.

An exact tab title alone is not sufficient because two ChatGPT tabs may legitimately share the same title. The specialized sender therefore now requires both:

- the just-in-time exact tab title; and
- the normalized managed conversation URL.

After selecting the exact-title tab, the sender reads the unique `urlbar-input` and verifies the exact managed conversation URL before composer discovery. It rechecks that URL again at the final no-send boundary immediately before setting `$sendInvoked=$true` and invoking the Send button.

A URL mismatch therefore remains a `PRE_SUBMIT_FAILED` condition. Once `$sendInvoked=$true`, failure is fail-closed as `SUBMIT_UNCERTAIN` unless submission is positively confirmed.

The specialized sender continues to use guarded clipboard paste only, exact composer readback, semantic Send `InvokePattern`, no Enter fallback, and clipboard restoration in `finally`.

### 5. Duplicate-tail test correction

PCE8.188B was rejected and automatically rolled back because the historical anti-generated-tail test used a stale `len(src) < 32000` heuristic. The already accepted baseline was 31,913 characters, so legitimate URL-binding code exceeded the limit.

The replacement retains semantic singleton checks for major generated blocks and a looser 40,000-character runaway sanity ceiling. The accepted candidate was 33,182 characters and all singleton markers remained exactly one.

### 6. PCE8.187 audit-script failure

PCE8.187 failed inside its read-only audit wrapper because `$Action` was interpolated in a double-quoted PowerShell search string, producing an invalid `IndexOf` search. It caused no source or live mutation and is not classified as a relay-product runtime failure.

## Current source acceptance

At commit `027e9854eb2b2c55618ff7917dba01444e843c3e`:

- Windows suite: 312 / 312
- Consumer suite: 99 / 99
- specialized sender target identity: exact title + exact managed conversation URL
- initial URL check: before composer discovery
- final URL check: before irreversible Send Invoke
- Windows delivery worker: not added
- Windows outbound-owner enable endpoint/setter: not added
- real ChatGPT send during these source acceptances: none
- remote push: none

## Live boundary

The live browser plane remains accepted v16 with SHA-256:

`9541A890A80A8200F949E6D7DA7132C10335BFABD487E0B89047919C6B1B899E`

No resolver or sender source from this chain has been promoted by `sync-live.py`; `sync-live.py` remains prohibited because live/source planes intentionally diverge.

The live v16 browser does not contain the source-side exclusive Windows-owner compatibility gate, so Windows outbound ownership must not be enabled.

## Next source-only stage

Build a dormant Windows outbound-delivery worker with no production-startup hook and no owner-enable route.

Required worker behavior:

1. enumerate only claimable `READY` / `PRE_SUBMIT_FAILED` non-attachment deliveries;
2. remain inert unless state says armed and outbound owner is `windows`;
3. resolve the managed conversation URL to the current exact Firefox tab before claiming;
4. validate the exact persisted wire-result file;
5. recheck STOP / owner state immediately before claim;
6. claim durably, transitioning to `SUBMITTING` before any sender transaction;
7. call the URL-bound specialized sender exactly once;
8. map only `PRE_SUBMIT_FAILED`, `SUBMITTED`, or `SUBMIT_UNCERTAIN` into the journal finish operation;
9. treat an exception after claim as `SUBMIT_UNCERTAIN` unless it is provably pre-invoke;
10. serialize resolver + sender transactions with one process-local lock and ultimately one worker thread.

The dormant worker must initially be tested only with fake resolver/sender functions. No real UIA send may be used for synthetic testing.

## Later cutover gates

The following remain mandatory before Windows ownership can ever become live:

- promote/prove the browser-side exclusive-owner compatibility behavior;
- implement an owner generation/ACK barrier so browser relinquishment is proven before Windows can send;
- preserve whole-product STOP semantics across backend, browser, and Windows worker;
- define attachment handling or retain browser ownership for attachment-bearing results;
- serialize clipboard use against any other clipboard-based sender path;
- perform exactly one genuine relay-result canary on the exact managed engineering conversation, never a synthetic composer probe.
