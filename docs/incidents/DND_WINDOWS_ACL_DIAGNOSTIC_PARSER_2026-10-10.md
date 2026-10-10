# D&D Windows ACL diagnostic parser failure — 2026-10-10

## Recorded failure
DND-WINDOWS-20261010-021-ACL-IDENTITY-VERIFICATION returned COMMAND_FAILED, exit 1. The Windows relay executed the requested Python command, resolved the current user SID, applied a restrictive ACL to a **disposable temporary directory**, and successfully exported that ACL (HARDEN_OK=True, ACL_SAVE_OK=True). The assistant-authored inspector then threw IndexError at `entries.append((role, fields[0], fields[1], fields[2]))`. This is a **diagnostic parsing error**, not evidence of ACL rejection or insecure access rights.

## Cause
The expression `aces = [item.split(';') for item in re.findall(...)]` pre-split every SDDL ACE. The following loop then operated only on `fields[0]`, which was merely `(A`, so `fields[1]` and `fields[2]` did not exist. No actual access-control entry was examined. The saved ACL display from this attempt is not preserved and does not support an ACL acceptance claim.

## Security scope
Changes in this attempt were confined to a temporary test directory created by `TemporaryDirectory`. A context-manager cleanup ran on exception. There is no indication that the real API credential store, game database, local D&D branch at 6bcc567ab75b62c2870c99319dcfc550fdd7823d or production bot was accessed or changed. The underlying import/permission model remains unresolved: PR15.7 candidate relies on Unix-only fcntl, POSIX permission bits, and directory fsync. Do not bypass them or ship a false-privacy fallback.

## Recovery
Never replay 021 or reuse its action ID. Issue 022 as a separate temporary ACL test with an independently self-tested parser: split **each complete parenthesized ACE only once**, demand exactly six semicolon-delimited SDDL fields, normalize user SID and SYSTEM trustee, and report any extra entries or inheritance without claiming security acceptance. Any parse anomaly is a diagnostic result, not a justification for permissive fallback. Avoid logging usernames, credential contents or sensitive files. After verifying ACL semantics, test Windows credential-store behavior in the isolated PR15.7 snapshot, preserving immutable archive and source branch.

This is DND task-scoped incident documentation on canonical monag144/GPT-Windows-Relay main, not a PCE engineering ordinal or Relay implementation change.
