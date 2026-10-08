# Incident — A6.399ay visible result but ChatGPT turn remained active

Timestamp: 2026-10-06T0230Z  
Reported by: Director  
Scope: relay watchdog / completion semantics

## Symptom

The relay result/return message became visibly available, but ChatGPT continued the assistant turn for multiple minutes before finally terminating. This delayed the next operation and looked like a relay hitch even though result delivery itself had succeeded.

## Classification

This is distinct from:

- result not delivered;
- browser disconnected;
- action still executing;
- idle browser age;
- ordinary model generation.

It is a post-result generation-finalization stall.

## Requirement

The lifecycle/HUD must expose a distinct bounded state such as `WAITING FOR GPT TURN END` after a visible relay result starts the next assistant turn. If meaningful generation does not terminate within the bounded watchdog while the visible content is stable, emit a dedicated post-result-turn-stall event, capture a screenshot automatically, and enter recovery. Do not resend or re-execute the already-completed Windows action.

## Agent 7 acceptance

Reproduce using a controlled delayed-finalization case and prove:

1. exact-once Windows execution remains intact;
2. HUD distinguishes visible result from assistant-turn termination;
3. timeout creates an incident event and screenshot;
4. recovery does not duplicate the prior packet.
