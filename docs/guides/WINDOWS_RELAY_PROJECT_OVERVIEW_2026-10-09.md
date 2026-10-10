# Windows Relay project overview — 2026-10-09

Project: `monag144/GPT-Windows-Relay`. Source checkout: `...\Downloads\Dev\GPT\GPT-Windows-Relay`; separate live Client installation: `...\Downloads\Dev\GPT\Client\Relay`. Never route Windows operations through historical `monag144/GPT-Termux-Relay`.

The system integrates ChatGPT messages, a browser extension, authenticated localhost Windows command execution, results returned to the conversation, Windows controls, and an optional consumer app. These components must be evaluated separately: source presence does not prove what the browser loaded.

**User-facing starting points:** repository root `README.md` for navigation, the date-based documentation index, and `docs/guides/WINDOWS_RELAY_ACTION_SANDWICH_2026-10-09.md` for the relay message format.

**Safety correction:** neither durable reservation nor exactly-once side effects may be claimed unconditionally. Isolated PCE15.043 and PCE15.047 tests showed concurrent reservation and old-identity eviction/replay gaps. Production remediation has not been established by those tests. See `docs/facts/WINDOWS_RELAY_OPERATING_SAFETY_2026-10-09.md`.

**Browser delivery/release:** a historical signed persistent extension gate remains open in the last proven acceptance snapshot. Verify actual loaded Firefox add-on and browser ownership before asserting continuity or release readiness. Old README setup instructions may describe development-only add-on behavior, not a validated production deployment.

**Agent handoffs:** the established user-requested one-shot `Run-Copy-Contents.cmd` is the allowed agent/chat handoff method; all other automatic or experimental switching is held by the dated user policy. Normal same-chat recovery and safety controls are separate and must not be disabled merely because switching is paused.

Historical detailed README (including now-disproven exact-once claim): `windows-relay/README.md` at GitHub commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8`. This overview is intentionally not a substitute for an installed-source inspection or a signed release.
