# PCE16.033 STOP admission and restart rearm safety finding — 2026-10-10

**Repository:** `monag144/GPT-Windows-Relay/main`. **Status: OPEN; confirmed in isolated V9, NOT shown in live Client.** Native receipt `PCE16.033-isolated-operator-stop-dispatch-and-restart-gap-proof`, session `pce16.1`, `OK`, exit 0, finished 2026-10-10 23:49:33 UTC; all 21 checks true. The test is successful because it **reproduced a safety defect**, not because STOP protection was accepted.

## Evidence and interpretation
- Offline `State.set_armed(False)` disarmed an isolated instance. Direct `backend.process()` for a new synthetic action passed through `State.claim_or_lookup()` to its intercepted `execute()` callback **once**, while `runtime.armed == False`. No actual subprocess was created; no live state, browser, localhost listener or Client accessed.
- The HTTP `/action` handler performs `if not self.server.state.armed` before `process`, **not** inside the atomic claim. Even HTTP admission can race with a concurrent STOP. Other entrypoints (`stdin`) may bypass the HTTP guard.
- Isolated `State.load()` unconditionally wrote `self.data['armed']=True` and `main()` explicitly called `st.set_armed(True)` twice across its mode branches. Reloading a persisted STOP state silently returned `armed=True`, while its generation remained nonzero. A restart from STOP therefore lacked explicit START authorization in this source version.
- Synthetic fixture result: `synthetic_execution_after_disarm=1`, `new_id_claim_accepted_while_disarmed=true`, `restart_rearmed_without_operator_request=true`, stop generation preserved, `actual_subprocess_started=false`, `real_http_requests=0`. A live unauthorized execution is **not established**.

## Corrective scope and limitations
- Before .034 read canonical harness/backlog/mission/facts and this incident and run original `engineering_preflight`. Apply the smallest isolated source patch to a **new** candidate leaving V9 and working Client unchanged.
- Make `claim_or_lookup` check `self.armed` **inside its self.lock** before durable SQLite claim to prevent disarmed ID allocation; ensure process calls through the claim path. Test disarmed rejection and that STOP raced between HTTP precheck and locked claim refuses admission.
- Add a second explicit dispatch-authority check before execute, exercising synthetic STOP between durable claim and attempted invocation; existing tombstone must prevent unsafe automatic reissue. Keep no real command or network.
- On restart retain persisted `armed` state; do not force-ARM within `load()` or `main()` unless the user explicitly requests START. Preserve stop_generation, browser quiescence, existing five HUD controls and exact-once identity rules. Verify explicit `set_armed(True)` permits new synthetic action.
- **Caveat:** a check just before `execute()` does not make STOP atomic with the OS subprocess spawn. A robust launch/STOP handoff (with explicit pre-spawn interlock, cancellation semantics and owner/authenticated ingress) still requires separate design and tests. Never call this patch a full live STOP acceptance.
- No automatic ChatGPT conversation/agent switching, owner bypass, runtime state clearing or original deployed Client code mutation.

**Governance:** PCE16.033 consumed and returned OK. At PCE16.035 audit .030–.034 first. No twenty-operation review due until PCE16.040.
