# Archived source fragment 21/23 — 2026-10-08T0752Z

The Director staged the repaired files behind a fresh rollback directory `Client\Relay\rollback\PCE7.428-pre-repaired-stage-20261006T0635Z`. All 12 copy operations succeeded; live targeted validation returned **17 tests, OK**; `hud.py --once` returned `online:false`, `title:"PAUSED"`, `backend:"Relay PAUSED • operator stop"`; and CMD printed `RELAY_REMAINS_PAUSED`.

A simultaneous screenshot still showed the *already-running* HUD window as `OFFLINE` with stale `DELIVERING` evidence aged ~3304 s. This does not contradict the staged HUD proof: an existing Python/Tk process does not reload when `hud.py` is replaced on disk. The visible instance was old in-memory code. Restart only the HUD process while leaving `.relay-paused` set; the newly launched HUD should then report PAUSED and expose the new START/STOP controls. Do not resume the relay merely to refresh the HUD.


## 2026-10-06T0641Z — PCE7 HUD hidden right-click close rejected

Director live acceptance of the repaired PAUSED HUD proved the explicit START/STOP operator controls are visible and usable. During that recovery, the Director identified the legacy right-click gesture that destroyed the entire HUD window as surprising and hostile to the operator-control mission.

Decision: remove the hidden `<Button-3>` → `root.destroy()` binding. Relay/HUD lifecycle actions must be explicit, visible controls; an incidental right-click must not remove the recovery surface. This is a source-release correction and does not require destabilizing the current paused/live bring-up solely to restage the HUD.

The repaired build remains rollback-protected by the PCE7.428 pre-stage backup. Basic relay + Firefox recovery is the next live acceptance step; watchdog runtime cutover remains deferred until ordinary relay execution is stable.


## 2026-10-06T0647Z — PCE7.429 live duplicate-result recurrence isolates post-submit resend defect

After the Director restarted the repaired relay and reloaded Firefox, PCE7.429 executed immediately and exactly once at the Windows boundary. Evidence: backend `ok=true`, `armed=true`, pause marker absent, fresh Firefox content-script start at 06:44:53Z, runtime `delivery-v12-result-wrapper-fallback-approval-v3-uierror-v1`, and a single immediate `DISCOVERED -> execution_requested -> action_received` path.

However, after the first PCE7.429 result reached ChatGPT, the identical saved result was injected into the conversation again instead of the next PCE7.430 probe taking ownership. This reproduces the 425/426 class without evidence of Windows re-execution: backend exact-once remains the safety boundary; browser result submission/retirement is the failing layer.

Source inspection found the concrete resend permission: `waitForDeliveryConfirmation()` already observed strong ChatGPT acceptance signals (`generation_started` or stable `composer_cleared`) but returned failure unless an exact user-result DOM turn was positively recognized. `injectConfirmed()` then interpreted that visibility uncertainty as permission to click Send again, up to three attempts.

Correction committed in `0c67c623d2036c93d318fcefdf346ca8236561c3`: delivery-v13 introduces a durable submit-once state. After generation starts or the composer is stably cleared, the packet becomes SUBMITTED and is persisted in session storage/attempted history. The relay then enters `WAITING FOR GPT TURN END`; its watchdog may observe and reconcile but contains no Send path and no backend action path. Exact user-turn recognition later emits delivery-complete/counting. Watchdog expiry emits explicit telemetry with `resend=false` and `reexecution=false`.

Regression contract: `a23835a8b6d3fde5d9b5916bbf987283b19f2b0d`. HUD vocabulary: `184ba68b0e8b536b8462fe55795e9b61d03fc3d6`. Remote V8 parse and structural invariants passed before live staging.


## 2026-10-06T0649Z — PCE7.430 confirms duplicate Send, not duplicate Windows execution

PCE7.430 eventually executed after the duplicate 429 result and supplied the exact event counts for PCE7.429. This supersedes the temporary conversational assumption that 430 had been displaced.

