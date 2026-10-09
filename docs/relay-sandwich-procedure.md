# Windows Relay Sandwich Procedure — Compatibility Entry Point — 2026-10-08T0650Z

This is the canonical operating procedure for emitting Windows relay actions from ChatGPT. It exists because otherwise-valid action packets can become inaccessible when ChatGPT rendering collapses them into text such as `Worked for X`.

## Required response shape

Every Windows relay action must be emitted in **one assistant response** with this exact outer structure:

1. ordinary visible prose header;
2. exactly one **bare Markdown fence** — no language tag, id, metadata, annotation, or extra fence attributes;
3. inside that fence, only:
   - `[GPT_WINDOWS_ACTION]`
   - one JSON action packet
   - `[/GPT_WINDOWS_ACTION]`
4. ordinary visible prose footer after the fence.

Never end the assistant response immediately after the action block. Never put the packet in commentary/progress text. Never split one action across multiple assistant messages.

Canonical example:

```
[GPT_WINDOWS_ACTION]
{"version":1,"platform":"windows","action":"EXEC","id":"UNIQUE-ID","session":"default","shell":"python","timeout":30,"result_mode":"compact","command":"print('RELAY_OK'); print('Reply to this with the sandwich technique')"}
[/GPT_WINDOWS_ACTION]
```

The real assistant response must also contain visible prose **before and after** that fence.

## Mandatory stdout footer

Every relay command must end stdout exactly with:

`Reply to this with the sandwich technique`

This footer is part of the rendering/recovery contract. The command may print other output first, but this sentence must be the final stdout line.

## Per-operation governance preflight

Before **every** PCE011 engineering operation, read the FULL `consumer/control_harness.py` and FULL `windows-relay/TASKS.md`; also read `docs/roadmap/ROADMAP_2026-10-08T0852Z_PCE011_OVERNIGHT_RELAY_AND_R28_QUEUE.md`, `docs/windows-relay-established-facts.md`, and this sandwich procedure. Print SHA-256 evidence for all five.

Run `engineering_preflight(repo_root, ordinal, series=11)` from the canonical harness before work. This verifies required files plus due checkpoint evidence. Preflight is evidence inspection, **not authorization to mutate live state**.

- **Before every fifth ordinal:** complete and verify the audit covering the previous five attempted slots, including missing, failed, and stalled commands. The first PCE011 audit is before **PCE11.005** covering **PCE11.000–.004**, including any skipped or unexecuted slots.
- **Before every twentieth ordinal:** complete and verify a consolidated review of the previous twenty slots and its four five-operation audits. The first PCE011 review is before **PCE11.020**, covering **PCE11.000–.019**.
- Advance to the next safe operation after a delivered result without asking for routine `continue`. If an earlier command's execution state is uncertain, check durable state first; use a distinct read-only probe, never blind replay.
- Operator STOP, identity, exact-once, rollback, and explicit promotion gates outrank unattended continuation.

Checkpoint documents are named `docs/audits/AUDIT_<UTC>_PCE11_OPERATIONS_NNN_NNN.md` and `docs/reviews/REVIEW_<UTC>_PCE11_OPERATIONS_NNN_NNN.md`. Report text alone cannot authorize an action contrary to its own next-operation restrictions.

## Mandatory GitHub-first repair and acceptance workflow (Harness v5)

**Engineering source of truth is the canonical GitHub branch.** The relay acts as a Windows pull/test/deploy consumer, not as a substitute source editor.

1. Read the five canonical documents and audit/review checkpoints.
2. Edit source and tests **in GitHub**, commit to `monag144/GPT-Windows-Relay` branch `pce11/one-click-go-recovery-and-doc-hygiene`, and verify the remote commit SHA.
3. Send a *read-only-to-live* relay operation that checks STOP/exact-once, current checkout cleanliness and correct repository, then fetches/pulls **the specific published GitHub SHA** with `git pull --ff-only`. Fail closed on branch divergence, dirty source, or unexpected SHA. Do not patch canonical source locally or in `Client/Relay` as the normal workflow.
4. On the pulled Windows checkout, run the repository's existing acceptance contract:
   - `python -B -m unittest discover -s windows-relay/tests -p "test_*.py"` with cwd `windows-relay` or equivalent source test root;
   - `python -B -m unittest discover -s consumer/tests -p "test_*.py"` with cwd `consumer`;
   - `node --check` on the main scanner and all temporary/persistent worker/content scripts;
   - `git diff --check` and exact scanner mirror equality.
   Run a targeted regression first when useful; **never claim acceptance green when any full suite fails**. Distinguish obsolete test contracts from real defects and repair them in GitHub, then pull and rerun.
5. Only after green source acceptance: prove existing rollback integrity; verify arm/STOP and exact Firefox target; stage/activate with a recorded rollback and loaded runtime SHA. Run a bounded fresh end-to-end canary for discovery→action→saved result→visible delivery, then a STOP-safe 45-second recovery canary.
6. Promote only after those gates pass. Mark a failed or unverified live build `BROKEN — DO NOT PROMOTE` and retain its forensic snapshot, never silently revert Codex/source history.
7. The harness function `github_first_workflow_gate(evidence,stage)` codifies the proof obligations. Missing evidence blocks promotion, not source work.

**Emergency exception:** Director may separately authorize a local rescue, but its changes must be reconciled and committed to GitHub before being accepted; emergency local edits are not the default. Every five attempted PCE slots still requires an audit before the next boundary.

