# Archived source fragment 16/23 — 2026-10-08T0752Z

Action 285 parser-validated the corrected structural Firefox activation helper before scheduling it. After exact Action 285 browser delivery, the helper bound the single visible Firefox `MozillaWindowClass`, selected the exact existing `Debugging - Runtime / this-firefox` tab, matched one `GPT Windows Relay` extension card using relay identity plus the live extension path and extension metadata, invoked its single card-scoped Reload control, selected the unique `PC Engineering 3` tab, refreshed it, and observed a fresh `v11-scroll-v5-delivery-v8` content-script start. Together with the already-live replacement backend from Action 276, delivery-v8 is now active across both boundaries. The final P4 gate is one end-to-end synthetic managed PNG attachment returned through ChatGPT and deleted only after confirmed delivery.


## P4 screenshot-on-request capability — COMPLETE GREEN

Action 287 completed the first true end-to-end screenshot return. A disposable topmost WPF window containing only synthetic proof text was captured through the live exact-window screenshot primitive. The action result advertised one managed PNG, delivery-v8 fetched that PNG through the authenticated basename-only backend route, the content script attached it to the ChatGPT composer, and the image arrived visibly in the same user result turn. Action 288 verified `relay_attachment_attached` telemetry before/at result delivery, zero send retries, confirmed result delivery, and deletion of the managed local PNG after delivery. No ordinary desktop image was used.

P4 is complete: explicit screen/window/region capture, bounded 20-file/24-hour managed storage, authenticated one-shot return suitable for ChatGPT visual inspection, and post-delivery cleanup are all live and proven. Continuous screenshot capture remains absent by design.


## AUDIT — PC Engineer 3 operations 285–288

- 285 parser-validated and armed the corrected structural Firefox v8 activation helper behind an exact result-delivery gate.
- 286 proved full backend + Firefox delivery-v8 activation GREEN with fresh `v11-scroll-v5-delivery-v8` telemetry.
- 287 captured a disposable synthetic WPF window and returned its managed PNG as an actual ChatGPT image attachment through delivery-v8.
- 288 verifies attachment telemetry, delivery ordering, zero retry behavior, managed PNG cleanup, and closes all P4 task items.


## INCIDENT — Action 289 orchestration helper returned None

Action 289 failed immediately after a read-only `git status --porcelain`. Its assistant-authored Python `q()` helper placed `return p` on the same semicolon-controlled line as the error branch, so successful commands returned `None` and the operation raised `AttributeError` before any repository or live-tree mutation. Action 290 replaces the helper with an unconditional return path.


## P5 semantic UI Automation control adapter v1 — STAGED

Action 290 begins P5 by extending the existing exact-window UI Automation model rather than adding coordinate clicking. `windows_tools.py` gains bounded semantic inspection plus exact control InvokePattern, SelectionItemPattern, and desired-state TogglePattern operations. Mutating operations require a control type plus Name and/or AutomationId, reject ambiguous matches, require visible/enabled targets, and verify selection/toggle readback where a semantic state exists. The adapter contains no SendKeys path. `sync-live.py` now carries the new adapter script into the live tree.


## AUDIT — PC Engineer 3 operations 285–289

- 285 repaired and parser-validated the Firefox v8 activation helper.
- 286 proved backend + Firefox delivery-v8 activation GREEN.
- 287 completed the first true synthetic PNG return to ChatGPT.
- 288 verified attachment ordering, zero retries, post-delivery managed-file cleanup, and closed P4.
- 289 failed before mutation due to an assistant-authored Python orchestration return-path defect; only read-only git status executed.


## INCIDENT — Action 290 full-suite invocation used wrong working directory

Action 290 successfully compiled the P5 adapter and passed its focused seven-test contract suite. Its later full-suite invocation was launched from the repository root while supplying an absolute tests directory, so legacy tests using plain imports could not resolve `windows_relay`, `resume_profile`, or `job_application_helper`. Action 291 recovered the full saved stderr and proved all four failures were import-path errors from that invocation shape, not adapter regressions. Action 292 restores the canonical test working directory (`windows-relay`) before evaluating the staged implementation.


## P5 semantic UI Automation control adapter v1 — LIVE GREEN

Action 292 corrected the prior full-suite working-directory error, passed the complete source regression suite, synchronized the new adapter through `sync-live.py`, and passed the complete live-tree suite. A disposable WPF harness then proved bounded semantic Button inspection, exact AutomationId InvokePattern with application-side effect, desired-state CheckBox TogglePattern On→Off readback, exact ListItem SelectionItemPattern readback, and fail-closed refusal of an ambiguous duplicate-name Button match. No coordinate clicking or SendKeys path was used.


## P5 Firefox browser-tab adapter v1 — STAGED / SUPERSEDED BY LIVE PROOF

Action 293 established the semantic discriminator for real Firefox browser tabs: visible enabled `TabItem` controls whose immediate parent is the Firefox `ControlType.Tab` with `AutomationId=tabbrowser-tabs`. This excludes page-internal tab controls such as Gmail categories. Action 294 packages that rule into the first P5 app-specific adapter with exact/unique tab selection and SelectionItem readback; no coordinate or SendKeys fallback is used.


## INCIDENT — Action 294 cached dynamic Firefox tab title across tab switch

Action 294 staged and pushed Firefox tab adapter v1 after 98 source tests and a successful live-tree sync. Its first live selection of the exact debugging tab succeeded. The proof then attempted to return using the ChatGPT tab's previously cached exact accessible Name and the adapter refused with `FIREFOX_TAB_MATCH_COUNT_0`. The adapter therefore failed closed rather than guessing. Action 295 re-enumerated live browser tabs and recovered the unique ChatGPT tab using the stable semantic substring `PC Engineering 3`, proving that exact browser-tab names must be treated as dynamic across selection/title updates. Future workflow proofs must re-resolve or use an intentionally unique stable substring rather than cache an exact dynamic title.


## P5 Firefox browser-tab adapter v1 — LIVE GREEN

Action 296 completed the first app-specific P5 adapter proof against the active Firefox instance. The adapter enumerated only browser-level `TabItem` controls under Firefox `tabbrowser-tabs`, excluded page-internal Gmail tabs, selected the exact existing `Debugging - Runtime / this-firefox` browser tab with SelectionItem readback, re-enumerated after the switch, then returned to the unique `PC Engineering 3` tab using a stable semantic substring and verified selected-state readback. This closes the live proof without coordinate clicking, SendKeys, page-DOM guessing, or reuse of a stale dynamic exact tab title.


## AUDIT — PC Engineer 3 operations 290–294

- 290 staged the semantic UIA adapter and passed its focused contract suite, but the full-suite invocation used the wrong working directory and failed on legacy import resolution before live sync or commit.
- 291 recovered the full saved result and proved those failures were test-harness import-path errors rather than product regressions.
- 292 reran the suite from the canonical `windows-relay` working directory, passed 95 source tests and the full live-tree suite, then live-proved semantic inspect/invoke/toggle/select plus ambiguous-match refusal.
- 293 read the Firefox UIA hierarchy and established `tabbrowser-tabs` as the semantic boundary separating real browser tabs from page-internal tab controls.
- 294 implemented, tested, synced, committed, and partially live-proved Firefox tab adapter v1; exact debugging-tab selection succeeded, while returning with a cached exact ChatGPT tab title failed closed after that title changed dynamically.


## P5 workflow composition v1 — STAGED

