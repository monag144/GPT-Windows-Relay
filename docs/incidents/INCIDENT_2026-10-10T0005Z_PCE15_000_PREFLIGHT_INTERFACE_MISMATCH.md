# Incident — PCE15.000 installed-preflight interface mismatch — 2026-10-10T0005Z

## Trigger and observed effect
PCE15.000 on canonical Windows local HEAD `a431cb6cbb7a5b712e5a5a1cfa022ef1b84ced4a` exited 1 with `BLOCKED: installed preflight differs from GitHub`. It assumed modern `engineering_preflight(series, next_ordinal, ...)`, whereas installed `consumer/control_harness.py` implemented `engineering_preflight(repo_root, ordinal, series=11)`. The initial command stopped **before** protected-hash checking and PCE14.029 receipt search.

## Cause and classification
Operator invocation version mismatch between verified GitHub `main` governance source and the older, deliberately unchanged local checkout. Fail-closed check behaved correctly. Ordinal .000 was issued and consumed, regardless of COMMAND_FAILED; no replay.

## Recovery and proof
PCE15.001 used the actual installed API and returned `OK`, verified two protected PCE12 audit SHA256 values, and located the saved PCE14.029 receipt. PCE15.002 independently reviewed all PCE14.025–.029 receipts. No product source, live Client file, browser focus, clipboard, or user-message effect was changed.

## Prevention and disposition
Use exact installed signature plus GitHub commit-provenance before dispatch; don't substitute a newer API until a guarded source update is explicitly approved. **Incident diagnosed, command invocation corrected; no code fix authorized during grading.** Continue with GitHub-first documentation audit and historical preflight compatibility, not bypass.
