# PCE 011 Firefox resolver GitHub-only source review — 2026-10-08T0735Z

## Source proof
Read `windows-relay/firefox_tab_adapter.ps1`, `firefox_adapter.py`, and `windows-relay/tests/test_firefox_adapter.py` on canonical GitHub. Existing resolver enumerated only TabItem descendants of visible MozillaWindowClass process-scoped windows. It rejected `IsOffscreen` TabItems before inspecting URL, and required their direct `ControlViewWalker` parent to match `Tab/tabbrowser-tabs`. On Firefox UIA trees with offscreen inactive tabs or intermediary wrappers, this can yield a false zero-match even if a valid tab exists.

## GitHub fix
Commit `07ed26e0`:
- Stop treating TabItem offscreen state as definitive absence; still require enabled, genuine Firefox tab-strip ancestor.
- Bounded six-level ControlView/RawView traversal for the `tabbrowser-tabs` ancestor; no generic arbitrary-tab acceptance.
- No silent fallback to an unverified tab. Counts classify no tabs, noncanonical tabs, and URL readbacks without leaking other conversations' URLs.
- Preserve original-selection restoration after scanning and maintain fail-closed exact URL/match count.
- Add source-level test enforcing those contracts.

## Evidence boundary
This is an evidence-backed *potential* filtering defect, not a live root-cause proof. The current selected conversation URL may also be stale, or Firefox UIA may expose no tab items. Source/static JS checks were run during transformation; Windows PowerShell AST tests, full suite and browser canary remain **NOT RUN**. No relay executed. No current browser PID, URL or loaded runtime identity assumed.

## Activation order
Remote reviewed SHA → fast-forward Windows checkout → PowerShell AST and focused/full tests → read-only classification → exact target binding → operator STOP/backup verification → narrowly-scoped reversible staged activation → new unique harmless exact-once + result visibility canary. Do not bypass any gate.
