# Script-only agent handoff — 2026-10-09

The Director permanently retires automatic agent/conversation switching as a product feature. This decision **supersedes the earlier temporary hold** in `docs/policy/POLICY_2026-10-10T0331Z_MANUAL_AGENT_HANDOFF_AND_AUTOMATED_ROTATION_HOLD.md`, whose historical original remains unchanged. The decision is dated by Pacific-local calendar day; later Git commit chronology resolves same-day ordering.

**One sanctioned method:** when the Director expressly requests a handoff, the source engineer identifies its own PCE series from chat/project evidence, increments by one, prepares `Client/Relay/test/Copy Contents.txt`, verifies the file and runs the preexisting `Run-Copy-Contents.cmd` once. The companion `Copy-Contents-To-ChatGPT.ps1` operates the existing Firefox session and submits using Enter. Confirm the submitted text appears in the actual new conversation; a launched process, new tab, or composer draft is insufficient. In ambiguous delivery states do not blindly send again.

The source engineer need not independently select or hardcode the next engineer in the launcher: e.g. PCE16 -> PCE17, PCE17 -> PCE18; the next ordinal resets to `PCE<n>.000` after a confirmed new agent. The prepared handoff must identify the derived target clearly so the recipient does not assume the prior series.

**Retire and prohibit use as handoff routes:** relay operation-count/scheduled rotation, Firefox content-script navigation/rename and send, watchdog/supervisor-driven fresh chats, out-of-band UIA/clipboard/tab scripting for successor creation, headless/browser test fallback rotations, and the experimental replacement-switching architecture. Existing shared UIA/clipboard/tab tools are only *suspended for switching*; do not rip them out of necessary ordinary same-chat relay operations, STOP, or recovery.

No automatic switching at ordinal 100. `consumer/control_harness.py` retains strict finite series limits, documented attempts, audit cadence, safety gates, and requires explicit one-shot manual handoff after exhaustion. Do not bypass a cross-conversation owner guard or relaunch an uncertain older packet.

**Archive:** `windows-relay/bin/AGENT_SWITCHING_RETIREMENT_2026-10-09.md` documents retired approaches, concrete source at pre-retirement SHA `77bee0a6b24e9bc7360f4a09505da4d6d1e8047c`, incidents, and retained/shared implementation boundaries.

**Deployment caveat:** GitHub-only source changes are not proof that the installed Client or Firefox add-on stopped rotating. That requires a separately authorized verified rollout. Existing PCE15 exact-once defects and Grade F release block remain.
