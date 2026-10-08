# Archived source fragment 2/2 — 2026-10-08T0752Z

**Recovery status:** complete. The machine is back in the known recovered pre-cutover state. The incident remains open solely for the failed v17 activation/proof path and the need for a bounded, invisible end-user cutover design.


## Forensic update — OP047 through OP050

OP047 confirmed the repository's intended Firefox layout: `extension/manifest.json` is the temporary `about:debugging` development path, while `extension-persistent` is reserved for the signed/force-installed production path. Therefore the temporary Firefox card pointing at `Client/Relay/extension/` is expected and should not be replaced with the persistent tree during development cutover.

OP049 ruled out the temporary worker's generated `extension/config.js` as the activation failure. The live config exists, targets port 8766, identifies Firefox, and its redacted token hash exactly matches the main 8766 bridge token. The config file is intentionally ignored by Git and is a local runtime secret/config artifact.

OP050 identified an uncovered Firefox-manifest regression in canonical source. The recovered working temporary Firefox manifest contains both:

- `background.scripts = ["service_worker.js"]`
- `background.service_worker = "service_worker.js"`

Canonical `extension/manifest.json`, imported in the sanitized Windows-repository snapshot, contains only `background.service_worker`. The canonical persistent Firefox manifest still contains both declarations. Existing tests exercise worker source contracts but do not assert the temporary Firefox manifest background declaration.

This is now the leading explanation for OP042's activation symptom: after the temporary add-on was reloaded from canonical source, Firefox could load the content script but the background bridge contract was no longer guaranteed to start in the same way as the recovered working Firefox manifest. Without a functioning background port, `content_script_started` telemetry cannot reach the 8766 backend, causing the helper's v17 proof gate to time out.

Before another live cutover, canonical source must restore the Firefox-compatible temporary background declaration and add regression coverage. The helper also still requires hard process-tree timeout/finalization guarantees so a failed rollback cannot remain user-visible for minutes.


## OP057 bounded-cutover result and corrected operator-impact finding

The second corrected cutover attempt (OP057) did **not** hang indefinitely. External forensic review in OP059 showed the canonical helper completed its failure, exact rollback, wake attempt, final report, and scheduled-task deletion in roughly 56 seconds after helper start. The OP056 rollback snapshot verified exact and the main relay returned healthy.

The activation still failed: after the canonical temporary add-on reload and ChatGPT refresh, no fresh v17/owner-v1 `content_script_started` event was observed before the cutover budget expired. OP060 narrowed the event timeline further. The first post-baseline content-port/startup telemetry appears only after rollback, and reports the recovered v16 runtime. Thus the canonical temporary extension produced no backend-visible startup telemetry during the canonical activation window.

A separate operator-notification defect was confirmed. The helper logged `failure_wake ok=true`, but `wake()` currently ignores the Firefox adapter process return code/output. Therefore the helper can claim a successful user-visible wake even when nothing is injected into ChatGPT. This explains why the operator reasonably observed an apparent >10 minute stall despite the helper itself having finalized in under a minute. User-visible completion must be verified, not inferred from a best-effort call.

Required follow-up before another full cutover:

- localize why the canonical temporary extension produces no background-port/startup telemetry during its activation window;
- make `wake()` fail on nonzero adapter status and add regression coverage;
- add a genuinely external operator-visible completion mechanism or independently verified ChatGPT injection result;
- keep the bounded rollback design, which did work in OP057, but do not label a cutover user-visible-successful unless the completion signal is actually observed.
