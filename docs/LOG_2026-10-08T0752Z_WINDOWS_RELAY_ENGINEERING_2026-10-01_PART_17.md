# Archived source fragment 17/23 — 2026-10-08T0752Z

Action 297 adds a deliberately small workflow runner over already-proven primitives. Workflow v1 accepts at most 32 prevalidated steps from a fixed operation allowlist: clipboard read/write/clear, semantic UIA field/control operations, Firefox browser-tab list/select, and explicit screenshot capture. It has no arbitrary shell, eval, coordinate click, templating, or implicit branching. Plans are validated completely before the first side effect, execution stops on the first failed step, and an explicitly declared window/region `fallback_screenshot` can return `needs_visual_reasoning` plus a ChatGPT image attachment rather than guessing the next interaction. Automatic full-screen fallback is intentionally disallowed.


## INCIDENT — Action 299 closeout verifier null-detail assumption

Action 299 was a read-only closeout verifier and failed before any repository mutation because its browser-event filter called `.get()` on event records whose `detail` field was explicitly null. Action 300 corrected the parser to normalize null/non-object detail values before packet filtering. The underlying Action 298 workflow result, visible ChatGPT image attachment, and managed-file lifecycle were unaffected.


## P5 workflow composition v1 — LIVE GREEN / P5 COMPLETE

Action 298 live-proved workflow composition across three already-proven adapters: clipboard write/read, Firefox browser-tab discovery/selection, and semantic UI Automation inspect/invoke. The success workflow completed all six ordered steps and produced the intended synthetic button side effect. A second workflow intentionally targeted two identically named buttons; semantic UIA refused the ambiguous mutation with `CONTROL_MATCH_COUNT_2`, the workflow stopped before the following clipboard step, and the explicitly declared exact-window screenshot fallback returned `needs_visual_reasoning` with a managed PNG attachment. The user-visible relay turn contained that synthetic image. Action 300 verified attachment telemetry preceded send confirmation and delivery completion, observed no send retry, and verified delivery-v8 deleted the managed PNG afterward. The original clipboard was restored.

P5 is complete: richer fail-closed semantic UIA primitives, a live Firefox app adapter, and a fixed-allowlist higher-level workflow layer with bounded visual fallback are all implemented and live-proven. The workflow language contains no arbitrary shell/eval execution, no implicit coordinate clicking, and stops on the first failed step rather than guessing.


## AUDIT — PC Engineer 3 operations 295–299

- 295 recovered the ChatGPT browser tab using fresh semantic substring resolution after 294 correctly refused a stale exact title.
- 296 completed the Firefox tab adapter live proof with structural browser-tab scoping, dynamic re-resolution, and selection readback.
- 297 implemented and staged workflow composition v1; focused workflow tests, the 103-test source suite, and live-tree synchronization all passed.
- 298 live-proved the normal clipboard + Firefox + semantic-UIA workflow and the fail-closed ambiguous-control path with exact-window screenshot fallback returned to ChatGPT.
- 299 attempted final telemetry/cleanup verification but its read-only parser assumed every event detail was an object; a null detail raised `AttributeError` before mutation.


## Native Python command_lines end-to-end validation — GREEN

Action 301 itself was delivered through the relay using `shell:"python"` plus `command_lines` and no `command`/`command_b64`. The executed program verified the canonical working directory, Unicode text, mixed quote/backslash punctuation, and embedded multiline string preservation before mutating project records. This proves native Python `command_lines` transport end to end through assistant packet parsing, browser bridge, localhost relay parsing, Python execution, result persistence, and browser result delivery.


## Roadmap reconciliation after P5 and command_lines proof

Action 302 reconciled the backlog against canonical Git history rather than stale V4-era checklist text. Commit `381b5416` establishes the contained scroll-V6 defer/revert; `7f1db855` establishes backend-only restart recovery; P1, P3, P4, and P5 completion commits are present; and Action 301 proved native Python `command_lines` end to end. The backlog now treats P0 as intentionally deferred, P2 as partially complete but externally gated by Mozilla signing, and P1/P3/P4/P5 as complete. The next actionable product milestone is obtaining/installing the signed persistent XPI so full Firefox and Windows/login restart recovery can be tested honestly.


## P2 signed persistent extension gate — local preflight prepared

Action 303 rebuilt and validated the current persistent extension package from `extension-persistent`, verified its manifest version/ID and exact package membership, inventoried Firefox/policy and local signing tooling without exposing credential values, and added `sign-extension.ps1`. The signing runner uses only environment-provided `WEB_EXT_API_KEY` / `WEB_EXT_API_SECRET`, invokes `web-ext sign` for the unlisted channel, and copies the produced artifact to the canonical `dist\gpt-windows-relay-signed.xpi`. The policy installer remains gated on that signed file and is parser-validated. No signing or policy installation is claimed unless an actual signed artifact is produced and verified.


## P2 local AMO signing toolchain — READY

Action 304 corrected the Action 303 preflight conclusion: AMO credentials were not the only missing prerequisite because Node/npm/npx/web-ext were also absent from the relay environment. Action 304 installed or discovered user-scope Node.js LTS without requesting elevation, verified native Node and npx execution, resolved `web-ext` through npx without contacting AMO for signing, and hardened `sign-extension.ps1` to locate user-scope/WinGet Node installations even when the long-running relay process has an older PATH. After this action, the local signing toolchain is executable; absent AMO API credentials are the remaining external authorization gate.


## P2 Mozilla AMO authorization boundary — classified

Action 305 opened the official AMO API-key page and Firefox redirected into Mozilla Accounts. Safe UI Automation inspection read only visible labels/control metadata and no field values, clipboard contents, passwords, JWT issuer values, or JWT secrets. Action 306 classifies the visible authorization state so the relay can stop exactly at the user-controlled authentication/authorization boundary rather than guessing or soliciting secret material through ChatGPT.

## 2026-10-03 — Human-intervention incident: visible relay packet produced no result
- The user had to report that the minimal relay packet was visible but produced no GPT_WINDOWS_RESULT/system response.
- Root cause in assistant rendering: opening Markdown fence contained metadata (`id="gfndkz"`) instead of being exactly three backticks.
- This counts as human intervention under the canonical incident policy because manual user diagnosis was required to continue an otherwise autonomous workflow.
- Correct contract: one assistant response containing visible prose header -> truly bare fence -> GPT_WINDOWS_ACTION envelope -> truly bare closing fence -> visible prose footer.
- Treat any language tag, id attribute, or fence metadata as a DO NOT ATTEMPT pattern.

## 2026-10-03 — Relay sandwich rendering recovery proven
- Recovery proof packet: `PCENG4-RELAY-036-true-bare-fence-proof`.
- End-to-end result: **OK**, exit code 0.
- Stdout contained `TRUE_BARE_FENCE_PROOF=OK` and the required final line `Reply to this with the sandwich technique`.
- This closes the immediate rendering incident: the correct assistant packet shape was accepted by the Firefox bridge, executed by the Windows relay, and returned automatically to chat.
- The preceding failed/collapsed attempts remain documented as DO NOT ATTEMPT patterns and human-intervention incidents.
- Future relay operations must preserve the proven visible-header -> bare fenced packet -> visible-footer technique.

## 2026-10-03 — Human-intervention incident: oversized command packet stalled
- A very large `command_b64` relay message remained unfinished/streaming for about five minutes and produced no GPT_WINDOWS_RESULT.
- The user had to report the stalled state and absent system response.
- The known-good sandwich wrapper was not sufficient because the assistant message itself was too large to complete reliably.
