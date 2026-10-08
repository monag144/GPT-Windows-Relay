# Incident — A6.399am content-contract fixture error — 2026-10-06T0205Z

**Class:** VALIDATION HARNESS DEFECT  
**Branch:** `consumer/r29-firefox-offline-tray`  
**Operation:** `PCENG-A6.399am-recovery-advice-redundancy-windows-gate`

A6.399am fast-forwarded Windows to `fcd7b8f`. Production Python compile passed, recovery-supervisor tests passed 14/14, and HUD tests passed 11/11. The gate then failed before live staging at the new content-contract test.

Root cause: `test_recovery_advice_has_secondary_observer_contract` referenced `self.content`, but `ChatGPTContentContractTests` defines no such fixture attribute. The test therefore failed before inspecting production content source.

Repair: read `windows-relay/extension/content.js` explicitly, consistent with the surrounding contract tests.

Classification: harness-only. No live dev files were staged by the failed operation, and Firefox was not reloaded. Product validation remains pending a corrected rerun.
