# Archived source fragment 20/23 — 2026-10-08T0752Z

After PCE7.425 successfully forced a Firefox refresh, backend exact-once worked: the returned 425 result carried `replayed:true`. However the same 425 result was subsequently posted into ChatGPT again after an already-visible 425 result turn. This is a browser-delivery anti-spam incident, not duplicate Windows execution.

Source inspection found that visible-result recognition depended solely on `USER_SELECTOR`; if current ChatGPT user-turn wrappers are not matched, `waitForDeliveryConfirmation()` cannot observe the exact result and its bounded retry loop can post the saved result again. Commit `9a3cd5b00348d219ece22a877d510124be4b64ff` adds a result-only current-conversation-wrapper fallback, explicitly rejects assistant-role wrappers and the composer, and does **not** broaden the assistant-only action execution trust boundary. Commit `50ac686b141ede52cff8ff8c76d06d0fdbc5b99f` adds the regression assertion.

Do not call the GitHub approval auto-click live-proven until this delivery fix is activated and the approval-v3 telemetry is independently observed.


### PCE7.426 approval-v3 runtime activation proof — 2026-10-06T0539Z

Delayed PCE7.426 readback proved the new approval runtime did activate after the PCE7.425 refresh. Browser telemetry contained fresh `content_script_started` events at 05:36:15Z and 05:36:20Z with runtime `v11-scroll-v5-delivery-v11-collapse-recovery-approval-v3-uierror-v1`.

`autoapproved_count` was zero because no qualifying GitHub approval card event occurred in the post-refresh window. Therefore source/runtime activation is proven, but an actual auto-click is **not yet live-proven**. The next proof must intentionally encounter the exact GitHub approval surface (or an equivalent naturally occurring one) and require `chatgpt_tool_approval_autoapproved` telemetry plus disappearance/continuation of the approval surface.

PCE7.427 was already emitted to stage/activate the result-turn de-duplication fix after the duplicate PCE7.425 delivery incident; do not stack a newer Windows action ahead of that existing obligation.


#### Corroboration: PCE7.426 also duplicated — 2026-10-06T0541Z

The exact PCE7.426 result was posted visibly a second time after its first visible delivery. This confirms the currently loaded `delivery-v11` result-recognition failure is systematic across ordinary post-refresh relay results, not unique to PCE7.425. Backend execution remains exact-once; the defect is repeated browser delivery of an already-saved result.

PCE7.427, already present in the managed conversation, is the next outstanding operation and contains the staged activation of the `GPT_WINDOWS_RESULT_TURN_WRAPPER_FALLBACK_V1` fix. Do not introduce a higher operation ID ahead of it while the old runtime's bounded 426 delivery loop is still draining.


### PCE7.427 interrupted restart + Director rescue — 2026-10-06T0542Z

After repeated visible-result duplication from the loaded delivery-v11 runtime, the Director intervened manually to rescue the workflow. This is an autonomy incident under the human-intervention policy. Exact operator action is not yet established and must not be invented; record it as **operator detail pending** until direct evidence or Director clarification identifies what was changed/closed/restarted.

Immediately afterward, `PCENG-PCE7.427-stage-dedupe-fix-and-reactivate` surfaced as `INTERRUPTED_RESTART`. Backend evidence is explicit:

- started 2026-10-06T05:42:10Z;
- terminalized 2026-10-06T05:42:15Z;
- saved result unavailable;
- exact-once boundary refused re-execution;
- stderr: `The command was previously processed, but its saved result is unavailable; it was not executed again.`

Do not call PCE7.427 successful or failed-at-a-specific-script-line. Its command may have partially progressed before process interruption. Next operation must be read-only forensic reconciliation of live/source hashes, runtime marker, backend state and supervisor/watchdog logs before any new mutation.


### Director rescue details + self-healing observation — 2026-10-06T0609Z

The Director supplied the exact manual rescue sequence for the 425/426 delivery-spam incident:

1. reloaded the Firefox relay extension/integration;
2. set it disabled (Firefox equivalent);
3. observed the programmed recovery machinery turn the integration back on again without further manual enablement;
4. then removed the relay extension entirely to stop the runaway browser-delivery behavior.

