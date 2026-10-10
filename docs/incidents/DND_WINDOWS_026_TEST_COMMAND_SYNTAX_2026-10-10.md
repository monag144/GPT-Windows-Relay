# D&D Windows credential-store smoke test command syntax incident — 2026-10-10

## Observed result
Relay action `DND-WINDOWS-20261010-026-CREDENTIAL-STORE-RUNTIME-TESTS` returned `COMMAND_FAILED` with exit code 1 at 2026-10-10T20:44:43Z. Windows Python rejected the *outer script* at line 93: `SyntaxError: '(' was never closed`.

The fault was in the assistant-authored final safety-print expression:
```py
print('NO_REAL_ENV_OR_CAMPAIGN_DB=', not (root / '.env').exists() and not list((root / 'data').glob('*.db'), flush=True)
```
The intended expression required an additional closing parenthesis on the boolean test before the `flush` keyword. No `OPERATION=026...` print or nested synthetic test output appeared. Python compiles the entire -c script before executing it; therefore this receipt supports **no executed 026 script statements or file mutations**, and provides **no credential-store runtime test result**.

## Prior state
Operation 025 already updated **only the isolated PR15.7 snapshot** `backups/pr157_a1b03ae2/app/services/api_credential_service.py`; its new SHA-256 `a4ffbff503e6f98db6e237c8a47b2dea22b3cabf109fc274a9e887d99151eeff`, original backup SHA-256 `3ebf1faf7ddac0754d8ce7c03e2296e34194d88148460a7b2dde8a8c29c9eb63`. Existing isolated Windows security helper SHA-256 `aabbdd834adcddc983ef8471b24a53dba42c61eb372ec08b7e900dbea1a71b49`. Original GitHub candidate and local committed Windows branch remain separate; no production credential store, campaign DB, bot or deployment touched by 026.

## Resolution protocol
Never resend/reuse 026. Issue next unique DND operation 027 with corrected and offline-syntax-validated Python command. Keep temp-only synthetic credentials, restricted subprocess environment, exact source SHA preflight, unmodified active Git branch checks, and explicitly report gate failures. Qualify actual read/write/replace/update/restart, concurrency, interprocess locking and fail-closed ACL before making any Windows readiness claim. Avoid exposing even synthetic secret contents in output. Record resulting pass/fail receipt and test findings.

Scope: D&D migration incident documentation in canonical monag144/GPT-Windows-Relay/main only; not a Relay code change, not a PCE ordinal, and no autonomous agent switching.
