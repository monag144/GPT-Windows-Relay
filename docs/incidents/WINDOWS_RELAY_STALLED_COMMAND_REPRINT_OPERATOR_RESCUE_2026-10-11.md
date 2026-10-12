# Windows Relay stalled command pickup — operator workaround reported — 2026-10-11

## User observation
After PCE17.012-independent-cutover-worker-probe was issued, the operator reported that reprinting a Windows relay action in a **new assistant response** may cause the stalled relay to resume. The reported recovery mechanism is **hypothesis, not confirmed**. No native PCE17.012 result has yet been provided in this conversation. Do not infer its execution status.

## Context
Last positively verified live process: PCE17.011 confirmed legacy nested runtime PID 7464 on 8766 and legacy HUD PIDs 1924/3340. This is not the staged integrated development build. Earlier HUD screenshot showed `STALLED`; at that moment backend displayed ONLINE/ARMED and 0 pending missions. Legacy checkpoint false positives were observed at PCE17.005 and PCE17.010, and PCE17.011 subsequently passed.

## Safety implications
Repeatedly emitting **the same action ID** when actual backend execution is uncertain is not a valid recovery method: request detection, execution and assistant result delivery are distinct states, and existing duplicate/replay safety gaps are unresolved. Treat issued PCE17.012 as consumed pending evidence. Use a unique new operation ID for any new safe bounded attempt, check original execution state when possible, and avoid replay of side-effectful commands. Never clear processed journal or bypass owner/STOP/auth checks to unstall.

## Permanent work item
`docs/roadmap/WINDOWS_RELAY_TASK_BACKLOG_2026-10-09.md` new P0 section **stalled scanner and user rescue**: instrument command discovery, executor vs delivery, bounded same-chat reinspection, recovery without operator rescues; verify live recovery, exactly-one execution and exactly-one visible result under streaming, refresh, extension reload and temporary disconnect; maintain one integrated development build.

## Operator experience
Interactive PowerShell copy-paste can mangle order. Operator prefers relay or CMD; for self-terminating transitions use an independently verified one-shot worker and durable result report. Never assume staged source is the active runtime.

## Expected next observation
Capture actual native receipt for the newly issued, distinct-ID safe probe or prior PCE17.012. Record the result and timing before claiming recovery. No backend cutover was performed by this incident documentation.