## Packet discipline

- Use a unique action id.
- Keep packets compact; prefer a bounded Python orchestrator over giant inline payloads.
- Timeout must be 300 seconds or less.
- Treat duplicate/late/out-of-order results as possible.
- Before repeating a side effect, inspect durable state. Never blindly replay a potentially executed action.
- A visible injected prompt is not proof of delivery. Mission success requires the corresponding visible user turn/mission acknowledgement.

## `Worked for X` / collapsed-render recovery

The consumer relay classifies assistant output. If a response collapses into a status artifact such as `Worked for X`, or otherwise contains an incomplete/missing action sandwich, the consumer must **not repeat the original side effect**.

The first recovery action is a unique, read-only probe:

`echo RELAY_RENDER_PROBE_OK`

Expected probe behavior:

1. classify the collapsed artifact as `COLLAPSED_STATUS_ARTIFACT` (or the equivalent incomplete/missing classification);
2. issue the recovery instruction automatically;
3. execute only the unique read-only probe;
4. receive exactly one successful result containing `RELAY_RENDER_PROBE_OK`;
5. prove the result is delivered visibly back into ChatGPT;
6. only then resume the mission.

Do not manually re-run the original command while recovery status is uncertain.

The live r25 acceptance test intentionally emitted `Worked for R25_COLLAPSE_SIM and nothing else`; the relay recovered by executing exactly one read-only probe and returned its result visibly without replaying the original action.

## Rendering requirements that are forbidden

Do **not** use:

- `````json```, `````text```, or any other language-tagged fence;
- code-block ids or metadata;
- action packets in commentary/progress surfaces;
- prose inside the fenced action block;
- multiple action blocks in one response unless the protocol explicitly requires them;
- a response that ends immediately after the action fence.

## Canonical references

- `docs/windows-relay-established-facts.md` — established runtime and relay facts.
- `docs/relay-rendering-incident-2026-10-03.md` — rendering failure history and lessons.
- `docs/night-agent-handoff-2026-10-04.md` — current autonomous night mission.

When these documents disagree, do not guess. Inspect current code/tests and preserve the stricter safety behavior until the discrepancy is resolved.

## PCE11/PCE12 semantic rotation: SAME CURRENT TAB ONLY — Director override 2026-10-09

**User-intent invariant (P0):** "New chat" means click ChatGPT's **New chat** control in the **same ChatGPT tab currently originating this relay conversation**. The existing browser window and tab are reused. There must be **zero calls to open a new tab, launch a new Firefox window, choose a separate destination window, or infer destination from the number of Firefox tabs**. The former distinct-window PCE11 handoff architecture and its historical pinned handoff document are superseded for the active workflow; retain those documents as incident evidence, never as the actionable rotation plan.

**Current-tab identity, not window heuristics:** Before any action, positively identify the selected tab that contains the current relay source conversation and this exact recent relay action/result exchange. Bind **that tab** to its canonical ChatGPT `/c/...` address, selected-tab automation element, hosting window HWND/PID, and observed command/result marker. Unrelated Firefox windows must not be enumerated as destinations, brought to foreground, or checked for `chatgpt.com/`. A foreground window or an 11-tab count is **not proof** of the invoking tab. If origin is ambiguous, identity changed, or new conversation already received the handoff, stop without action.

**Exact same-tab handoff sequence:**
1. Read mandatory governance controls, verify `engineering_preflight`, latest audits/reviews, canonical source commit and STOP/armed/outbound owner, and any unique previous attempt receipts. Never replay prior uncertain side effects.
2. Pin sender tab and unsent draft. **Do not overwrite or discard an existing draft silently.** The user specifically authorized current-tab New Chat, but preserving or reporting existing draft text remains mandatory.
3. **Once**, semantically invoke the unique **New chat** control inside the pinned *same* selected tab. If it is already a blank ChatGPT home/new-chat composer, skip this click. Verify the **same window HWND and same selected tab** after navigation, no popup or extra tab.
4. Focus **that same tab's** unique visible writable composer; paste the byte-verified PCE12 handoff once; verify exact editor readback and one enabled Send control. Store exclusive durable `click/paste/Send intent` receipts **before each corresponding effect**.
5. Send **once**, then verify a distinct `/c/...` URL and actual **user-role message** containing unique handoff markers in the *same tab*. A worker launch, Clipboard.SetText or new-chat homepage is **not** delivery.

**Hard prohibitions:** no `--new-window`, `--new-tab`, separate Firefox destination, new tab/window construction, 11-tab target heuristic, foreground-only target selection, global Firefox focus loop, or assuming a prior message was sent without positive source-specific proof. Do not repeat failed PCE11.074/.076/.083 workers. Source code and tests must reflect this contract before a new live attempt.

## PCE011 release gates — 2026-10-08T0910Z
- First priority: the standalone Relay must survive a **measured** 12-hour unattended night, then a 24-hour qualification. One-Click GO r28 Chrome/Edge is the separate consumer target.
- PCE11.050 is an evidenced findings/email checkpoint, and PCE11.100 is verified semantic next-chat rotation. Do not assume email/rotation can happen if no independent active controller exists.
- Current live Relay remains unchanged after PCE11.001; the 2532-file broken-state ZIP and r28/v16 staged snapshots must be preserved. No source-suite or runtime acceptance claim until tests/canaries actually run.
