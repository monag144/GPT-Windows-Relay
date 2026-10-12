# Windows Relay — Single Development Build and Release Policy — 2026-10-11

**User directive (authoritative):** There is **one integrated Windows Relay development build**. It contains the **relay/backend, the operator HUD, the browser integration, and One-Click Go**. Development work stays in that single build. **Once development is complete and accepted, re-release from the same tested build.** Do not maintain separate competing developmental programs.

## One build, one operator experience
- Exactly one authoritative development source/build and, once activated, one live relay backend, one HUD, one One-Click Go entry point, and the matching extension integration.
- One-Click Go must start/reconnect the unified application rather than spawn a second backend, watchdog or HUD. START / STOP / RESTART / OFF / KILL remain distinct operator HUD controls; authenticated ARM is an internal permission/quiescence state, not an additional HUD button.
- Do not develop separate 'new', 'current', 'active', 'candidate' or 'consumer' Windows Relay application trees that claim simultaneous authority. Deprecated Prototype snapshots and old Client/runtime trees are historical provenance or rollback only, not alternative active builds.
- Retain backup files and prior installations for controlled rollback without starting a second active competing installation. Preserve authentication, persistent queue/results, STOP, ownership and exact-once protections while migrating.
- Use `monag144/GPT-Windows-Relay` only, not the retired Termux repository. The single integrated canonical source is the `windows-relay/` tree: `windows_relay.py` backend, `hud.py` HUD, `extension-persistent/` integration source, and `START-GPT-WINDOWS-RELAY.bat` One-Click Go. Do not promote historical duplicate paths as release sources.

## Development now versus release later
- This is **development**, not a public or production re-release. Do not create a separate product build as a workaround during engineering.
- Complete live deployment identity verification and functional/STOP/security tests first. Successful GitHub commits, file hashes, Python syntax checks or a staged folder are **not** loaded-runtime or production acceptance evidence.
- Release and package the same approved integrated build **only after development is explicitly finished and acceptance is satisfied**. Preserve a recorded Git commit, verified package hashes, deployment/rollback method and browser-extension provenance.

## Current PCE17 deployment caveat
- **Desired policy** is a single development build. **Last actual live evidence** from `PCE17.011` (2026-10-12 01:24 UTC) shows the old nested `windows-relay/runtime/windows_relay.py` still owns port 8766 (PID 7464) and the old `runtime/hud.py` runs as PIDs 1924/3340. The canonical integrated `windows-relay/` root is staged, but **not proven activated**.
- Pending October 4 Chrome missions were user-authorized and cleared in `PCE17.009` (0 pending); rollback snapshot `PCE17.006` contains 2,628 verified files. Neither this policy nor a GitHub note changes the actual running process.
- `PCE17.012-independent-cutover-worker-probe` was issued and its native result is outstanding at the time of writing. Do not reuse its ID or assume a successful scheduler handoff.
- Until a controlled migration positively verifies the full live canonical paths and extension/HUD ownership, state plainly that the **legacy build remains the running implementation**. Do not present any re-release as done.

## Operator interaction
- Prefer commands delivered by the existing relay. Interactive PowerShell paste is unreliable for this operator; for self-terminating handoff actions prefer a verified independent `.cmd`/`.bat` or independently run scheduled helper, preserving readback logs and rollback.
- Do not force the operator to reinstall the Firefox extension or run manual PowerShell absent necessity. Respect one-off operator-controlled handoffs; automatic chat/agent switching remains retired.

## Precedence and references
User directive > exact verified live process/loaded-extension evidence > dated GitHub documentation > historic snapshots.
See `docs/handoffs/WINDOWS_RELAY_PCE17_LEGACY_TO_CANONICAL_DEPLOYMENT_STATE_2026-10-11.md`, `docs/roadmap/WINDOWS_RELAY_MISSION_AND_PRIORITIES_2026-10-09.md`, `docs/facts/WINDOWS_RELAY_OPERATING_SAFETY_2026-10-09.md`, and `consumer/control_harness.py`.
