# Termux contamination / Windows reconciliation audit — 2026-10-07T2034Z

## Scope

Migration source snapshot: old Termux `consumer/r29-firefox-offline-tray@d69666da530390146ba093dc1138dc794541b861`.
Runaway Windows work later reached old Termux r29 `249e3bb46c6ea57968d9ecf5157d73867a7f918d`.

The damage is **localized to the old r29 Windows branch** among the checked Windows-era branches. `development/runtime-control`, `consumer/one-click-go`, r26, r27, and r28 show no commits after 2026-10-06T00:00Z in the audit.

Post-split r29 drift:
- 35 commits;
- 63 changed files;
- 4,779 additions / 354 deletions;
- 32 `windows-relay/`, 5 `consumer/`, 26 `docs/`.

Against current `GPT-Windows-Relay/main`:
- 10 files already byte-identical;
- 24 files divergent;
- 29 files absent from Windows.

Do not copy r29 wholesale. Reconcile this bounded set.

## Already identical — no move needed

- `consumer/browser_manager.py`
- `consumer/tests/test_managed_conversation_identity.py`
- `consumer/tests/test_recovery_supervisor.py`
- `windows-relay/firefox_adapter.py`
- `windows-relay/tests/test_firefox_adapter.py`
- `windows-relay/tests/test_whole_product_stop_contract.py`
- `windows-relay/tests/test_windows_outbound_worker.py`
- `windows-relay/tests/test_windows_tools.py`
- `windows-relay/uia_control_action.ps1`
- `windows-relay/windows_outbound_worker.py`

## Divergent — merge/reconcile, never blind overwrite

- `consumer/recovery_supervisor.py`
- `consumer/tests/test_chatgpt_content_contract.py`
- `docs/INCIDENT_2026-10-06T0953Z_PCE7_445_447_HUD_CONTROL_CUTOVER_CHAIN.md`
- `docs/RELAY_OPERATIONAL_RULES.md`
- `docs/ROLLBACK_INDEX_2026-10-06T0701Z_RELAY_RECOVERY_BOUNDARIES.md`
- `docs/windows-relay-engineering-log-2026-10-01.md`
- `docs/windows-relay-established-facts.md`
- `docs/windows-relay-mission-and-roadmap.md`
- `windows-relay/TASKS.md`
- `windows-relay/content.js`
- `windows-relay/extension-persistent/content.js`
- `windows-relay/extension-persistent/service_worker.js`
- `windows-relay/extension/content.js`
- `windows-relay/extension/manifest.json`
- `windows-relay/extension/service_worker.js`
- `windows-relay/firefox_tab_adapter.ps1`
- `windows-relay/hud.py`
- `windows-relay/relay-control.ps1`
- `windows-relay/relay-watchdog-loop.ps1`
- `windows-relay/sync-live.py`
- `windows-relay/tests/test_browser_contract.py`
- `windows-relay/tests/test_hud.py`
- `windows-relay/tests/test_protocol.py`
- `windows-relay/windows_relay.py`

## Missing from Windows — review/import valid work

Documentation/evidence:
- `docs/ACCEPTANCE_2026-10-06T2219Z_PCE8_V16_BROWSER_RECOVERY.md`
- `docs/ACCEPTANCE_2026-10-06T2236Z_PCE8_STALE_OWNER_LEASE_DEADMAN.md`
- `docs/INCIDENT_2026-10-06T1742Z_PCE8_26B_V14_CANARY_SESSION_ESCAPE.md`
- `docs/INCIDENT_2026-10-06T2031Z_PCE8_61_STALE_DRAFT_RECOVERY_OWNER_LEAK.md`
- `docs/INCIDENT_2026-10-06T2200Z_PCE8_89_SYNTHETIC_COMPOSER_PROBE_SUBMISSION.md`
- `docs/INCIDENT_2026-10-06T2231Z_PCE8_113_STALE_OWNER_HELPER_FALSE_NEGATIVE.md`
- `docs/INCIDENT_2026-10-07T0013Z_PCE8_149A_GET_HISTORY_ALIAS_AND_INPUT_STREAM_ERROR.md`
- nine compact PCE9 incident files from OP101-era diagnostics;
- three PCE8 architecture/acceptance records at 2026-10-07T0002Z, T0101Z, T0210Z.

Runtime/tests:
- `windows-relay/run-control.ps1`
- `windows-relay/tests/test_control_launcher_split_pce9.py`
- `windows-relay/tests/test_firefox_nested_picker_pce9.py`
- `windows-relay/tests/test_firefox_temp_manifest_compat_pce9.py`
- `windows-relay/tests/test_hud_full_control_surface_pce9.py`
- `windows-relay/tests/test_result_turn_div_wrapper_pce9.py`
- `windows-relay/tests/test_result_turn_match_diagnostic_pce9.py`
- `windows-relay/tests/test_result_turn_user_message_class_selector_pce9.py`
- `windows-relay/tests/test_sync_live_manifest_pce9.py`

## Cleanup order

1. Preserve the old r29 head and migration anchor as read-only evidence.
2. Reconcile source/tests into Windows main with targeted diffs and full suites.
3. Import only useful evidence docs, renaming/splitting them to the <=10 KiB timestamped structure where practical.
4. Verify Windows main/live runtime convergence.
5. Only then clean the Termux r29 branch of Windows-specific post-split work or freeze it as historical contamination. Do not delete evidence first.
