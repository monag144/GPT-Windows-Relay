# Windows Relay mission and priorities — 2026-10-09

**Mission:** provide a reliable, auditable ChatGPT ↔ Windows interaction bridge that minimizes manual copying, debugging and recovery, with explicit operator control and no duplicate side effects. Scope is `monag144/GPT-Windows-Relay` only. This document is a Pacific-local calendar-date snapshot, not a claim of current runtime release state.

## Engineering priorities from the last verified PCE15 evidence

1. **Safety first: exact-once source defects.** PCE15.043 isolated backend reproduced concurrent same-ID claim race; PCE15.047 showed replay after 500 processed records and late outbound-ID collision. The proposed PCE15.049 identity ledger remained synthetic. Atomic durable claim and non-evictable replay tombstone would need a separate authorized implementation, review and crash/concurrency tests.
2. **Prove installed/browser identity.** Last verified product acceptance reported G16 loaded Firefox add-on identity and same-conversation owner behavior unresolved. Source and packaged XPI equality do not establish a loaded extension.
3. **Live delivery and endurance.** Last PCE15 release review reported independent live sends G26 0/60 and unattended endurance G27 0/2; do not upgrade until actual receipts and correct release gates are available.
4. **Browser lifecycle and signed extension.** Full Firefox/browser/Windows login restart acceptance historically depended on persistent signed extension/policy validation. Verify the currently installed artifact before claiming solved.
5. **User experience and product expansion** (Windows HUD, targeted screenshots, semantic UI automation, browser adapters, consumer app, job application helper) remain strategic components. Historical 'complete' checkmarks in an older roadmap are not substitute for reproducible current acceptance.

## Agent handoff constraint

The user has explicitly held **all automated conversation/agent switching** and further work on a replacement system. Only a separately requested manual one-shot launch of the known `Run-Copy-Contents.cmd` remains approved. Stop at the PCE ordinal budget rather than silently auto-rotating. Existing same-chat retry and safety controls are not thereby disabled.

Prior detailed 22 KB roadmap: `docs/windows-relay-mission-and-roadmap.md` at GitHub commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8` (historical; contains older rotation requirements). The latest operation ledger and incident evidence control any later status; never infer progress after handoff solely from this date.
