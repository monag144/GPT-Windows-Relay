# Repair and restart evidence

Date: 2026-10-10

- Before restart: two Client `windows_relay.py server` processes were present and no listener owned TCP 8766. Supervisor history showed repeated paused exits and duplicate-supervisor detection.
- Action: used the installed Client `relay-control.ps1 restart` controller. No source replacement or Firefox reload was performed.
- After restart: one backend listener owns `127.0.0.1:8766`; unauthenticated `/status` returns HTTP 401, confirming the authentication gate is present.
- Offline regression: 403 tests passed (`python -m unittest discover -s windows-relay/tests -p test_*.py -q`).
- Installed-source backup and hashes: `Backup/repair-20261010-211713/`.
- Firefox content-script injection, background-port authentication, and native round-trip remain unverified because the existing ChatGPT tab was not refreshed and no operation was replayed.
- PCE16.035, PCE16.036, and PCE16.037 were not replayed.

This remains WIP and is not a stable release.