Confirmed PCE7.429 lifecycle:
- `relay_packet_discovered=1`
- `relay_action_execution_requested=1`
- `relay_result_received=1`
- `relay_result_text_set=2`
- `relay_result_send_attempt=2`
- `relay_result_send_clicked=2`
- `relay_result_send_unconfirmed=2`
- `relay_result_delivery_failed=1`
- `relay_result_delivery_retry_deferred=1`

The backend processed record remains a single completed PCE7.429 operation. Therefore the incident is positively isolated to browser result submission: one Windows execution produced a saved result, but the content runtime clicked ChatGPT Send twice because exact user-turn confirmation was not recognized. This is direct live justification for the delivery-v13 submit-once boundary in commit `0c67c623d2036c93d318fcefdf346ca8236561c3`.

PCE7.431 was already emitted to validate and stage delivery-v13. It must not be redundantly reissued merely because queue/recovery ordering delayed it.


## 2026-10-06T0654Z — PCE7.430 result also duplicated under delivery-v12

The PCE7.430 saved result itself appeared in ChatGPT a second time after its first successful arrival. This reproduces the same browser-side resend pathology on the very forensic probe that proved it for 429. The incident is therefore systematic in the active delivery-v12 runtime, not packet-specific.

No new operation is being issued while the old delivery owner exhausts its bounded attempts. PCE7.431 remains the already-emitted next obligation: validate the repaired source, create a new rollback boundary, and stage delivery-v13 without reloading mid-operation. This avoids worsening the queue and preserves backend exact-once.


## 2026-10-06T0655Z — PCE7.431 validation correctly blocks staging on stale runtime assertion

PCE7.431 reached the Windows backend and failed during the first targeted `test_browser_contract.py` run, before rollback creation or live-file staging. Live delivery-v12 therefore remained untouched.

The failing contract still asserted the older delivery-v11 runtime identity in two places. Delivery-v13 intentionally changes runtime identity so live activation can be distinguished. Both assertions were updated to require the full v13 identity in `23d77cc2021608831af0a45e9b1532848c1b487a`. Re-run must still pass targeted browser/HUD tests and the entire Windows-relay suite before staging.


## 2026-10-06T0657Z — Old PCE7.429 backend replay proves v12 can loop beyond three send attempts

After three visible PCE7.431 copies, the active v12 content runtime resurfaced PCE7.429 again. The returned envelope explicitly reported `replayed:true` with the original 06:46:37Z/06:46:38Z execution timestamps and saved-result path. Therefore the failure is broader than one three-attempt `injectConfirmed` loop: recovery can rediscover an old assistant action after that loop, call the backend with the same ID, receive the exact-once saved result, and re-enter result delivery. No Windows side effect re-executed, but browser result spam can repeat indefinitely.

This establishes a break-glass deployment requirement: when the currently loaded content runtime itself is the looping fault domain, disable/remove that extension runtime before staging/activating the repaired runtime. Backend exact-once is necessary but cannot by itself stop saved-result delivery spam.


## 2026-10-06T0701Z — Director STOP exposes browser-quiescence gap; rollback-first rule adopted

Director clicked HUD STOP during the v12 result-replay storm. HUD correctly changed to PAUSED, but saved-result spam continued. This is now a distinct incident: [INCIDENT_2026-10-06T0701Z_HUD_STOP_PAUSED_BUT_BROWSER_RESULT_SPAM_CONTINUED.md](./INCIDENT_2026-10-06T0701Z_HUD_STOP_PAUSED_BUT_BROWSER_RESULT_SPAM_CONTINUED.md).

The observation proves that the durable pause interlock currently owns backend/supervisor resurrection but does not synchronously cancel already-running browser result/recovery loops. Operator STOP acceptance is expanded to whole-product quiescence.

Director also established a deployment rule: create a fresh live rollback snapshot before every live change; when a candidate breaks, restore the previous snapshot before further experimentation. Known boundaries and non-boundaries are indexed in [ROLLBACK_INDEX_2026-10-06T0701Z_RELAY_RECOVERY_BOUNDARIES.md](./ROLLBACK_INDEX_2026-10-06T0701Z_RELAY_RECOVERY_BOUNDARIES.md).


## 2026-10-06T0704Z — PCE7.433 break-glass command blocked by dirty local source checkout before backup/staging

