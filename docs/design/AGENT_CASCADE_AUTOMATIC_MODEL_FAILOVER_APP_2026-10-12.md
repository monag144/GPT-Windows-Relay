# Agent Cascade — automatic model failover app — 2026-10-12

**Status:** User-approved concept design; not implemented, installed, tested, or approved for access to real credentials.  
**Identity:** Standalone, local-first Windows AI-agent orchestration application. It is **not** a feature of the Windows Relay, OpenCode, the D&D bot, or the retired conversation-switching mechanisms.  
**Repository placement:** Design-only incubation under `monag144/GPT-Windows-Relay/docs/design` because it is the available Windows AI-infrastructure repository and no dedicated Agent Cascade repository currently exists in the connected GitHub account. This placement grants no Relay runtime authority and introduces no executable changes. When a separate Agent Cascade repository is created, migrate this design with provenance intact.  
**Operator decision:** Design approved, then requested public GitHub competitor/security review **before** repository publication; this document records that review. All research findings are preliminary unless otherwise stated.

## 1. Mission and user requirements

Create a Windows desktop app above/alongside OpenCode that automatically selects an available, **qualified**, preferably zero-cost AI coding model, detects when its rate/usage limits are exhausted, and resumes unfinished development with the next eligible provider/model. Minimize human intervention while preserving mission scope, evidence, filesystem integrity, provider rules, and API credential safety.

The operator especially values **genuinely free or sustainable hosted API access with no low daily token cutoff**. A model catalog entry, the string `free`, or $0 marginal pricing is **not** proof of unlimited service. Route conservatively and handle real quota results. The existing candidate families include Z.AI GLM, NVIDIA Nemotron, OpenCode-hosted MiMo/Nemotron, and eventually local Ollama/LM Studio. Do not hard-code models or free status as perpetual truths.

**Non-goals for v0.1:** no Relay/backend repair, no D&D bot deployment, no automatic ChatGPT conversation switching, no bypass of provider quotas, no multi-account evasion of restrictions, and no claim that running third-party models keeps prompt/source code private from those approved inference providers.

## 2. Functional components

1. **Model registry:** exact `provider/model` identifiers, capabilities (tools, context, vision, streaming), provenance, operator approval, permission tier, model/version, costs, free-tier and usage policy, benchmark qualification, and enabled status.
2. **Provider adapters:** support official OpenCode CLI/server/SDK capabilities if validated against installed version; provider-native API adapters may be developed later. Model names are gateway-specific; identical-sounding models on different hosts must have distinct identities and capacity status.
3. **Availability monitor:** classify `429`, `Retry-After`, documented quota reset, exhausted credit, `401/403`, `404` model removal, network failures, `5xx`, context overflow, and unknown errors. Avoid frequent metered probes. Quota and per-minute throttling are different states; absence of a documented daily limit is not unlimited capacity.
4. **Eligibility/routing engine:** hard-gate **operator authorization -> workspace security -> provider privacy policy -> zero-cost policy -> benchmark qualification -> model availability**. Only then rank candidates on task fit, reliability, quota health, latency, and expected cost. Never treat a weighted score as an override of hard failures.
5. **Checkpoint manager:** durable SQLite record of user objective, prohibitions, authorized paths, Git branch/HEAD, operation IDs, tool receipts, write evidence, test outcomes, model handoffs, and unfinished milestones. Store metadata and necessary **redacted** summaries; do not store API keys, raw secret material, or sensitive prompts by default.
6. **Execution supervisor:** exactly one writable owner per workspace/task at a time. Switch providers at verified safe boundaries; if a request may have executed tools or writes before an interruption, enter `AMBIGUOUS` and reconcile filesystem/process/Git evidence *read-only* before any continuation. Never unconditionally re-send the last model instruction after an uncertain side effect.
7. **Dashboard:** Windows GUI showing provider/model, task status, qualified alternatives, cooldown, known/unknown quota, last checkpoint, handoff reason, evidence, and optional cost. Controls: Start, Pause, Stop, Resume, Manual Override, Disable Provider.
8. **Recovery scheduler:** prefer authorized distinct provider gateways when a model becomes unavailable, maintain bounded exponential backoff/circuit breakers, and re-enable a cooled-down provider at the next safe boundary—not mid-write or mid-stream.

