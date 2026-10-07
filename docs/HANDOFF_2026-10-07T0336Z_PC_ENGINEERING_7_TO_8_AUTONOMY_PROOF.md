# PC Engineering 7 → PC Engineering 8 handoff — autonomy proof gate

Timestamp: 2026-10-07T03:36Z  
Canonical Windows repository: `monag144/GPT-Windows-Relay`  
Canonical branch: `main`  
Canonical migration snapshot at handoff review: `1054197bd13c14be25e3b6bc96913315795fc126`

## Naming / rotation contract

- The engineering agent is the chat generation: PC Engineering 8 is **PCE8**.
- The numbered engineering checkpoint and the A-suffix are different layers.
- A new numbered checkpoint starts its sub-operations at **A1**.
- Therefore the next checkpoint after PCE8.199 is **PCE8.200A1**, not PCE8.199A4.
- At the next 100-turn agent rotation, the relay must create/select and verify the next managed chat automatically as **💻PC Engineering 9🔧**, including the emojis. Manual chat creation/renaming is an engineering incident.

## Canonical-repository reconciliation warning

The repository migration is clean, but the canonical GitHub snapshot does **not** yet contain the latest local PCE8 source-accepted work from the old Windows checkout.

At review time, canonical `main` does not contain:

- `windows-relay/windows_outbound_worker.py`
- `docs/PCE8_2026-10-07T0210Z_EXACT_WIRE_TARGET_RESOLUTION_AND_URL_BOUND_SENDER.md`

The old local Windows engineering branch had source-accepted work through:

- URL-bound specialized Windows result sender: local commit `027e9854eb2b2c55618ff7917dba01444e843c3e`
- exact-wire/target-safety engineering note: local commit `b738c2c52526a4348ad65643e5e7db73329b1823`
- dormant Windows outbound worker foundation: local commit `ea9dd95d2f4ed7a205580527873fcb7d6347b08c`

Do not overwrite either side. First reconcile the local unpushed PCE8 work into the new canonical Windows repository, preserving the Job Application Engine v2 and the migrated PCE7/HUD/recovery tree.

## Completed PCE8 work before rotation

Source-accepted and locally committed before the repository split:

1. Specialized Windows outbound result sender hardened to exact tab title + exact managed conversation URL, with URL revalidation before composer work and again immediately before the irreversible send boundary.
2. Full acceptance for that sender: 312 Windows tests + 99 consumer tests.
3. Durable exact-wire outbound state foundation documented: READY / SUBMITTING / PRE_SUBMIT_FAILED / SUBMITTED / SUBMIT_UNCERTAIN; restart converts SUBMITTING to SUBMIT_UNCERTAIN; no automatic resend after uncertainty.
4. Managed conversation URL → exact Firefox tab resolver source-accepted.
5. Dormant Windows outbound worker source-accepted and committed; fake actuators only, one packet per run_once, no production startup wiring, no owner-enable route.
6. Full dormant-worker regression: 321 Windows tests + 99 consumer tests.
7. Ownership-handoff generation barrier design audited through PCE8.199. The PCE8.199 patcher was only being assembled; it had **not** been executed against source and must not be treated as accepted implementation.

## Control-harness review

`consumer/control_harness.py` is useful but not sufficient for autonomous closure of the remaining roadmap.

Current harness v1 provides:

- exact-byte SHA-256 dedupe;
- timestamped incident-file creation;
- deduplicated reflection logging;
- baseline/candidate improvement gating;
- a high-level continuous-improvement contract.

It does **not** currently provide a runtime acceptance state machine proving the Director's remaining autonomy requirements, nor does it itself drive recovery, rotation, or proof collection.

PCE8 must extend the harness so a run cannot declare autonomy complete without machine-verifiable runtime evidence.

## Mandatory PCE8 runtime proof gates

### A. GitHub approval auto-accept proof

The source already contains the deliberately narrow GitHub policy marker `GPT_CHATGPT_GITHUB_APPROVAL_AUTOCLICK_V1`.

PCE8 must produce live proof, not only static source evidence, that the exact native card:

`Allow ChatGPT to use GitHub?`

with all three controls:

- `Always allow`
- `Deny`
- `Allow once`

is positively identified at the bottom of the managed conversation and automatically invokes only `Always allow`.

Required evidence includes the browser telemetry event:

`chatgpt_tool_approval_autoapproved`

with GitHub / Always allow / bottom / exact-surface details, plus continued workflow progress without a user click.

### B. Traffic-flow error detection → autonomous refresh → recovery proof

Existing source detects visible ChatGPT failures such as `Error in input stream`, network/connection interruption, and generation failure.

Existing durable packet recovery can emit:

- `relay_scanner_stalled`
- `relay_page_refresh_requested`

and call `location.reload()` after its bounded deadman.

However, current recovery-supervisor behavior for a visible UI error is primarily diagnostic capture; the autonomous proof path still needs to demonstrate or add a deterministic refresh/recovery action for the failure the Director has previously had to repair manually.

Required live proof sequence:

1. inject or reproduce a bounded, safe traffic-flow failure;
2. detect it without Director diagnosis;
3. capture evidence before repair;
4. request/perform the managed ChatGPT refresh automatically;
5. reacquire the exact managed conversation;
6. resume relay progress;
7. prove exactly-once behavior for the affected packet;
8. user rescue count remains zero.

### C. Manual-intervention hole closure

Treat every previously required manual browser intervention as an acceptance failure until proven automated:

- manual ChatGPT refresh;
- manual extension reload/about:debugging work;
- manual return to the engineering conversation;
- manual fresh-chat creation;
- manual chat naming;
- manual GitHub approval click;
- manual relay restart after recoverable crash;
- stale pre-STOP packet surprise execution.

The harness must count user rescues and fail promotion when the count is nonzero.

### D. Rotation proof

Before PCE8 retires, prove the next rotation end-to-end:

- create a fresh managed engineering conversation;
- name it exactly **💻PC Engineering 9🔧**;
- inject the timestamped handoff;
- verify the title and managed conversation identity;
- switch ownership to the new chat;
- prevent stale PCE8 queued/deferred actions from hijacking PCE9.

## Immediate PCE8 order

1. Reconcile old local PCE8 commits with new canonical `GPT-Windows-Relay/main`.
2. Extend the control harness with explicit runtime proof gates and user-rescue accounting.
3. Preserve operator STOP as the highest-priority execution barrier; implement stale queued-action cancellation/epoch protection before claiming zero-touch.
4. Prove GitHub auto-approval live.
5. Prove traffic-flow error detection + autonomous refresh/recovery live.
6. Prove remaining manual-intervention holes closed.
7. Resume ownership-generation barrier work only after the canonical/local reconciliation is clean.
8. Continue roadmap autonomously; ask the Director only when a genuinely non-automatable or safety-sensitive choice remains.

## Non-negotiable operating rules

- Windows work uses `monag144/GPT-Windows-Relay` → `main`.
- Android/Termux work remains in `monag144/GPT-Termux-Relay`.
- No manual Firefox recovery instructions to the Director.
- Never automatically resend after an uncertain send boundary.
- Preserve exact-once backend semantics.
- Explicit operator STOP/standby invalidates stale queued/discovered actions.
- Runtime proof is required; source markers alone are not acceptance.
