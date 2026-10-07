# Incident: OP086 persistent worker pairing overwrite
OP086 full-suite containment proved the temporary and persistent Firefox service workers are not interchangeable. The persistent worker has independent local-token pairing and does not own the temp worker's delivered-operation rotation subsystem. Later rotation work must patch only the architecture that actually owns the behavior.
