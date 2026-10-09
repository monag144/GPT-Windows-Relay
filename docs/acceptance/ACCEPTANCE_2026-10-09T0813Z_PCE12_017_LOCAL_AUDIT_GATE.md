# PCE12.017 local audit-ingestion acceptance — 2026-10-09T0813Z

The command PCE12.017-sync-verified-github-audit-to-legacy-gate returned Windows Relay EXEC status OK (exit 0), 1082 ms.

## Verified evidence
- Local checkout: canonical Windows repo remote https://github.com/monag144/GPT-Windows-Relay.git; branch pce11/one-click-go-recovery-and-doc-hygiene, rollback HEAD 03c7779268aed2984b8b5f3cea6ff3dbff0f66df.
- GitHub source of compatibility audit: main at commit 0b2905a33d52ca5f8b76ee5cca04d4304e8c8f2f, file docs/audits/AUDIT_2026-10-09T0808Z_PCE12_OPERATIONS_010_014.md.
- Source blob SHA readback and local download proof: 5e8074c46e5bb408e216e3c91b0f40386557425f (4612 bytes, UTF-8).
- File installed at canonical local docs/audits/..._010_014.md, previously absent.
- Local legacy engineering_preflight(repo_root,15,12) returned ok=True, five required control reads and audit checkpoint path matching the installed file.
- Audit SHA256 reported by Windows validator: 3d18d1f3b8b01df51b4b853f46dde1fa142eb335cbc351bcdd6639307e98ccab.
- No relay restart, source file overwrite, or GitHub Actions was involved.

## Scope and remaining issues
This proves the legacy validator accepts the audit for the .010–.014 window, not that the deployed runtime was updated or all future .020/.025 checkpoints are synchronized. The correct long-term fix is authenticated GitHub audit ingestion plus harmonizing the legacy three-positional-argument API with the canonical modern receipt-based harness; avoid bypassing controls.

Next operation at time of acceptance: .018 (the .015 gate block, .016 source discovery, and .017 success all consumed). At .020 complete the 5-operation audit .015–.019 and the nonblocking 20-operation review. Check canonical GitHub harness every turn.
