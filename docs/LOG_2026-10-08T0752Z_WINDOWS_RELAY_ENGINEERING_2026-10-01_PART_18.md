# Archived source fragment 18/23 — 2026-10-08T0752Z

- New invariant: keep chat relay packets compact; do not transport whole profiles/databases/giant scripts inline. Use bounded multi-step file writes or existing local/source files.
- Backend execution was not proven to have started; do not misclassify this as a Windows relay backend failure.

## 2026-10-03 — Human-intervention incident: relay packet emitted through commentary surface
- Packet PCENG4-JOBAUTO-037-profile-state-audit was compact and visually bare-fenced but collapsed/no usable result appeared.
- Difference from known-good proof: 037 was emitted in commentary/update output rather than the final assistant response.
- User had to report the failure.
- New hard rule: relay sandwiches are final-response-only. Never emit them in commentary/progress/status messages or split commentary/final surfaces.


## 2026-10-03 — Job-application profile persistence and Git divergence recovery
- Canonical local applicant profile validated with 18 employment records extending to 2012.
- Current Post Falls application reached the pre-signature gate with confirmed non-signature fields staged and audited.
- Local commit `d6f1539` was created successfully, but its push was rejected because `development/runtime-control` had newer remote commits from direct GitHub incident logging.
- This was a branch-divergence/push ordering issue, not loss of the local profile or application state.
- The reusable defaults file was then created directly on the remote branch through the GitHub connector.
- Signature/agreement/submit remain intentionally untouched pending explicit authorization.

## 2026-10-03 — Job-application profile persistence and Git PATH incident
- Canonical local profile validated with 18 employment records extending to 2012.
- Post Falls application reached the pre-signature gate with confirmed non-signature fields staged.
- Action 046 failed because native Python could not resolve `git` from PATH. No repository write occurred from that failed action.
- Recovery uses the established explicit Git path: `C:\Program Files\Git\cmd\git.exe`.
- Signature/agreement/submit remain intentionally untouched pending explicit authorization.


## Reliability-regression evidence, GitHub approval-card UX, and PCE7 boundary — 2026-10-06T0300Z

### Evidence carried forward
- The 2026-10-04 night-agent handoff records the r25 consumer baseline as: normal live E2E PASS; live `Worked for X` collapse recovery PASS; relay suite 245/245 with zero exclusions; consumer suite 47/47; consumer Chrome connected at preflight; branch clean and matching origin.
- At the 2026-10-06T0257Z comparison checkpoint, GitHub comparison from audited stable `consumer/one-click-go` SHA `d5b9db7ad785b5cae8dc3b64219303b9fcfa634a` to r29 SHA `3d8ef23ab9f281ef8961aaf016f94c34f9e2cce9` reported r29 ahead by exactly 200 commits and behind by 0. This is a comparison boundary, not proof that any particular commit caused the regression.
- The Director reports a material practical reliability regression: an earlier relay era could operate autonomously for long periods and roughly the operation-182-to-200 era behaved materially better, while the present live path often struggles to progress through more than about two operations without intervention. Treat this as Director-observed field evidence requiring measured reproduction; do not rewrite it as a repository-proven duration claim.
- The 2026-10-06T0246Z Agent 6->7 handoff remains authoritative historical evidence for its boundary: A6.400 was discovered but never executed. Its documented open blockers remain on the release board.

### Engineering priority amendment
- Restore sustained relay forward progress before expanding unrelated feature surface. This does not authorize deleting newer recovery/safety work.
- Use r25 and the better historical operation range as differential evidence across scanner ownership, settlement/reacquisition, operation locking, delivery/finalization, browser lifecycle and recovery transitions.
- First reliability repair target is `DISCOVERED -> execution`: bounded transition-specific deadline, screenshot/evidence before repair mutation where required, exact-once backend state check before replay, and recovery without waiting for the approximately five-minute dead-man.
- Result visibility and ChatGPT turn finalization are separate states. Finalization recovery must never re-execute the completed Windows action.
- Preserve immediate remount reacquisition, approximately 15-second forced broad reinspection, approximately five-minute dead-man, collapse/folded recovery, delayed/out-of-order protection, backend dedupe, durable recovery ownership and honest HUD state.
- Add measured sustained-operation/soak acceptance. One or two consecutive successful packets are insufficient evidence that autonomy is restored.
- Do not blindly revert r29 to r25; preserve or equivalently replace the newer exact-once, approval, screenshot, out-of-band recovery and lifecycle safeguards.

