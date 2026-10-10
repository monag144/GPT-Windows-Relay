# Windows Relay operating safety — 2026-10-09

**Repository:** `monag144/GPT-Windows-Relay`, not `GPT-Termux-Relay`. **Evidence scope:** October 9 Pacific-local review of GitHub main at `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8` and user-provided PCE15.043–.049 isolated test receipts. Not a claim of present loaded-extension identity, installed Client bytes, or release readiness.

## Operating boundaries

- Use unique relay action IDs and the visible header → single bare fenced `[GPT_WINDOWS_ACTION]` JSON → visible footer form, with exact user-result recognition. Never blindly re-run an operation with possible side effects.
- **Backend exact-once guarantee is NOT established.** PCE15.043 source-level isolated tests reproduced concurrent check-then-reserve duplicate execution; PCE15.047 source-level tests reproduced replay after the 500-entry processed-ID cache evicted an old ID, including a changed-payload collision raised **after synthetic execution**. These are not proof of a real duplicate shell command, but they invalidate blanket guarantees previously stated in `windows-relay/README.md`.
- The memory-only ledger/atomic-claim prototype in PCE15.049 was not deployed or proven durable. Never claim remediation until a reviewed fix and loaded-runtime acceptance exist.
- Latest independently graded PCE15 product checkpoint: audit window [45,49] accepted for the subsequently attempted PCE15.050. That packet later returned `relay_owner_same_session_different_conversation` in PCE16, and its ordinal is consumed, not eligible for retry. Grade F / BLOCKED (11/28), G16 loaded Firefox identity UNKNOWN, G26 independent live sends 0/60, G27 endurance 0/2. Reconfirm actual running evidence before reporting newer status.
- **Permanently retired:** all automatic agent/chat switching and replacement development. The only authorized transfer is an expressly requested one-shot existing `Run-Copy-Contents.cmd`, with the source engineer deriving current PCE series +1. See `docs/policy/SCRIPT_ONLY_AGENT_HANDOFF_2026-10-09.md` and the retirement bin `windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md`. Previous hold is historical. At the PCE ordinal limit, stop rather than auto-rotate.
- Honor STOP/ARM, governance preflight, GitHub-first audit checkpoint cadence, and independent verification of all file mutations. The installed `consumer/control_harness.py` API must be inspected rather than assumed equal to GitHub source.
- Do not infer browser extension loaded state, Windows scheduled-task state, Firefox signing, or production readiness from documentation or static code alone.

## History and evidence

Prior full rules are preserved at GitHub commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8`, path `docs/RELAY_OPERATIONAL_RULES.md`. That snapshot included an obsolete requirement to auto-rotate every 100 actions and a superseded note about the control harness; neither is active operating authority.

Exact-once incident records: `docs/incidents/INCIDENT_2026-10-10T0250Z_PCE15_NONATOMIC_ACTION_CLAIM_AND_OWNER_GUARD_GAPS.md` and `docs/incidents/INCIDENT_2026-10-10T0304Z_PCE15_DEDUP_RETENTION_POST_EVICTION_REPLAY.md`.

**Safety precedence:** actual current user directives, verified GitHub and installed runtime evidence, then dated history. Untimestamped labels are not authority.
