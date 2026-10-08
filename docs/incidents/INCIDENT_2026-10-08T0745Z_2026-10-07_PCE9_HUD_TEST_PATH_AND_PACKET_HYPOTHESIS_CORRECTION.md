# Historical record preserved — 2026-10-08T0745Z

﻿# Incident / correction: HUD test path + OP002 packet hypothesis

## HUD test harness
Directly executing `windows-relay/tests/test_hud.py` places the tests directory on Python import search path, causing `import hud` to fail. This is a harness invocation defect.

## Packet-rejection hypothesis correction
`validPacketBody()` checks version, platform, action, and id. It does not whitelist/reject extra fields. Therefore the presence of `owner_claim` or `timeout` in OP002 is not, by itself, evidence for its rejection. Do not modify packet schema based on that hypothesis.

## Rule
Falsified hypotheses must be logged and abandoned. Future rejection work must use actual bridge/runtime rejection evidence.
