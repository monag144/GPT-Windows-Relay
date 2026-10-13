# Windows Relay canary #1 rejected — issuance/owner integration — 2026-10-12

## Observed, not inferred

The operator loaded the canonical persistent Firefox extension from `windows-relay/extension-persistent/`, paired with the local `bridge.json` bearer token and armed the backend. ChatGPT issued a read-only PowerShell canary with ID `RELAY-CANARY-20261012-1656-001`, `session=default`. The browser sent:

```text
[GPT_WINDOWS_FEEDBACK] {"version":1,"type":"RELAY_DIAGNOSTIC","source":"windows_browser_bridge","state":"ACTION_FAILED","packet_id":"RELAY-CANARY-20261012-1656-001","detail":"RelayError","recommended_action":"Before retry: read roadmap/facts/incidents/log; prove net-new progress; log this failure; update development log; preserve rollback; check PCE8/PCE9 budget; then diagnose and reissue with a new unique id."} [/GPT_WINDOWS_FEEDBACK]
```

`RelayError` is generic and does **not alone identify** the server-side subreason. The source at WIP `e6c87ab6` definitely contained a mismatched protocol: the persistent worker POSTed only `{packet}`, while the backend required `{packet,issuance,owner}` and a separately human-authorized `conversation_owner`. This is a sufficient identified defect; there may be additional runtime blockers. The feedback is not a verified execution receipt. Do not replay this ID as a fresh command or assume an arbitrary side effect happened.

## Code changes

Canonical source only: `windows-relay/windows_relay.py`, `windows-relay/extension-persistent/service_worker.js`, `extension-persistent/content.js`, `extension-persistent/manifest.json` bumped to **0.3.18**.

- Browser transport computes SHA-256 of exact UTF-8 action packet via WebCrypto; includes action ID/session/hash and the same content-tab URL/session/positive tab ID. Tampered or missing metadata rejects before backend execution.
- Backend enforces operator-bound conversation **and tab ID**, not only matching URL/session. A tab change requires renewed authorization.
- A missing backend owner triggers **one native Windows YES/NO confirmation** through `/owner-bind-request`. The dialog states conversation URL, session and tab ID; **NO is the default**. An affirmative local operator action binds the owner; refusal or unavailable desktop aborts. The existing separate operator-token `/owner-bind` route remains protected. No silent bearer-only owner claim.
- Firefox extension storage read/write failure is an error, not presumed success; stale owner tab and session mismatches reject.
- Backend denial details are surfaced instead of collapsing every `RelayError` into a generic diagnostic.
- Previously emitted PCE8/PCE9 governance and local rollback advice has been replaced in the canonical persistent content script. No local backups are created.

## Evidence and limitations

- Executed the published persistent worker in an isolated JavaScript mock environment, checking exact packet bytes, hashed issuance structure, owner/tab metadata, operator approval path, decline (without retry execution), wrong tab, storage failure and successful mocked response. It is a **mock behavior test**, not live Firefox or Windows proof.
- Added `windows-relay/tests/test_authenticated_transport.py`, `test_operator_owner_http.py`, and Node smoke `relay_action_transport_smoke.cjs` driven by `test_browser_transport_node.py`.
- These committed Python/Node regression tests still require an actual user-side run on the checked-out code, with isolated loopback HTTP fixtures and mocked process execution. The remote source is not proof of a live successful round trip.
- `session=default` stays allowed for the initial canary; backend requires the same bound session for subsequent actions. Browser tab transfers or new sessions may need a new operator-confirmed bind.
- Firefox extension already loaded before pull and Python relay already running before pull must be reloaded/restarted **only on operator instruction**, after offline tests. Pairing token must not be printed or shared.

## Next acceptance sequence

1. Fast-forward Main-Build WIP with `git pull --ff-only`; do **not** alter unique dirty/untracked runtime data or create local backups.
2. Run `python -B -m unittest discover -s windows-relay/tests -p test_authenticated_transport.py -v`, same for `test_operator_owner_http.py`, `test_browser_transport_node.py`, and `python -B -m unittest discover -s windows-relay/tests -p test_no_local_backups_policy.py -v`. Node smoke is automatically skipped if Node.js unavailable; run `node --check windows-relay/extension-persistent/service_worker.js` when present.
3. If passing, explicitly restart the canonical Python relay and reload the temporary `GPT Windows Relay v0.3.18` add-on in Firefox's `about:debugging#/runtime/this-firefox`. Reload will likely not require re-pairing, but if the popup says unpaired use the existing token from `%APPDATA%\GPTWindowsRelay\bridge.json` privately. Do not install alternate extensions.
4. Only after versions/provenance and arm state are confirmed, send a **new, unique-ID read-only canary** and answer the native operator confirmation (YES only for correct URL/session/tab). Record exact authenticated backend result or error. Do not suppress STOP/owner guards.

**No source version, static test, mock test, or authenticated pairing alone establishes a production command execution success.**
