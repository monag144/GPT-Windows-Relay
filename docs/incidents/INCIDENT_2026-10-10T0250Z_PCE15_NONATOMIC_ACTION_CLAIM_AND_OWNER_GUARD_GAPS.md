# PCE15 — Nonatomic operation reservation and browser conversation guard gaps — 2026-10-10T0250Z

## Severity, discovery and impact boundary

**SEVERITY: HIGH — demonstrated reproducible source-level exact-once safety bug; live exploitation/side effects NOT observed. Release BLOCKED.** Detected in diagnostic PCE15.040–.044 during strict release grading. The Python backend's process(packet,state) performs state.lookup(action.id) and then later calls state.reserve(action) without a shared atomic check/claim transaction; the reserve function does not refuse an existing same-ID reservation and overwrites the processed entry. This can permit two concurrent requests with identical IDs (identical OR different payloads) to both reach execution if both observe absence before either reserves. Existence of multithreaded HTTP server establishes plausible interleaving; no real live race, duplicate shell command or duplicate ChatGPT send was witnessed. The running backend module bytes have not been independently attested, although the process argv referenced Client source.

Three source cohorts examined: verified GitHub main, local development HEAD and deployed Client file. Their normalized backend SHA256 are respectively:
- main be9a326f3ce8d48ce061f53d53cf47f01b0e916556f382b6161270268497638b
- development 6a4590ddcfcb1742a462591ad7ec168723f2bd173f2323868c2b550d3cbb7957
- Client c4c1c8b4b2f87a99c9f04328e016770e8ea8f8399f973c517f1da67f2358e4d4

This incident is distinct from unresolved release packaging and Firefox loaded extension identity; no threat actor, compromised session, malicious package, or user harm is inferred.

## Reproduction and test integrity

PCE15.042: actual GitHub main AST-extracted Action/extract/State.lookup/State.reserve/State._mutate_and_save/process ran with in-memory mock save and execute. Forced simultaneous read-before-reservation resulted in TWO synthetic execution calls for one ID with equal or differing payload; sequential same-payload duplicates suppressed and changed-payload collision rejected. Development and Client subprocesses failed NameError because isolated test harness omitted engineering_governance_check: explicitly NOT an observed development or Client result.

PCE15.043: corrected isolated child provided a mock governance approval (production preflight never bypassed). All three source cohorts demonstrated two synthetic executions for same ID under forced initial-lookup overlap, both same and different payloads; sequential duplicate/collision handling remained correct. Governance mocks were each called twice for dev/Client, confirming governance alone did not serialize reservation. No real command executed or persistent state touched.

PCE15.044: original State.reserve invoked serially with same ID and different payload **overwrote** the first hash. Prototype atomic_claim performed check plus State._mutate_and_save under one lock: 16-thread same payload -> one CLAIMED, 15 DUPLICATE_INFLIGHT; alternating payloads -> one CLAIMED, 7 duplicates, 8 collisions. Simulated persistence OSError rolled back in-memory state, then retry CLAIMED. Tested across main, development and Client. **This is a mock/in-memory design proof, NOT a committed or deployed patch.** Does not prove cross-process durability, safe restart after uncertain execution, atomic writes outside mock, crash windows, or browser result exactly-once.

## Related Firefox content/worker safety findings

PCE15.040 static and PCE15.041 isolated Node.js execution showed all three contemporary service_worker.js variants:
1. ownership guard runs before cursor guard and callAction, but for an already-owned matching conversation the branch allows a request without rechecking whether sender tab is active, sender tab id equals saved owner tab id, or packet session equals saved owner session;
2. conversation identity prefers message-provided conversation_key/conversation_href ahead of sender.tab.url; a mocked mismatch was allowed for the same stored conversation;
3. operationSeriesPosition only recognizes OP### style tokens; current PCE15.### identifiers parse as null and late:false, so frontend late-operation protection does not cover these IDs;
4. equal parsed ordinal is not rejected by cursor (strict less-than), relying on backend duplication defenses.

The historical Client XPI lacks the owner/cursor helpers, but whether it is actually loaded by Firefox remains UNKNOWN. These are source-level and mock tests, not confirmed malicious cross-tab delivery or runtime failures.

## Required remediation and verification (NOT YET AUTHORIZED)

Priority P0: after explicit change authorization in reviewed development, implement atomic reservation of ID plus payload hash in a single lock/transaction *after* governance policy and operator STOP; prevent duplicate execute on same ID even when two HTTP requests arrive simultaneously; distinguish identical payload replay, collision, inflight, crash-restart uncertainty and persisted saved-result semantics. Prevent raw State.reserve overwriting prior records or make reservation private and guarded. Avoid treating an idempotent response replay as a command rerun. Test with synchronized same-ID same/different payload, 16+ threads and server restarts, realistic persistence failures, multi-process contention if supported, inconsistent saved result, and outbound delivery recovery.

Priority P0 browser: bind identity to authoritative port.sender.tab.url and tab.id, reject conflict with message key, recheck active/owner tab/session in same-conversation branch, define deliberate signed owner transfer, fail closed on malformed or unknown cursor IDs, recognize PCE15 identifiers, define equal ordinal replay behavior. Verify content-worker message provenance. All fixes must preserve real operator STOP/ARM behavior and avoid duplicate ChatGPT submission.

Priority P1: reconcile deployed source, build deterministic exactly-five-member extension package excluding 10 historical backups; verify Mozilla signature and real loaded extension origin; compare signed/loaded code SHA to reviewed source. Build test-before-promote atomic deploy with rollback and live G16/G26/G27 evidence. No GitHub Actions runs while credits exhausted; run isolated/local tests only.

## Governance preservation, exact-once incident response

No production fix, release change, Client deploy, Firefox modification, actual user send or backend replay has been made. Operations PCE15.040–.044 all returned OK/0; PCE15.042 dev/Client isolated subprocesses failed as described. Protected PCE12 duplicate hash 3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab; Client XPI hash 18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8. Windows development tracked checkout unchanged, 29 previous untracked docs. No rollback required/performed; do not clean/reset/stash. Incident status: **OPEN / reproducible source-level safety blocker; mitigation prototyped in isolation only**.

Overall grade remains **F / RELEASE BLOCKED — 11/28 qualifying gates, G16 unverified, G26 0/60 independent live sends, G27 0/2 endurance tests**. Full operation audit: docs/audits/AUDIT_2026-10-10T0250Z_PCE15_040_044_CHECKPOINT.md. Next numbered PCE15.045 requires GitHub-first audit [040–044], merge/readback, docs-only sync, and installed preflight.
