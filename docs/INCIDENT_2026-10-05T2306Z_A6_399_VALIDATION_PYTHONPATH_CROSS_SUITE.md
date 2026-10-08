# Incident — A6.399 cross-suite PYTHONPATH contamination

**Class:** INCIDENT / VALIDATION HARNESS  
**Timestamp:** 2026-10-05T2306Z  
**Operation:** `PCENG-A6.399-deploy-consumer-recovery-supervisor`  
**Consumer r29 HEAD under test:** `7a422225b7a5a928658249508c259e39caf3dfe9`

## Result

The consumer suite completed first and passed: **69 tests, OK**, including the independent recovery-supervisor tests.

The subsequent Windows-relay suite failed during discovery because the validation command had set `PYTHONPATH` to `consumer` and did not change it before discovering `windows-relay/tests`. `test_consumer_mission_queue.py` therefore could not import top-level `windows_relay`.

This is a validation-harness environment error, not evidence of a product regression.

## Correction

Run the relay suite with `PYTHONPATH=<repo>\windows-relay`, then continue package construction only on PASS. A6.399 remains COMMAND_FAILED and must not be relabeled as an end-to-end deployment pass.
