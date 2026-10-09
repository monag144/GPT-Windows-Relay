# PCE13.000–.019 — mandatory twenty-operation engineering review — 2026-10-09T1914Z

## Mission and authority
Repository `monag144/GPT-Windows-Relay`, branch `pce11/one-click-go-recovery-and-doc-hygiene`. Current mission: standalone 12h unattended Windows Relay qualification, then 24h extended qualification, eventually One-Click GO r28 and browser A–Z acceptance with STOP, no duplicate side effects, source/runtime parity. Canonical five controls: `consumer/control_harness.py`, `windows-relay/TASKS.md`, `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`, `docs/windows-relay-established-facts.md`, `docs/relay-sandwich-procedure.md`. The source still names PCE11 in its text, while successor uses actual `engineering_preflight(root,n,series=13)` and PCE13.000–.100 ordinal budget. Keep source-only preflight and runtime authority separate.

## Five-window reconciliation
| Window | Source-of-truth audit | Outcome |
| --- | --- | --- |
| .000–.004 | `docs/audits/AUDIT_2026-10-09T1115Z_PCE13_OPERATIONS_000_004.md` | .000 governance read error, .001–.004 corrected; dirty local untracked PCE12 evidence; .018/.019 older rotation worker failures discovered, not accepted handoff. Read-only with stdout truncation. |
| .005–.009 | `docs/audits/AUDIT_2026-10-09T1126Z_PCE13_OPERATIONS_005_009.md` | .005 dispatch blocked due absent local audit; safeguarded out-of-band GOVSYNC fast-forward restored it. .006/.007 recovered PCE12.018 `NEW_CHAT_URL_NOT_VERIFIED_NO_GREETING`, PCE12.019 `COMPOSER_NOT_EMPTY_ABORT`. .008 33/33 static/regression tests green, false-positive PowerShell parse diagnostic; .009 independent ParseFile/ParseInput zero errors. |
| .010–.014 | `docs/audits/AUDIT_2026-10-09T1905Z_PCE13_OPERATIONS_010_014.md` | .010 origin UIA diagnostic incorrectly uses PowerShell `$matches` automatic variable; false `PROVEN_ORIGIN_COUNT=1`. .011 saved result had no inner stderr. .012 fixes diagnostic variable, origin not proven; .013 localizes missing selected-tab UIA identity (1 Firefox, 1 ChatGPT, 1 readable doc, selected tab 0). .014 command emitted but never observed reserved or completed, no RESULT; side-effect status not inferred from missing user response alone. |
| .015–.019 | `docs/audits/AUDIT_2026-10-09T1913Z_PCE13_OPERATIONS_015_019.md` | .015 durable journal `.014` not reserved, 0 outbound/result; relay still running. .016 Firefox crash files 0 and relevant Windows application/system crash events 0; browser journal active. .017 120-second confirmation watchdog failed four times in window. .018 exact result envelope visible for `.012/.013`, zero recognized role-selector candidates. .019 captured ChatGPT DOM nested `group/user-message`, `bg-user-message`, anonymous DIVs; fallback exact-envelope check remains unproven. |

## Exact twenty-slot operation ledger (harness-required labels)

This ledger explicitly accounts for every attempted slot. It does not retroactively turn blocked, uncertain, or unacknowledged results into successes; the linked five-operation audits retain precise packet IDs and preserved results.

| Slot | Evidenced classification and result |
| --- | --- |
| PCE13.000 | Initial governance read incomplete; read-only baseline; remediation next slot |
| PCE13.001 | Five controls and preflight accepted; stdout truncated; read-only |
| PCE13.002 | Verified dirty PCE12 audit and protected listener; read-only |
| PCE13.003 | Recovered PCE12 results and untracked audit; stdout truncated; read-only |
| PCE13.004 | PCE12.018/.019 handoff outcomes found unsuccessful; read-only |
| PCE13.005 | GOVERNANCE_BLOCKED due absent locally synced five-slot audit; no dispatch |
| PCE13.006 | After GOVSYNC, verified PCE12.018 navigation error; read-only |
| PCE13.007 | Recovered PCE12.019 COMPOSER_NOT_EMPTY_ABORT; read-only |
| PCE13.008 | 33 targeted tests pass; misleading PowerShell parser diagnostic; no effect |
| PCE13.009 | Correct ParseFile/ParseInput both zero errors; read-only |
| PCE13.010 | UIA origin count false-positive due $Matches collision; no UI effect |
| PCE13.011 | Read saved .010 failure; inner PowerShell stderr unavailable |
| PCE13.012 | Resolved $Matches conflict in probe; real origin count zero; read-only |
| PCE13.013 | One Firefox ChatGPT window/document; selected tab identity zero |
| PCE13.014 | Packet emitted but no relay execution record or saved result; UNKNOWN delivery, no replay |
| PCE13.015 | Backend journal shows .014 unreserved; relay process alive |
| PCE13.016 | Browser journal live; Firefox crash reports zero and relevant Windows events zero |
| PCE13.017 | Watchdog telemetry four expirations, one confirmed result submission, stdout truncated |
| PCE13.018 | Two exact envelopes visible but zero role selector candidates; stdout truncated |
| PCE13.019 | Captured nested real ChatGPT user-message DOM; structural fallback still unverified |

