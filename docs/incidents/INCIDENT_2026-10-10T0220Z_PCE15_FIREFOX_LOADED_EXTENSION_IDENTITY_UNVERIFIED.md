# Incident — Firefox loaded-extension identity remains unverified — 2026-10-10T0220Z

**Status: OPEN.** Release blocker: independent loaded-code and originating-tab identity (G16) remain unverified; no evidence of compromise and no proof the relay extension is absent. Broader release status **Grade F / RELEASE BLOCKED**.

## Evidence actually observed

- PCE15.030 proved reproducible, in-memory five-asset extension ZIPs from source main, development commit and Client. All three pairwise builds deterministic, five members, zero old backups, ZIP CRC PASS, but each differs from existing Client XPI `dist/gpt-windows-relay-0.3.17.xpi` SHA256 `18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8`. A deterministic archive is NOT a signed or installed extension. Main, dev and Client contain different code versions while using persistent manifest version 0.3.17.
- PCE15.031 found all 17 static content feature strings present in GitHub main, development, Client and historical XPI; source byte digests differ. `tabs.query({active:true,lastFocusedWindow:true})` in main does NOT by itself require broad `tabs` permission. The two observed main `tab.url` references are `port.sender.tab.url` metadata accesses; their authorization and semantics have not been proven by live Firefox tracing. Do not invent a permission failure.
- PCE15.032 found all 19 tested static ownership/conversation-isolation and operation-cursor guard patterns in main/development/Client, but 0/19 in existing historical XPI. Five ownership helper sections have matching hashes in main/development, different Client hashes, and absent counterparts in old XPI. Static presence/absence does not establish which worker Firefox actually loads or whether guards execute on every path.
- PCE15.033 examined OS process metadata for 20 Firefox processes without explicit `-profile` flags. Two discovered Firefox profiles: one no extensions.json; the other 19 addon registrations, none matching the canonical relay ID `gpt-windows-relay@local` or checked relay name patterns. The inspected `extensions/` disk candidates were empty of matching relay XPI. Zero verified running-process to profile mappings.
- PCE15.034 checked the same profiles plus `extensions.webextensions.uuids` keys. No relay-matching entry among 31 UUID map keys; one profile had `addonStartup.json.lz4` of 5,775 B and `parent.lock`, neither sufficient proof of active Firefox profile nor loaded runtime. Cache contents were not examined. No unrelated IDs, passwords, profiles' private data, command-line details or browsing history were emitted.

**Interpretation:** The current checked on-disk registration evidence does not identify relay code in Firefox. It does not rule out a temporary about:debugging extension, custom/browser-tooling install, stale profile registry, wrong-profile inference, unpacked module, or other code-injection method. Prior XPI itself lacks sampled ownership guards; this is a potentially material capability discrepancy **if** Firefox actually loads that package. No such assertion has been established.

## Containment and controlled resolution

1. Keep G16 UNVERIFIED, no claim of installed Firefox runtime parity, signature trust, user-role ChatGPT send or safe cross-conversation behavior. Do not interpret process count as window count. No evidence of unauthorized activity, credentials in backups, or exploitation.
2. Follow the canonical GitHub-first operation governance; audit PCE15.030–.034 before ordinal .035. Later read-only investigations should improve profile/process binding and identify loaded extension origin without changing Firefox or browsing user content. Any runtime instrumentation must be separately reviewed and authorized, with protection for tokens and user messages.
3. Once actual loaded code is independently attested, create source-coherent package bill of materials, test-before-promote deployment with rollback, independently test ownership/cursor guards and real user-role sends, and run required endurance. No unilateral Client or Firefox writes; no GitHub Actions (credits exhausted).
4. Preserve 22 existing untracked files as of PCE15.034 (21 prior GitHub documents + protected PCE12 local audit); two PCE12 copies valid SHA256 `3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab`, Client XPI unchanged SHA256 `18a5b12032e106118e160c2842e3cbe5d80a2ce01988584414fe09001e47bbe8`. No destructive git clean/reset/stash, no restoring or overwriting historical evidence.

## Related references

- Detailed five-operation review `docs/audits/AUDIT_2026-10-10T0220Z_PCE15_030_034_CHECKPOINT.md`.
- Compatible next-preflight receipt `docs/audits/AUDIT_2026-10-10T0220Z_PCE15_OPERATIONS_030_034.md`.
- `docs/incidents/INCIDENT_2026-10-10T0206Z_PCE15_XPI_RELEASE_REPRODUCIBILITY_AND_PACKAGE_HYGIENE.md` documents the 10 extraneous .bak files, missing permissions and unreproducible history for existing XPI.
- GitHub audit branch from verified main `dc7e383c65df7434a8a0c01eb2f0286ae9aa1a7b` is docs-only. No CI workflow requested.

**Incident OPEN — G16 and product release BLOCKED.**
