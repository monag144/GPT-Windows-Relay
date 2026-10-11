# PCE16 HUD controls backlog — 2026-10-10

Development queue only; do not implement or deploy in this consolidation task.

Preserve the five installed Client controls unchanged: START, STOP, RESTART, OFF, KILL.

Queue visible, guarded controls:

- RETRY: recovery only, distinct from FORCE, with no duplicate side effects.
- FOCUS CHAT: focus the exact verified conversation.
- SELECT CHAT: select the intended Firefox conversation.
- CLAIM / CONNECT: explicitly bind and confirm ownership.
- FORCE: reinspect only an eligible packet in the verified conversation; never bypass STOP, ownership, authentication, or duplicate suppression.

Display bound conversation, focused tab, last FORCE outcome, scanner freshness, ownership, and reasons disabled actions cannot run. Do not add an independent ARM control or revive automatic agent switching. STOP/OFF/KILL remain dominant.