## Major failures, resolutions, unresolved blockers
1. **P0 Rotation:** PCE12 handoff has NOT been delivered and positively verified in a new same-origin ChatGPT tab. PCE12.018 navigation URL unknown; PCE12.019 new composer nonempty (may be placeholder or draft). Preserve drafts; no blind paste or repeated click/Send. Agent011 current-tab worker is still PCE12-specific, not a safe PCE13→PCE14 drop-in.
2. **Governance publication drift:** Audits committed to remote do not pass Windows pre-dispatch governance until synced. .005 was genuinely GOVERNANCE_BLOCKED, not retroactively successful. Resolved each boundary using separate explicitly identified, constrained, verified fast-forward, preserving original untracked PCE12.010–.014 audit and its immutable LOCALAPPDATA backup. As of most recent successful checkpoint, local HEAD `4ce1b42a91a5dd694267b1800e8b98cb372af209`, with exactly one preexisting untracked audit.
3. **False tooling probe:** `.008` PS parser error caused by bad diagnostic invocation; `.009` real parser 0 errors. `.010` `$Matches` collision was our own PowerShell diagnostic bug. Never treat own probe errors as worker/runtime crashes.
4. **Unsent result turn recognition:** PCE13.012/.013 result envelopes visibly present, `USER_SELECTOR` matches zero nodes, strict receipt watchdog fires. Source `content.js` contains guarded structural bubble fallback; `.019` shows `.013` has `bg-user-message` bubble with direct parent classes satisfying source check, so investigate exact envelope parsing and other provenance before changing selectors. A result in body alone is not sufficient evidence: do not weaken no-assistant-quote anti-replay contract.
5. **Missing .014 command:** PCE13.014 not recorded in backend's processed, outbound, or results, while surrounding browser events and later actions work. Browser scanner/response/rendering failure suspected but **not proved**; do not call this a Firefox process crash or equate 120-second receipt watchdog with direct cause of non-dispatch.
6. **Browser tab identity:** .013 detected 0 uniquely selected UIA TabItem despite 1 ChatGPT Firefox window/document. Resolve with read-only UIA provenance before attempting semantic same-tab rotation. Don't target a different tab/window or use an old separate-window worker.
7. **Protocol rendering:** Earlier action fences had extra metadata; canonical `docs/relay-sandwich-procedure.md` mandates exactly visible header → **bare** triple-fenced `[GPT_WINDOWS_ACTION]` JSON → visible footer, all in one final. Correct next emission.

## Regression/tests, release metrics and safety
- Source-only preflight succeeded in corrected operations; it always reports `mutation_authorized=false`. No code patch, extension installation, runtime restarts or UI-affecting worker acceptance across PCE13.000–.019.
- `.008` passed 33 targeted tests. `.009` parser ParseFile/ParseInput zero errors. No full test suite, no current-tab end-to-end delivered handoff, no 12-hour unattended or 24-hour extension qualification. Keep readiness as **NOT ACCEPTED**.
- Evidence of duplicate Windows action execution in these operations: none; relay journal authoritative for dedup. Evidence of lost drafts: none from read-only steps; not a global guarantee. At least one user rescue involved reporting a crash/missing result and recovery. Do not claim no unobserved effects from .014 on assumption alone.
- Rollback strategy: GitHub branch source-verified, pin commit blob SHAs and exact diff before fast-forward; never clean dirty tree; preserve `%LOCALAPPDATA%/GPTWindowsRelay/ops/GOVSYNC13-AUDIT-RESTORE-20261009-01/PCE12_010_014_preserved.md`; no live promotion without rollback and STOP owner checks.
- Logs captured limited recent history and some stdout was truncated; only full persisted outputs may disambiguate .017/.018 telemetry. Source diagnostics `.019` do not expose actual bubble full text, so fallback failure remains open.

## Next twenty-operation plan
Before PCE13.020: publish the `.015-.019` audit and this twenty-op review to canonical GitHub; verify exact remote diff and source SHA; guarded Windows fast-forward preserving PCE12 evidence; run `engineering_preflight(root,20,series=13)` and demand BOTH `checkpoints.audit` and `checkpoints.review`.
Proceed from .020 with **read-only** DOM matcher forensics or Codex CLI source review using recorded anonymous structure; derive a fail-closed fix with positive and negative automated tests for exact user bubble, assistant quote, altered JSON and unsent draft. Then source code patch GitHub-first and full-suite in isolated checkout, verify artifact parity and rollback, owner STOP and runtime gates before any bounded one-shot browser canary. Keep 12h overnight qualification and 24h follow-up postponed until actual proven successful delivery.

**REVIEW COMPLETE FOR OPERATIONS 000–019; QUANTITY=20 EXACT; LIVE/OVERNIGHT ACCEPTANCE BLOCKED.**
