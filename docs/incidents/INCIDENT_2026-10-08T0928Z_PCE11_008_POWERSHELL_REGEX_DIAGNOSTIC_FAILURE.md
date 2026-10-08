# PCE11.008 — PowerShell path-regex failure

Observed 2026-10-08T09:27:55Z–09:27:57Z. Status **OPEN**, pending PCE11.009 acceptance.

## Facts
Unique action `PCE11.008-precise-live-process-identity-verification` returned `COMMAND_FAILED`, exit 1. PowerShell rejected `(?i)\Client\Relay\` as an invalid regular expression (unrecognized escape \C). The generated Python command also emitted an invalid-escape SyntaxWarning. PowerShell produced no usable JSON, triggering Python JSONDecodeError. Previous topology evidence was read but not updated. No STOP, process termination, Firefox control or live-source mutation occurred.

The prior PCE11.007 result was successfully saved but response display truncated after the first four PID descriptions. The complete evidence remains at `Client/Relay/bin/PASSIVE_TOPOLOGY_2026-10-08T092500Z.json` (SHA256 `735cea44ba871da2e11074f38dfedf4b3e79c52f414416b0ff020d5bbf75856e`).

## Smallest correction
Create a GitHub-reviewed source helper for PCE11.009 using PowerShell literal case-insensitive substring matching, **not** unescaped regex, and -EncodedCommand to protect Python/PowerShell quoting. Require nonempty valid JSON arrays and current PID/creation-time evidence before making duplication conclusions. Keep printed evidence bounded and redact full process command lines and sensitive configuration.

## Unchanged safety gates
No process clean-up before exact live ownership, STOP semantics and rollback proof. Current historical source candidate checks 19/19 jobs passed at PCE11.004, but are not current live-runtime qualification. This incident must appear in the audit before PCE11.010.
