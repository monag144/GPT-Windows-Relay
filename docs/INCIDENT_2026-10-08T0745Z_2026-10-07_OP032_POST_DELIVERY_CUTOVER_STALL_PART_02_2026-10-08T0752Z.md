# Archived source fragment 2/2 — 2026-10-08T0752Z

2. Why rollback was not self-contained against version skew after restoring older adapter files.

### Recovery decision

A **targeted partial recovery** is required before another cutover attempt:

- terminate the stale OP032 scheduled task/helper process tree;
- verify the restored v16 live tree is coherent and healthy;
- normalize HUD cardinality;
- leave Firefox on the ChatGPT conversation and close/ignore the residual debugging tab as appropriate;
- verify backend, supervisor, browser bridge, and current runtime identity;
- preserve the OP030 backup and helper logs as evidence.

Do **not** attempt the v17 cutover again until the post-delivery completion gate and rollback adapter-version dependency are redesigned.


## Recovery update — OP034 targeted partial recovery

OP034 completed the targeted recovery successfully.

Confirmed:

- stale scheduled task `GPTWindowsRelay-PCE8-OP032-LiveCutover` was removed;
- stale helper processes were terminated and no helper processes remained;
- the OP030 pre-cutover snapshot was proven fully restored:
  - `RESTORE_MISSING=0`
  - `RESTORE_MISMATCH=0`
  - `RESTORE_UNEXPECTED=0`
- backend/control health is restored:
  - `RUNNING PID=12644 PAUSED=False`
  - listener is present on PID 12644;
- HUD process topology is one logical launcher/root with one interpreter child:
  - raw pythonw count 2;
  - logical root count 1;
- Firefox is back on the intended **PC Engineering 8** tab;
- the debugging tab remains open but is unselected and retained as incident evidence;
- v17 was **not** reattempted.

The runtime event probe reported `v11-scroll-v5-delivery-v11-collapse-recovery`, but that event timestamp was 2026-10-05 and therefore is not accepted as proof of the currently loaded extension runtime. A follow-up read-only inspection is required to identify the active browser runtime before any new cutover design is armed.

**Recovery status:** targeted partial recovery complete; machine returned to a stable pre-cutover state. No additional rollback is currently indicated. The incident remains open because the failed post-delivery gate and rollback version-skew defects still require correction before a v17 reattempt.


## Forensic update — OP035/OP036

OP035 proved the OP032 helper waited on the wrong Firefox delivery signal. The active `%LOCALAPPDATA%\\GPTWindowsRelay` Firefox stream emitted `relay_result_received`, `relay_result_send_accepted`, and later `relay_result_turn_end_watchdog_expired`, but **zero** `relay_result_delivery_complete` events in the inspected recent history. OP032 itself reached `relay_result_send_accepted` at 04:55:44Z and the result was visible to the user. Historical `relay_result_delivery_complete` events were found only in the separate `%LOCALAPPDATA%\\GPTWindowsRelayConsumer` Chrome lineage. Therefore the helper's `relay_result_delivery_complete` gate was invalid for the active Firefox runtime.

OP036 isolated the rollback adapter mismatch. Both the restored live adapter and canonical adapter support `--firefox-pid` for `ensure-addon`, `refresh-tab`, and `send-chatgpt-prompt`. However, the restored live adapter's `list-tabs` parser does **not** accept `--firefox-pid`, while canonical `list-tabs` does. The failed rollback repeatedly invoked `list-tabs --firefox-pid 18160`, causing the observed argument errors and preventing the helper from detecting the debugging tab after restoring the older adapter.

Recovery design requirements are now explicit: use `relay_result_send_accepted` as the pre-cutover handoff gate; do not use the turn-end watchdog as a completion gate; and make rollback/browser discovery compatible with both adapter generations, e.g. by using unscoped `list-tabs` for discovery before passing the discovered Firefox PID only to subcommands supported by both generations.
