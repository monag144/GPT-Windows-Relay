# Archived source fragment 22/23 — 2026-10-08T0752Z

Director supplied the complete CMD output from the proposed PCE7.433 break-glass staging chain. The pull fast-forwarded the local checkout from `7e2cf19` to `2ae9f24`, then `test_browser_contract.py` failed 4 of 51 tests. Because the command was chained with `&&`, execution stopped at that targeted suite: the PCE7.433 rollback directory was not created and no live file was copied.

The failing test process read a local `windows-relay/extension/content.js` whose runtime was still `v11-scroll-v5-delivery-v11-collapse-recovery` and which lacked the v13 submit-once state.

GitHub forensic readback proves this is local worktree divergence, not a bad remote branch: both remote commit `7e2cf198becc2d1884f27339c597e3adde323635` and remote commit `2ae9f246bd8867e273f450249682bab72a17a221` contain the identical v13 content blob SHA `39572edf843e680add6e3566748d5414276c53d2`, length 81350, marker `GPT_WINDOWS_RESULT_SUBMIT_ONCE_V1`, runtime `v11-scroll-v5-delivery-v13-submit-once-result-wrapper-fallback-approval-v3-uierror-v1`.

Conclusion: the local Git checkout already had a modified older `windows-relay/extension/content.js`; the fast-forward did not touch that path because the incoming commit range did not modify it. The test gate correctly prevented that stale worktree file from being promoted live.

Recovery must follow the new rollback-first rule: preserve the dirty local source file before restoring that path from HEAD, prove the source path is clean, rerun targeted/full tests, then create a new live rollback boundary before any staging.

## 2026-10-07 — PCE8 OP077 discipline checkpoint
Marker: `PCE8_OP077_DISCIPLINE_CHECKPOINT`
Real progress: f04b925 startup fix promoted; v17 browser microactivation/resume proven earlier; OP070 proved main/consumer launcher collision; OP073 recorded 398 Windows tests green; OP074 recorded 101 consumer tests green and harness source gate green. Debt: repeated full-cutover scaffold delayed root-cause discovery; several test-root mistakes wasted operations; OP075 failed transport; OP076 was rejected for exceeding relay command-size limits. GitHub auto-approval source exists but live auto-click telemetry remains unproven. Rotation to 💻PC Engineering 9🔧 is now P0.

## 2026-10-07 — PCE8 OP078 retry/latest-wins
Marker: `PCE8_OP078_RETRY_LATEST_WINS`
Adds modern HUD RETRY, selected-PC-Engineering refresh retry, latest-instruction-wins for stale/deferred browser ownership, every-result operation-discipline reminder, direct watchdog launch hardening, and PCE9 rotation budget P0. Safety invariant remains: do not preempt a genuinely inflight Windows side effect or overwrite an unresolved result draft. GitHub auto-approve live click remains unproven.

## 2026-10-07 — PCE8 OP079 retry integration repair
Marker: `PCE8_OP079_RETRY_INTEGRATION_REPAIR`
OP078 contained real new functionality but failed its Windows integration gate due to a malformed test insertion and unsynchronized content-script copies. OP079 preserves the functionality, repairs those two integration defects, reruns complete Windows and consumer suites, and only then promotes. PCE9 rotation remains P0; GitHub auto-approval live click remains unproven.

## 2026-10-07 — PCE8 OP085 rotation trigger
Marker: `PCE8_OP085_ROTATION_TRIGGER`
Preserve and roll back failed OP082 HUD source, then replace generic-home rotation in canonical source with a durable PCE8→PCE9 trigger. Exactly delivered PCE8 operations at/after OP087 persist a rotation request containing exact title `💻PC Engineering 9🔧`, session `pce9.1`, and bounded handoff, then notify the content plane. Create/rename/verification handler follows in OP086. Rotation is P0.

## 2026-10-07 — PCE8 OP086 rotation trigger gate repair
Marker: `PCE8_OP086_ROTATION_TRIGGER_GATE_REPAIR`
OP085 correctly restored the promoted source boundary and built the durable PCE9 rotation trigger, but its new test was pytest-style and `unittest` ran zero tests. OP086 repairs only that harness defect, then runs complete Windows and consumer suites before promotion. Rotation remains P0; no live reload occurs in this operation.

