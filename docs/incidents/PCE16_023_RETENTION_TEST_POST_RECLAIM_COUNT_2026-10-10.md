# PCE16.023 isolated retention fixture assertion failure — 2026-10-10

**Scope:** monag144/GPT-Windows-Relay/main; PCE16.023 only. **Status: OPEN TEST-HARNESS DEFECT, NO LIVE CLIENT MUTATION.**

## Native evidence
`PCE16.023-isolated-processed-id-eviction-replay-test` returned `COMMAND_FAILED`, exit code 2, at 2026-10-10 23:20:40 UTC. The isolated fixture recorded true for `frozen_stage_manifest`, `v3_manifest`, `v3_backend_sha256`, `v3_all_nine_components`, `original_mark_unmodified`, `atomic_claim_available`, `NOT_SUBMITTED_initial_500`, `NOT_SUBMITTED_new_claim`, `ALREADY_SUBMITTED_initial_500`, `ALREADY_SUBMITTED_new_claim`, `ready_action_retained`; failed `submitted_action_evicted` with `AssertionError`. Because exception happened before `fixture_results` was assigned, do not claim this run's full submitted-case result.

## Source-based diagnosis (hypothesis to independently verify)
The fixture's submitted case first calls `state.mark(new, ...)`, which applies the original `mark` pruning logic when records exceed 500. With old delivery `SUBMITTED`, the first old ID can be removed and count would become 500. **But the fixture then calls `state.claim_or_lookup(old)` before recording `processed_after_mark`.** If pruning made the old ID unrecognized, this call writes a new `INFLIGHT` reservation and brings processed count back to 501. The test asserts `old_reclaim_permitted` *and* `processed_after_mark == 500`, internally inconsistent under successful reclaim. The failed assertion does not disprove eviction/reclaim. It also does not establish actual live duplicate command execution.

## Required correction
- Treat ordinal .023 as consumed. Do not reissue same action ID.
- In a new isolated test, measure `count_immediately_after_mark`, `old_present_immediately_after_mark`, `count_after_replay_attempt`, `reclaim_permitted` separately. Keep pending vs submitted cases and clearly distinguish reported evidence from inference.
- **Move straight into a guarded offline patch** if the direct old-source behavior confirms the risk: preserve all processed-ID decisions without unsafe 500-entry pruning, and guard against historical IDs retained solely in outbound delivery metadata. Consider data growth/rollout compatibility; no live Client patch/deploy without staged negative tests and approval.
- Never clear existing Client processed ledger, outbound deliveries, queues, or runtime credentials. Test with synthetic IDs and temporary state only. Preserve original candidate and frozen snapshots; keep rollback.

**Governance:** No PCE ordinal reused; no script/real shell execution, live state read or Client modification reported by the native action. This incident is a test correctness issue and a substantive exact-once design risk, not an accepted release.