### State machine

`CREATED -> PREFLIGHT -> RUNNING -> CHECKPOINTING -> (RUNNING | SWITCH_PENDING | BLOCKED | COMPLETED)`

`SWITCH_PENDING -> QUIESCE -> VERIFY_EFFECTS -> (REPLAY_SAFE | MANUAL_REVIEW | NEXT_MODEL)`

`FAILED / TIMED_OUT / UNCERTAIN` never equates to `NOT_EXECUTED`. Persist state before dispatch, record request ID, provider attempt ID, model identity, tool/output boundary, receipt and local effect evidence; on restart reconcile before advancing.

### Example

- GLM completes three of five D&D campaign-creation milestones using an isolated disposable development branch.
- GLM reports confirmed quota exhaustion; the supervisor stops sending new work to GLM, stores the verified checkpoint and current Git/diff/test evidence.
- Nemotron is eligible for remaining tasks under the same exact authorization and scope. It receives the original mission plus **verified** progress and unresolved steps, not a fictional continuation of GLM's internal reasoning.
- If Nemotron times out during a file-writing step, the supervisor does **not** blindly prompt MiMo to repeat the step. It first establishes the authoritative file state and whether the tool action completed, then resumes safely.
- Completion requires the operator's definition of done and independent tests, not merely a successful model handoff.

## 3. Credential and data security: non-negotiable boundaries

### Threat model

The most important assets are upstream API keys, OAuth/refresh tokens, SSH/Git credentials, Windows user files, source code, campaign/user databases, and confidential prompt/tool output. Attack or accident paths include an untrusted OpenCode plugin, malicious npm/PyPI binary update, dependency hook, compromised release, improperly configured local gateway, exposed listener, log/trace export, insecure config backups, arbitrary custom provider URLs, dependency auto-update, and accidental failover to a more permissive/paid model.

**Crucial limitation:** Any program with the operator's full Windows user privileges might read files and credentials accessible to that user, even if Agent Cascade uses encrypted at-rest key storage. DPAPI/Windows Credential Manager protects at rest and narrows routine exposure; it does not defend against arbitrary malicious code already executing with equal privileges. Likewise OpenCode already stores/uses its own provider credentials; Agent Cascade cannot retroactively protect them if a loaded plugin or compromised OpenCode process can read them.

### Design requirements

- **No credential import by default.** Prefer an OS-protected credential broker using Windows Credential Manager/DPAPI with user-specific ACLs and minimal scope. Only the outbound provider adapter handles decrypted material for the authorized target. Never write keys into project repositories, SQLite, plain config files, logs, prompts, stack traces, diagnostics, process arguments, or child-process environment.
- **Network egress allowlist:** explicit provider host + HTTPS/TLS certificate verification; reject arbitrary redirect forwarding of Authorization headers, mixed-content HTTP, unknown base URLs, and unauthorized proxy endpoints. DNS/TLS and domain changes require operator review. Remote gateways necessarily receive the *user-authorized prompt/request*, but must **never** receive another provider's API credential.
- **Strict listener boundary:** use a Windows named pipe or other authenticated local IPC if practical; any HTTP compatibility endpoint must bind `127.0.0.1` only, use a per-install unpredictable auth token and robust Origin/CSRF checks, and never expose administrative methods unauthenticated. No automatic firewall opening or remote bind.
- **Metadata-only logs by default:** event class, model ID, timestamp, opaque request correlation ID, retries/cooldown and redacted response status. No body, raw Authorization headers, provider error text containing embedded credentials, tool arguments, prompt segments, code diffs, user files, transcripts or secret-bearing URLs. Sensitive diagnostic capture requires an explicit temporary opt-in and sanitization.
- **Zero-cost mode hard gate:** never silently route to a billable endpoint, prepaid credit, paid fallback, or unapproved provider. Cost changes invalidate an eligibility snapshot until verified again.
- **No plugin with omnipotent credentials by default:** if an OpenCode event adapter is necessary, prefer a tiny audited, pinned, narrowly scoped local component that sees event metadata but not API keys or complete source/prompt bodies. If that isolation is not technically enforceable in OpenCode's plugin environment, document that limitation and avoid claiming it.
- **Supply-chain controls:** exact dependency/installer versions and checksums, inspect package installation scripts and transitive dependencies, reproducible offline tests, compare source release to published package, code signing if possible, disable automatic unreviewed updates, scan dependencies, secret scanning and network-egress testing before adding real keys. No remote `curl|bash` installations on a credential-bearing development machine.
- **Scope/permission gates:** no new model can gain more filesystem, network, repo or destructive-action permissions after failover. Unsafe actions (push, merge, deploy, deletion, key rotation, external messaging) require explicit operator authorization and affirmative receipts.
- **Privacy constraints:** credential protection is separate from source-code confidentiality. If any approved model provider can receive source text, the system must show and honor that policy. Local inference can eliminate remote inference egress but not host-side malware risk.