## 2026-10-07 — PCE8 OP089 rotation trigger normalization
Marker: `PCE8_OP089_ROTATION_TRIGGER_NORMALIZATION`
Normalize the persistent worker back to exact promoted Git bytes, retain rotation only in the temporary/dev worker that owns delivered-operation counting, and fix forced-rotation precedence over normal modulo-100 calculation. OP092 is the first eligible automatic PCE8→PCE9 trigger, leaving OP090 for create/rename implementation and OP091 for activation proof.

## 2026-10-07 — PCE8 OP090 consumer rotation contract
Marker: `PCE8_OP090_CONSUMER_ROTATION_CONTRACT`
OP089 reached 401/401 Windows green. Consumer acceptance still asserted the retired generic-home rotation mechanism. OP090 changes that test to require the durable exact PCE9 trigger instead: exact title/session, `relay_chat_rotation_start`, and no generic-home `chrome.tabs.update`. Full Windows + consumer suites gate promotion.

## 2026-10-07 — PCE8 OP091 durable rotation handler
Marker: `PCE8_OP091_ROTATION_HANDLER`
Build the content-side handler for the already-promoted PCE9 trigger. Rotation state survives same-origin navigation in sessionStorage; the handler opens fresh ChatGPT, submits the handoff once, waits for a new `/c/...` identity, renames that exact conversation to `💻PC Engineering 9🔧`, and emits `chat_rotation_verified` only after exact title/path verification. No live reload occurs in this operation.

## 2026-10-07 — PCE8 OP093 rotation-handler promotion
Marker: `PCE8_OP093_HANDLER_PROMOTION`
Back up before cache cleanup, remove generated Python cache, restore the protected relay bootstrap ordering, and gate the durable fresh-chat/handoff/exact-rename handler through complete Windows and consumer suites. First eligible live rotation moves to OP095 so OP094 can stage/reload the promoted extension safely.

## 2026-10-07 — PCE8 OP094 rotation runtime activation
Marker: `PCE8_OP094_ROTATION_RUNTIME_ACTIVATION`
Source trigger/handler are promoted and fully gated. OP094 stages only the temporary Firefox extension worker/content into the live tree, preserves rollback copies, and schedules a delayed temporary-addon reload plus PCE8 tab refresh so OP094 result delivery is not disrupted. OP095 must first verify the activation receipt before serving as live rotation acceptance.

## 2026-10-07 — PCE8 OP096 rotation forensics
Marker: `PCE8_OP096_ROTATION_FORENSICS`
Non-trigger diagnostic operation. OP094 Reload/refresh calls were successful; its final-title acceptance was a transient-title false negative. OP095 post-delivery classification: **OP095_NOT_COUNTED_AFTER_EXACT_VISIBLE_RESULT**. Current Firefox URL observed by UIA: `None`. No rotation-triggering PCE8BOOT ID is used in OP096.

## 2026-10-07 — PCE8 OP097 result-turn recognition
Marker: `PCE8_OP097_RESULT_TURN_RECOGNITION`
Repair the exact-delivery boundary isolated by OP096: accept current element-agnostic `[data-turn=user]` and `[data-testid^=conversation-turn-]` wrappers while preserving explicit assistant rejection and composer exclusion. Move the first eligible engineering trigger to OP099 so OP098 can activate/prove the repaired runtime without retroactively rotating on OP095.

## 2026-10-07 — PCE8 OP098 result-recognition activation
Marker: `PCE8_OP098_RESULT_RECOGNITION_ACTIVATION`
Activate the OP097 element-agnostic exact-result recognition fix in the temporary Firefox extension. OP098 is intentionally non-triggering. Live activation acceptance uses fresh `content_script_started` plus content/integration telemetry after delayed add-on reload and PCE8 refresh; transient tab title is informational only. OP099 remains the first eligible automatic PCE8→PCE9 rotation trigger.

## 2026-10-07 — PCE8 OP099 final rotation trigger
Marker: `PCE8_OP099_FINAL_ROTATION_TRIGGER`
OP098 telemetry-based activation is green. Live source contains the OP099 engineering threshold, durable fresh-chat/rename handler, and repaired element-agnostic exact-result recognition. OP099 performs no browser mutation. Its exact visible result delivery is the final PCE8 live acceptance trigger. PCE9 must verify `op099-rotation-acceptance.json` before further engineering mutation.

## 2026-10-07 — PCE8 OP101 control-harness New chat rescue
Marker: `PCE8_OP101_CONTROL_HARNESS_NEW_CHAT_RESCUE`