### GitHub approval-card screenshot finding
- Director screenshot at 2026-10-06T0259Z positively identifies the recurring native ChatGPT GitHub approval surface at the bottom of the conversation: `Allow ChatGPT to use GitHub?` with `Always allow`, `Deny`, and `Allow once`.
- Low-priority requested UX: when the managed conversation is already at the bottom and this exact positively identified GitHub approval surface appears under the Director's pre-authorized policy, automatically invoke the configured GitHub approval choice so the run is not stranded.
- This must remain narrow: do not blindly click unknown providers, differently worded security surfaces, or ambiguous controls. Provider/text/control identity plus bottom-of-conversation state are prerequisites.
- The screenshot also explains the immediately preceding GitHub documentation-write interruption: the connector write was waiting on this approval surface rather than proving a repository failure.

### PCE7 boundary
- Director superseded the proposed Agent-7 `A7.1` working numbering for this conversation. Engineering proceeds as `PCE7.400` through `PCE7.499`.
- `PCE7.500` is the mandatory timestamped handoff/rotation boundary and should ideally exercise automatic fresh-chat/next-agent startup.
- Historical failed `A6.400` remains a separate incident; do not renumber it or count it as a successful rotation.
- If the primary PCE7.500 rotation fails, independent/out-of-band fallback must preserve and deliver the handoff rather than leave it stranded at `DISCOVERED`.


## PCE7 stale operation owner after completed result delivery — 2026-10-06T0324Z

PCE7.401/PCE7.403/PCE7.404 confirmed the first concrete forward-progress root defect in the present relay.

- A6.399ay executed once and finished `COMMAND_FAILED` at 02:30:31Z; its saved backend result exists.
- Browser delivery then succeeded: send clicked/confirmed and `relay_result_delivery_complete` emitted at 02:32:27Z.
- At 02:32:51Z a leftover/reappearing A6.399ay relay-result draft was detected. Draft recovery reacquired A6.399ay as `activeRelayOperationId`, attempted another send, and at 02:34:22Z deferred with `Send button not ready within 90000ms`.
- That recovery failure retained the global owner. Historical A6.400 subsequently accumulated 78 discoveries, 78 queue events, and 78 `relay_action_deferred_for_active_operation` events behind A6.399ay, while never reaching backend reservation or execution.
- PCE7.403 at 03:22:40Z still proved A6.400 had no processed record/result. It also proved PCE7.402 never executed.
- The earlier hypothesis that A6.400 late-executed and caused the 03:09Z generic-ChatGPT navigation is therefore disproved. The session-escape/manual-return/manual-rename incident remains real with cause still open.

Source finding:
- `recoverExistingRelayDraft()` can reacquire ownership for a stale draft after normal delivery and does not first reject a packet already recorded as delivered/attempted.
- Its deferred/failure path intentionally retains ownership, while the no-draft path does not reconcile a stale owner against exact visible result evidence.
- `drainDeferredActions()` refuses to drain with any active owner, turning this stale draft into a global deadlock.
- `waitForDeliveryConfirmation()` also treats generation-start or stable composer-clear as semantic delivery confirmation. That contradicts F-005 / Operational Rule 12, which require the matching live `[GPT_WINDOWS_RESULT]` user turn.

Repair contract:
1. matching user-result-turn evidence is the only delivery-complete signal; generation-start/composer-clear are progress telemetry only;
