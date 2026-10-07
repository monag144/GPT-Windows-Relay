# Incident: forensic output explosion

OP005 exited successfully but violated its bounded-output objective.

## Cause
The runtime recursive scan traversed historical saved-result JSON. Those files embed prior stdout fields, including very large historical outputs, so a single regex match could emit megabytes.

## Permanent harness rule
Do not recursively grep relay result archives or live-backup captures when extracting evidence. Prefer tracked source via `git grep`. Bound match count and truncate every emitted line. Read a specific saved result only by structured scalar fields unless its stdout size is already known safe.

## Product impact
None. No production runtime code was changed.
