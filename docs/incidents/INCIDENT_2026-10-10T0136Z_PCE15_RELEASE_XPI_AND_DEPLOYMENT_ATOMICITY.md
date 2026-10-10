# Incident — PCE15 release archive/reproducibility and non-atomic live sync — 2026-10-10T0136Z

## Confirmed static findings

PCE15.017 detected that local `windows-relay/sync-live.py` allowlist has **38 files** versus **26** on canonical GitHub `main`. All 38 expected source/Client files exist, but 17 have true content drift; temporary Firefox `extension/popup.html` is referenced by `manifest.json` and present on both trees but omitted from deployment allowlist. The current local sync code creates backups and then copies each file into `Client/Relay` **before running unittest**. It deletes and replaces live tests before invoking them and rebuilds XPI afterward. Static inspection found no explicit atomic swap or automatic rollback call after failure. This design can leave a mixed or partially deployed Client if an update/test fails. The test did not execute sync or prove an actual failure occurred.

PCE15.018 inspected **18 readable XPI archives** under Client `dist`; no recognized signature-named entries found and no matching registration record in two scanned Firefox profile metadata directories. Neither observation proves the absence of a currently running temporary extension or conclusively rules on Mozilla signature verification. The exact Firefox-loaded code remains UNKNOWN.

PCE15.019 CRC-checked `gpt-windows-relay-0.3.17.xpi` (SHA256 `18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8`). Five named required assets were present. `popup.html` and `popup.js` matched normalized current source and Client. `manifest.json`, `content.js`, and `service_worker.js` did **not** match current source and Client, despite version number `0.3.17`. Tested release reproducibility **FAIL (3/5 mismatches)**. This incident is distinct from historical Client drift (PCE15.009) and seven simulated merge conflicts (PCE15.014).

## Safeguards and release disposition

**Incident OPEN; Grade F, release BLOCKED.** No production change, extension install/reload, build, XPI replacement, branch merge, Git-index change, Firefox input, message send, or rollback occurred in PCE15.015–.019; all five receipts prove unchanged worktree and protected audit hashes. Source checkout still `a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a`. Protected untracked PCE12 audit and external backup SHA256 `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab` must not be overwritten or cleaned.

Required eventual remediation through reviewed **GitHub-first** integration/build, not a local Client hotfix: reconcile branch governance conflicts; derive explicit complete release/asset manifest and versioned content hashes; staged tests **before** live changes; fail-closed verified rollback/atomic promotion; independent runtime-loaded extension attestation and exact-once ChatGPT role receipt tests. This is future planning, not authorization for live deployment during strict grading.