## 4. GitHub alternatives inspected — preliminary security assessment (2026-10-12 Pacific)

These repositories are legitimate research leads, **not security-cleared products**. Review comprised GitHub README/security policies, selected code files, dependency manifests, and public incidents. No local execution, full dependency audit, packet capture, binary verification, or credential-bearing testing was performed. **No finding of current malicious behavior is asserted for the small plugins.** Every in-process OpenCode plugin adds a trusted-code surface and has potential to read data available to the hosting process.

| Project | What already matches Agent Cascade | Observed credential / data exposure surface | Decision |
|---|---|---|---|
| [peva3/opencode-fallback](https://github.com/peva3/opencode-fallback) | Automatic OpenCode fallback on rate limit, recover from disconnects, optional auto-continue | Source `src/plugin.ts` calls `session.abort`, `session.revert`, then replays the last prompt or a continuation containing partial assistant output. This can repeat tool actions after a partially successful write. `src/log.ts` writes arbitrary structured event/error details to a plaintext local log when enabled; error text could hold sensitive data. No evidence of an intentional exfiltration endpoint in inspected files, but **not a full audit**. | **Do not install with production keys/workspace**; reference its event integration and recovery approach only. |
| [linuxdynasty/opencode-quota-failover](https://github.com/linuxdynasty/opencode-quota-failover) | Differentiate hard quota exhaustion from transient 429 and switch provider in the same session | Source `src/failover.ts` replays message parts through OpenCode session APIs; stores and logs failover diagnostics. Replaying the user request is unsafe if earlier tool side effects are not reconciled. Plugin runs in OpenCode trust context. No complete security audit or published artifact attestation. | **Read source as a prototype**, especially error classification; not authorized with real keys. |
| [Sharper-Flow/opencode-model-routing](https://github.com/Sharper-Flow/opencode-model-routing) | Per-agent primary/fallback chains, cooldown tracking, preemptive skips, time-to-first-token detection | `plugin/src/plugin-internal.ts` has direct session access, config hooks, abort/revert/prompt interactions; docs describe cooldown files and bounded fallback. In-process plugin remains privileged relative to user files and session data. It is a model-routing solution, **not proof of durable, exact-once, file-safe task continuation**. | **Strong feature reference**, hold off installing pending full release/dependency/egress review. |
| [Apale7/opencode-provider-switch](https://github.com/Apale7/opencode-provider-switch) (`ocswitch`) | Local OpenCode-compatible proxy, upstream key pools, failover before first byte, circuit breaker | The README explicitly states upstream credentials reside in local `ocswitch` config, server-admin token is **plaintext** in `admin.api_key`, and network traces/request logs use SQLite. Admin/browser access plus non-loopback binding would expand risk. Documentation samples put `--api-key` values in shell arguments; don't do that. | **Reject for our credential-bearing deployment as shipped**. Useful architecture inspiration only. |
| [farion1231/cc-switch](https://github.com/farion1231/cc-switch) | Cross-platform model/provider config manager, local HTTP routing and failover for some CLIs | Project `SECURITY.md` acknowledges no user-level privilege separation and possible non-loopback proxy listening. Manual states OpenCode is a **coexist** app and does not use its failover queue. Direct-mode provider keys are written into tool config files. Local-first privacy policy is a statement, not a formal source/package audit. | **Does not deliver OpenCode failover we require**, so do not entrust keys solely for this goal. |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | Mature cross-provider proxy/router, multi-model fallback, budgets | **Confirmed historical credential-stealing supply-chain attack**: official vendor advisory says PyPI `litellm==1.82.7` and `1.82.8` were backdoored March 24, 2026. Later safe release `1.83.0` and new pipeline were reported. Current versions are **not thereby proven malicious**. Additional gateway key storage, master key, logging and failover permissions demand careful configuration; default fallbacks can have access-control surprises unless enforced. | **No LiteLLM install for this project now**; learn from safety architecture and incident. |
| [maximhq/bifrost](https://github.com/maximhq/bifrost) | Automatic retries, categorized quota/auth/429 failures, per-key rotation and provider fallback | A local gateway handling upstream credentials and upstream request contents; documented observability and metrics make storage/export configuration important. Heavy deployment and attack surface relative to our simple Windows single-user requirement. No specific malware claim. | **Architectural reference** for failure classification, not our MVP dependency. |

### Evidence/links and boundaries

- peva3 source: [`src/plugin.ts`](https://github.com/peva3/opencode-fallback/blob/main/src/plugin.ts) and [`src/log.ts`](https://github.com/peva3/opencode-fallback/blob/main/src/log.ts); observed repo HEAD `9ac3ef46ff3f50f3ffd934891868a95416de7409`.
- linuxdynasty source: [`src/failover.ts`](https://github.com/linuxdynasty/opencode-quota-failover/blob/main/src/failover.ts); observed HEAD `ef0a9842eaf9dab03c9d8bd4957043fa27595647`.
- Sharper-Flow source: [`plugin/src/plugin-internal.ts`](https://github.com/Sharper-Flow/opencode-model-routing/blob/main/plugin/src/plugin-internal.ts); observed HEAD `92edf19423b113e8f07c0966a537dfd8edf54f0e`.
- ocswitch: [README English, Security Notes](https://github.com/Apale7/opencode-provider-switch/blob/master/README_EN.md); observed HEAD `20cb8b6f2598663e4bb7daed7ed75e8a7847d2b1`.
- CC Switch: [SECURITY.md](https://github.com/farion1231/cc-switch/blob/main/SECURITY.md), [switch-provider user manual](https://github.com/farion1231/cc-switch/blob/main/docs/user-manual/en/2-providers/2.2-switch.md); observed HEAD `d9a62313c8a276216ed40245c638753606831e95`.
- LiteLLM official incident: [March 2026 advisory](https://docs.litellm.ai/blog/security-update-march-2026) and [GitHub incident issue #24518](https://github.com/BerriAI/litellm/issues/24518); observed repo HEAD `a5d05355b680506890034dc23a1cdfd2513697fd`. **Only versions 1.82.7 and 1.82.8** were confirmed affected in the vendor notice; no generalized allegation about today's releases.
- Bifrost: [retries/fallback documentation](https://github.com/maximhq/bifrost/blob/dev/docs/features/retries-and-fallbacks.mdx), [telemetry](https://github.com/maximhq/bifrost/blob/dev/docs/features/telemetry.mdx); observed HEAD `1c6d1d546cd3a81abf4df67244b1ae84094b49f0`.
- This is a **point-in-time research snapshot**, not a proof that source files and release artifacts are byte-identical. Source may have changed after the observed commit; require pinned commit/release hash verification before any future reuse.

### Security conclusion

There **are already tools that do model fallback**. We should not reinvent basic HTTP error classification or every gateway protocol from scratch. But a proprietary-free, secure, local **development-task continuity system** with a strong credential broker, fail-closed quota/cost policy, exact operation evidence, and safe Git-aware handoff is not established by any reviewed candidate. The user therefore approved **building our own narrowly scoped implementation**, borrowing *ideas and standards* rather than trusting unaudited executables with real keys. Whether a new implementation is safer must be **proven through tests and reviews**, not assumed because we wrote it.

## 5. Test plan and acceptance gates

### Disposable security test lab

- Use fake provider servers and synthetic keys with unique canaries. Verify no canary enters logs, UI snapshots, export files, prompts, debug traces, git status/diff, crash reports, or unapproved outbound destinations.
- Fake 429 with short Retry-After, hard quota exhaustion, delayed response, TCP reset, streaming disconnect after tool calls, cancelled request, 401 bad key, 404 retired model, and concurrent workers. Validate status and route choice independently.
- Deliberately interrupt: (a) before dispatch, (b) after provider accepted request but before response, (c) after local file write but before success receipt, (d) after Git commit but before acknowledgment. New model may continue **only** after read-only reconciliation or operator review.
- Deny arbitrary upstream URL redirection and `0.0.0.0` listener, test loopback authentication and hostile Origin, test remote code-injection through error messages and tool output.
- Verify no key is retrievable from SQLite or backups. Check Windows ACL and operating-user boundary, but do not misrepresent DPAPI as protection against malicious same-user code.
- Unavailable zero-cost providers -> **BLOCKED**, not a paid fallback; no hidden repeated trial of the exhausted provider. Require cost-policy revalidation if a free endpoint becomes paid.
- Import the [AI Agent Qualification Matrix](https://docs.google.com/spreadsheets/d/1JkJzVUpZr_eAVsVMZD4KbDTdl8mTptez4DKzBNFksEg/edit) read-only for suitability, retaining run dates, provider/host, repetitions and hard gates. Historical estimates are **not certificates**.

### Explicit acceptance definition

The MVP is accepted only after: clean permissioned installation from pinned reviewed dependencies; zero real-key leaks in canary tests; no remote listener; correct provider/cooldown selection; zero-cost hard gate; safe switch with no duplicate side effects across crash ambiguity; resume after app restart; preserved Git/workspace invariants; reproducible logs/evidence; and operator Stop/Pause working even under provider errors. A green tool/API result is **not** a substitute for verified local side effects.

## 6. Development roadmap

1. **Phase 0 — isolation/security design:** document IPC and credential-storage interface; pin exact OpenCode version and SDK calls; create test-only repo/fixtures, unprivileged sandbox and network canary harness; review dependency provenance. No real keys.
2. **Phase 1 — narrow MVP:** provider registry, manual model selection, fake API adapters, metadata logging, failure taxonomy, bounded fallback only on *read-only and demonstrably side-effect-free* operations. Local-first dashboard optional until core passes.
3. **Phase 2 — safe task continuity:** SQLite checkpoint/reconciliation, Git-aware workspace locks, single-writer supervision, controlled handoff of checked mission/evidence, pause on ambiguous side effects.
4. **Phase 3 — qualification-aware selection:** benchmark matrix import, preflight model eligibility, operator quotas/zero-cost policy, cooldown scheduling, provider data-policy allowlists, model specialization.
5. **Phase 4 — validated real-provider integrations:** each provider added one at a time with disposable limited-scope keys and explicit endpoint approvals. Independent security review, failure injection, long-run survivability; only then broaden permissions.
6. **Phase 5 — future local inference:** Ollama/LM Studio through a compatible reviewed adapter, keeping workloads and privacy policies independent of hosted gateways.

**One-sentence design law:** *Models are replaceable; operator authority, verified task state, credential boundaries and repository evidence are not.*
