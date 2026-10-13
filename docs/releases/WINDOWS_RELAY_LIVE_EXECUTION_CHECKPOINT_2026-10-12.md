# Windows Relay live execution checkpoint — 2026-10-12

**Date:** October 12, 2026, Pacific time (the Git tag was created on October 13 UTC). The date belongs to the **verified operator acceptance event**, not the age of a directory, document title, or local filesystem copy.

## Verified GitHub provenance

- **Repository:** `monag144/GPT-Windows-Relay`, canonical Windows Relay Git source `windows-relay/`.
- **Development branch at the time of acceptance:** `wip/windows-relay-rebuilt-resynced-2047-101026`. This is a branch name, not a command to switch away from a working checkout.
- **Immutable operator-pushed annotated tag:** [`windows-relay-v0.3.18-live-verified-20261012`](https://github.com/monag144/GPT-Windows-Relay/tree/windows-relay-v0.3.18-live-verified-20261012).
- **Tag target verified through GitHub tag-object API:** `f00307494a83338d29b4c35dd6264e71fa142dbd`. Tag creation time: 2026-10-13T00:50:51Z.
- **Canonical extension source:** `windows-relay/extension-persistent/`. Manifest version `0.3.18`, Firefox ID `gpt-windows-relay@local`. The separately scoped `windows-relay/extension/` is *One-Click Go*, not an alternative GPT Windows Relay runtime.
- **Backend/source set:** `windows-relay/windows_relay.py`, `hud.py`, `run.ps1`, `relay-control.ps1`, `relay-watchdog-loop.ps1`, and `START-GPT-WINDOWS-RELAY.bat`. Launcher uses its own directory, not the older `GPT/Client/Relay` tree.

## Native operator verification

The operator fast-forwarded the checkout through `9cf9d6697edcabf45fe0c8226805447cd3b7c07e` and supplied native Windows test output:

| Focused suite | Native result |
|---|---:|
| Authenticated issuance, owner, and tab rejection | **8 / 8 passed** |
| Isolated HTTP owner consent/rejection and once-only mocked execution | **4 / 4 passed** |
| Node mock running the persistent Firefox worker transport | **1 / 1 passed** |
| **Total focused verification** | **13 / 13 passed** |

The operator loaded and confirmed the same canonical unpacked extension as `v0.3.18`, paired/armed it and returned a genuine completed `[GPT_WINDOWS_RESULT]` envelope for `PCE17-CANARY-20261012-002`, session `pce17.1`, read-only PowerShell. Receipt: `status=OK`, `exit_code=0`, `duration_ms=1680`, empty stderr; stdout began `GPT_WINDOWS_RELAY_CANARY_002_OK` and reported Windows PowerShell **5.1.19041.2364**. Output was not truncated, and the required sandwich reminder was included. **Real authenticated ChatGPT → Firefox → canonical Windows backend → PowerShell → result delivery worked for this test.**

The supplied receipt does not separately prove that a native operator YES/NO prompt was displayed, though the approved-binding path is covered by isolated tests.

## Engineering versus operational evidence

**This is the known-working checkpoint, not a blanket certification.** The 13 focused tests and one real canary do not establish a green full-project unit suite, persistent browser restart endurance, all STOP/owner replay negative cases, all job-application workflows, or cleanup of unique untracked local runtime material. Source changes made **after** the pinned commit must be separately tested before they are called verified.

No local backup is permitted. GitHub history and the annotated tag preserve tracked nonsecret code only. Do not create local snapshot/rollback/secondary runtime directories. Existing unique local credentials, journal/state, profiles and untracked work cannot be recovered from a public GitHub commit and must not be deleted without user review.

## Dated-record precedence

When an older review, roadmap or README states the Client install is still the deployed path, that Firefox loaded identity is unknown, or that no live canary has ever worked, treat it as a **historical observation as of its own date** rather than the October 12 acceptance state. Older facts and incidents should not be erased or rewritten; newer verified evidence supersedes the old status claim. Repository default `main` is a separate branch, **not** the published canary tag and **not** the automatically selected delivery target.