This closes the previously pending operator-detail field. It is also valuable positive field evidence: the disable/recovery path restored the integration as designed. Preserve that recovery behavior while fixing result de-duplication.

Screenshot evidence at 06:09:39Z then showed:

- HUD headline: `DELIVERING`;
- backend: `Relay ONLINE • ARMED • pending 0`;
- browser: `Firefox IDLE • action_result • 1639s`;
- lifecycle: `DELIVERING • ChatGPT send control became ready • 1639s`;
- packet: `PCENG-PCE7.427-stage-dedupe-fix-and-reactivate`.

The `DELIVERING` headline is therefore stale-state evidence, not proof that delivery is currently active: both supporting browser/lifecycle events are approximately 27 minutes old. This independently confirms the HUD lifecycle-aging defect already on the roadmap: nonterminal phases such as DELIVERING/STARTING must age into an explicit stale/stalled state instead of persisting indefinitely.

At this checkpoint the backend is visibly online/armed, but browser integration cannot be inferred alive after the Director removed the extension merely from the stale HUD phase. Next guidance must require a fresh near-zero-age browser/content-script event before resuming relay mutations.


### Pre-spam rollback boundary + intentional operator stop/start — 2026-10-06T0618Z

Preserve the first practically useful pre-spam live browser state before installing further repairs. Exact rollback evidence already exists locally:

- `Client\Relay\rollback\PCE7.422-20261006T053422Z\content.js`
- pre-spam live content SHA-256 recorded by PCE7.422: `26ce6b9bcd63ef5acb2043bef0216eba5d42623aeaf733c98df264e183f83ed5`
- PCE7.407 rollback directory remains `Client\Relay\rollback\PCE7.407-20261006T034645Z` for the earlier paired extension files.

Do not delete these rollback snapshots while the delivery-v12 repair is being validated.

Operator-control architecture is now explicit: redundancy keeps the relay alive unless the human intentionally sets the existing `.relay-paused` interlock. HUD commit `cd76768d1f6e0388389e5c627fc6035251a4a7f5` adds STOP/START controls; `START-RELAY.bat` and `STOP-RELAY.bat` were repaired as real multi-line CMD launchers in `e183beb9f163e5431c0e47d06ff9552b1f770533` and `1c149a152d61aceb06515a4deb004dd700123423`. Watchdog source corruption from the earlier string-replacement edit was repaired in `8d645117e044fbf41b3d0e0a959936e35b96207d`; regression coverage is in `b822d2e89e989bb08823be79573c68c9c44714e1`.

Intentional STOP must win over every watchdog/recovery plane. START clears the interlock and returns ownership to supervision.


### Repaired checkout targeted validation — 2026-10-06T0633Z

With the live relay intentionally paused via `.relay-paused`, the Director fast-forwarded the consumer checkout to `5b2434fc6f9cbd75b4fa90f346c10a6332541354` and ran:

`python -m unittest discover -s tests -p test_hud.py -q`

Result: **17 tests, OK**.

Two preceding runs exposed only a newly-added assertion escaping mistake around the watchdog mutex string; the watchdog implementation itself was not changed for those failures. The assertion was simplified to count the stable mutex name and independently rechecked against source before the final passing run.

Do not stage/start live yet solely from this targeted gate; run the complete Windows-relay unit suite first, then create a fresh live rollback snapshot before copying repaired files.


### Repaired checkout full-suite validation — 2026-10-06T0635Z

While the live relay remained intentionally paused, the Director ran the complete `windows-relay/tests` suite from the repaired checkout using the live relay Python runtime.

Result: **265 tests in 4.050 s, OK**.

The two printed `ATOMIC_REPLACE_RETRY` lines were expected simulated transient-sharing-lock test behavior; the suite was green. This clears the source test gate for a paused, rollback-protected live staging of only the repaired content/HUD/watchdog/operator-launcher files. Starting/resuming the relay remains a separate acceptance step.


### Paused staging proof + old HUD process distinction — 2026-10-06T0637Z

