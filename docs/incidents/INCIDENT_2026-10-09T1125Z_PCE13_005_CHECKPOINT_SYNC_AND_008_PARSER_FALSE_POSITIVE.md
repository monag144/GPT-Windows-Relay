# Incident — PCE13.005 checkpoint sync and PCE13.008 diagnostic false positive — 2026-10-09T1125Z

## Observed symptoms
- PCE13.005 returned GOVERNANCE_BLOCKED before reservation or execution: `audit checkpoint missing before PCE13.005: PCE13.000-.004`. The audit existed on GitHub but not yet in the canonical Windows checkout.
- PCE13.008 targeted regression suite passed (33 tests), but an inline PowerShell diagnostic returned `PS_PARSE_EXIT=2` and `POWERSHELL_PARSE_ERRORS=1`. The tool command did not emit the error's source extent, so this was not proof the rotation worker was invalid.

## Evidence and containment
- PCE13.000–.004 audit committed on GitHub as `b647a8698f97e09c3f85deae3423244391fe6610`, then recovered with separately identified `GOVSYNC13-AUDIT-RESTORE-20261009-01` operation. This command verified exact origin and target SHAs, six-file allowlist, and blob SHA, backed up the untracked PCE12.010–.014 audit byte-for-byte, and ran `git merge --ff-only`. Afterward `engineering_preflight(root,5,series=13)` returned accepted. HEAD `b647a8698f97e09c3f85deae3423244391fe6610`. Live runtime unchanged.
- PCE13.008: `SOURCE_CONTRACT` six guards true; `TARGETED_EXIT=0`, 33 tests OK. Its PowerShell inline script invocation produced an error count without identifying a source location.
- PCE13.009: independent, correctly targeted PowerShell `Parser.ParseFile` and `Parser.ParseInput` checks on current local `windows-relay/agent011_current_tab_new_chat.ps1` both returned exit 0 and zero parser errors. Local worker raw SHA256 `e8560fd276f20f9ae5e213e2a1b6c64fc739f4f724cf7bcb79006b1bbb37cb51`.
- No browser navigation, paste, Send, runtime deploy, or source edits occurred during the diagnostic operations.

## Root cause and resolution classification
- Checkpoint: publication to the canonical remote was not equivalent to a local audit checkpoint. The pre-dispatch governance check behaved correctly. Corrected by a constrained, verified audit synchronization preserving all PCE12 evidence.
- Parser: the `.008` inline diagnostic was faulty or insufficiently specified; `.009` proves the named worker parses with the correct invocation. Do NOT patch the working source or weaken tests in response to the `.008` false positive.
- Underlying separate PCE12 handoff failure remains unresolved: `.018` navigation URL verification failed and `.019` stopped with `COMPOSER_NOT_EMPTY_ABORT`; a composer count is not a verified handoff delivery.

## Preventive controls
- Publish each five-slot audit to GitHub and bring it into the local exact-source checkout BEFORE attempting the boundary ordinal. Use a uniquely identified, reversible governance sync rather than bypassing blocked operations.
- Parse PowerShell from an explicit absolute file path passed through an environment variable or safe argument binding; report structured `ErrorId`, `Extent` and `Message`. A syntax failure without source extent is inconclusive.
- Preserve real unsent drafts; observe accessibility editor value in privacy-preserving classification before any new paste. No old-worker replay, no status inference, no live mutation before test/STOP/identity/rollback gates.

## Status
Checkpoint **RESOLVED**; PowerShell syntax false positive **RESOLVED**. PCE12 handoff delivery **OPEN**. No fresh end-to-end live canary or release promotion claimed.
