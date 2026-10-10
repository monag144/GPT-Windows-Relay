# Incident — Incomplete extension release contract and unreproducible XPI — 2026-10-10T0206Z

## Observation and reproducible evidence

**Status: OPEN / release integrity FAIL / not established as a security compromise.**

PCE15.025 found the current temporary extension (v1.1.0) has five statically required manifest/popup assets, but the 38-file sync-live deployment allowlist excludes both extension/popup.html and extension/popup.js. Both are present on current source and Client disk. Persistent extension (v0.3.17) has five required assets covered by allowlist. The script replaces Client/tests before unit testing with no preserved test directory or explicit atomic rollback.

PCE15.025 and PCE15.026 jointly verified pinned Client archive dist/gpt-windows-relay-0.3.17.xpi SHA256 18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8, CRC PASS and 15 members. Ten extra members are historical .bak copies (seven content scripts, one manifest, two service workers), totaling 63,465 uncompressed bytes, each byte-identical to a file in the Client extension-persistent directory. Both known Python and PowerShell packaging recipes ingest directory contents without explicit exclusions; those 10 files do not exist in the current clean development source persistent-extension directory.

PCE15.026 established 3/5 required XPI active assets (manifest.json, content.js, service_worker.js) differ from both current development and Client; popup.html and popup.js match both. Source and Client manifests match. All versions label themselves 0.3.17, with persistent Gecko id gpt-windows-relay@local; version and name matching do not prove code parity.

PCE15.027 found XPI manifest permissions activeTab/storage only, while both current source and Client manifest declare activeTab/alarms/storage/tabs. Host permissions match. PCE15.028 matched this capability deficit against XPI worker: alarms.clear/create/onAlarm and tabs.get/query/reload occur in current source/Client worker, not in packaged worker (448, 413, 204 lines respectively). These are lexical reference observations, not proof of runtime execution or a Firefox permission error.

PCE15.029 searched reachable local Git history over both named extension trees and found historical exact blob matches for the packaged manifest and both popup files, but no exact blob matches for packaged content.js or packaged service_worker.js. No complete five-active-asset matching candidate Git commit was found among the two candidate commits checked. Missing/unreachable history or out-of-repo transformations remain possible.

## Risk boundary, containment and proposed remedy

Do NOT allege credentials were shipped, malware was installed, someone edited unauthorized code, or that Firefox is running this XPI. Signature verification, runtime-loaded assets, Firefox active profile/policy, service-worker API failures, ChatGPT send and originating-tab identity are UNVERIFIED. Historical backup content was not examined for secrets. Ten packaged backup files are an avoidable artifact hygiene problem regardless of secret presence.

There were no product mutations, package rebuilds, human rescues, Firefox actions, or ChatGPT sends in PCE15.025–.029. Every numbered diagnostic OK/0 preserved the checkout and PCE12 evidence SHA256 3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab; no rollback was necessary. Pinned strict Grade F / RELEASE BLOCKED, 11/28 evidence gates passing (39.29%); G26 0/60, G27 0/2.

Proposed source-first remediation, NOT authorized to deploy from this incident: review a five-asset persistent manifest and temporary extension popup dependencies; implement a deterministic package whitelist with no .bak files; assert every package member and manifest permissions against source SHA; test before atomic/rollback-capable promotion; validate signed Firefox installation and exact loaded identity, independent STOP/exact-once send and endurance. Preserve all unclassified Client-only files and earlier historical evidence. Avoid GitHub Actions reruns while credits unavailable.

Incident overlaps prior package/deployment-atomicity report in docs/incidents/INCIDENT_2026-10-10T0136Z_PCE15_RELEASE_XPI_AND_DEPLOYMENT_ATOMICITY.md. Detailed operation audit: docs/audits/AUDIT_2026-10-10T0206Z_PCE15_025_029_CHECKPOINT.md. No PCE15.030 until verified GitHub checkpoint and installed preflight.
