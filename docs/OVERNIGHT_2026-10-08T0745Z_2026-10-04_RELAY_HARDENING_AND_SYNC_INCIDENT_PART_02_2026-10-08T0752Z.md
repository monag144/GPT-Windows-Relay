# Archived source fragment 2/2 — 2026-10-08T0752Z

- selected browser executable;
- relay backend ownership/port;
- extension/bridge health;
- ChatGPT tab reachability;
- prompt injection capability;
- optional minimal no-op sandwich test when needed.

### 13. Dev/consumer ownership isolation

Development relay and consumer One-Click relay must not silently compete for the same port/state namespace. Add explicit instance identity and ownership arbitration or separate port/state namespaces.

### 14. Updater rollback / known-good release

Before consumer update, retain a known-good package/version. Failed post-update self-test should automatically revert or clearly fall back without destroying the live install.

### 15. Evidence bundle

Every full acceptance run should produce a timestamped evidence directory containing:

- release/revision and Git commit SHA;
- update result;
- chosen browser/path;
- mission journal;
- key telemetry excerpts;
- screenshots at important UI stages;
- packet IDs and result status;
- final PASS/FAIL summary.

This is the source for the requested **photo proof of everything working amazingly**.

## Required end-to-end acceptance run

The feature is not complete until a clean consumer test proves, with evidence:

1. Start from the consumer package/repository state.
2. Pull/update from GitHub through the supported product path.
3. Launch GO.
4. Click/check for update and prove the displayed semantic version **and r revision**.
5. Select a supported browser from the UI.
6. Launch the browser through GO.
7. Submit a natural-language test mission through GO.
8. Verify GO automatically appends the machine-readable relay harness and example packet; the user does not manually type relay instructions.
9. Verify the ChatGPT user turn containing the durable mission ID is present in the authoritative PC conversation.
10. Verify ChatGPT produces a canonical final-response sandwich.
11. Verify scanner accepts it exactly once.
12. Verify backend executes it exactly once.
13. Verify result returns and is confirmed as a ChatGPT user turn.
14. Run a screenshot-producing mission and verify the managed image appears in the conversation.
15. Capture screenshots/photo proof of the major stages and store them in the evidence bundle.
16. Intentionally exercise at least one recovery path (for example a harmless malformed/collapsed simulation) and prove the harness detects it, sends the minimal probe, locks the proven method, and resumes without user intervention.

## Human-intervention budget

Target: **zero unplanned operator actions** after the initial user mission submission.

Any unplanned reload, reopen, manual send, manual copy/paste, terminal operation, extension reload, or physical return to the PC to diagnose a stalled mission is an incident and must be logged.

## Immediate operator recovery for the current sync incident

Until the above redundancy is implemented, when the phone and PC clients diverge:

1. Go to the Windows PC.
2. In the Firefox ChatGPT tab used by the relay, confirm this exact conversation is open.
3. Look for the newest user turn from the phone. If it is missing, refresh the ChatGPT page and reopen this conversation from the sidebar/history.
4. Confirm the newest turn is now visible on the PC before sending anything else.
5. Confirm the compact relay HUD is visible and reports a healthy/ready state.
6. Send one short message from the PC in this same conversation: `PC SYNCED`.
7. From that point, treat the PC conversation as authoritative for the overnight relay mission while the new sync-divergence protections are built.

No terminal or PowerShell interaction is part of this recovery procedure.
