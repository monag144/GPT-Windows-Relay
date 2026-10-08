# A6.400 rotation packet discovered but never executed

Timestamp: 2026-10-06T0245Z (2026-10-05 19:45 PDT)  
Class: INCIDENT / RELAY DISCOVERY-TO-EXECUTION / AGENT ROTATION  
Branch: `consumer/r29-firefox-offline-tray`  
Operation: `PCENG-A6.400-rotate-to-agent7`  
Disposition: FAIL — Director intervention required

## What happened

The final Agent 6 operation was deliberately numbered A6.400 so the existing 100-operation rotation machinery could be acceptance-tested while handing the work to Agent 7.

Director screenshot evidence shows the ChatGPT assistant turn had completed and the canonical A6.400 packet was visibly present. The HUD showed:

- `DISCOVERED`;
- relay `ONLINE • ARMED`;
- Firefox `ACTIVE`;
- lifecycle `relay_packet_discovered`;
- packet `PCENG-A6.400-rotate-to-agent7`;
- `packet parsed; settling before execution • 7s`.

No execution result for A6.400 was produced. Therefore the packet was parsed but failed to advance from discovery/settle into execution. This is not an inner command failure and must not be recorded as a completed rotation.

## Why this matters

The recovery architecture already says that DISCOVERED which does not advance after settle/reacquire bounds is evidence of a scanner handoff fault. This incident proves the rotation boundary can itself be stranded in that transition. A final-operation handoff cannot depend solely on the same browser-resident path that is being acceptance-tested.

The failure is especially important because the requested fresh-chat rotation is itself a redundancy boundary. If it stalls at DISCOVERED, the system needs an independent supervisor deadline capable of recognizing the missing transition, capturing a screenshot, and using the out-of-band recovery plane without duplicating an already-executed Windows action.

## Required repair

1. Treat discovery-to-execution transition age as a first-class deadline, separate from the approximately five-minute dead-man.
2. When the settle/reacquire bound is exceeded, classify a scanner handoff fault immediately; do not leave HUD indefinitely at DISCOVERED.
3. Capture a screenshot before mutation and attach/present the diagnostic to GPT through the independent recovery path when the primary browser path is suspect.
4. Determine from backend exact-once state whether an action reservation/execution exists before any replay.
5. If no backend execution exists, recover/reacquire and allow exactly one execution. If execution exists, recover result delivery only.
6. Rotation boundaries must have an out-of-band fallback: failure of the A6.400 packet cannot prevent the Agent 7 handoff.
7. Re-run a deliberate 100-operation/fresh-chat acceptance after this transition watchdog is repaired.

## Evidence rule

A6.400 is FAIL. It must not be promoted to PASS merely because the packet was visible, parsed, or because the HUD said Firefox ACTIVE. Acceptance requires the rotation action to execute, the new chat to be created/selected, the dated handoff prompt to arrive there, and the next operation to be A7.1 without Director intervention.
