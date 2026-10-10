# D&D Windows migration action 036 source-inspection syntax incident — 2026-10-10

## Receipt
Action `DND-WINDOWS-20261010-036-TARGETED-BYOK-SETTINGS-SOURCE-INSPECTION` returned COMMAND_FAILED, exit code 1, 2026-10-10T21:03:02Z. The Windows Python interpreter rejected its single-string `-c` command before any script execution: SyntaxError at line 39, a regular-expression source line containing an unescaped quote inside a raw double-quoted string:

`s = re.sub(r"(?i)(api[_-]?key|bot[_-]?token|secret)(\\s*=\\s*)['"][^'"]+['"]", ...)`

The closing `"` inside the character class terminated the Python string literal prematurely. Script-level preflight, source reads, or mutations did not happen. This is a **command-generation defect**, not evidence of a D&D feature regression. Do not replay operation ID 036.

## Prior user-verified evidence
Operation 035 read the saved op032 campaign-creation failure traceback without running tests. `tests/test_pr15_7_campaign_creation.py::test_free_byok_and_premium_access_are_operational_not_campaign_truth` fails at line 227 when `campaign_generation_access(settings, mode="byok", owner_telegram_id=10)` calls `ApiCredentialStore(settings.api_credential_store_path).list_for_owner`. The store enters `_prepare`, where Windows helper `protect_directory` rejects an ACL with unexpected entries. The first eight tests passed. No evidence yet of what settings path was used, whether the parent directory existed before the test, or why its ACL has extra entries.

## Recovery
Use a new unique operation ID 037. Perform an independently syntax-validated *read-only* diagnostic of only test's BYOK section, inference-access code, `ApiCredentialStore._prepare`, Windows helper `protect_directory`, and source definitions of `api_credential_store_path`. Avoid complex quote-sensitive regex entirely; at most simple `sk-[A-Za-z0-9_-]{10,}` redaction, or redact lines containing key-assignment text. Report narrowly bounded output to prevent relay truncation. Verify git branch `fix/windows-python313-utf8-20261010` at `6bcc567ab75b62c2870c99319dcfc550fdd7823d`, known untracked `cmd.exe`, snapshot source SHA `93ab3c55bf61f98870ec15b2c386b84cb44c2dd2fce1426dada53478e2d20fba`, Windows helper SHA `aabbdd834adcddc983ef8471b24a53dba42c61eb372ec08b7e900dbea1a71b49`, archive SHA `0d0324d3b5fe9526d61285b071b699c4185760a398415c15b4c10aff6a75facc`. No live bot, campaign DB or credentials. Once root cause is established, apply only a narrowly justified change with a backup; do not weaken fail-closed ACLs to make test pass.

This incident is task-scoped documentation in canonical monag144/GPT-Windows-Relay, not a PCE action or Relay Client implementation change.
