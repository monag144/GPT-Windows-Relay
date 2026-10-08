# PCE011 timestamp/size documentation cleanup ledger — 2026-10-08T0756Z

## Outcome and exact scope
- Canonical Windows working branch: `pce11/one-click-go-recovery-and-doc-hygiene`. Historical Git objects and intentional safety branches preserved. No Windows relay/live files were modified during documentation cleanup.
- **Original content entries migrated:** 40 legacy documents now have NEW timestamped canonical files. The old paths remain compact marked `PCE11_TIMESTAMP_COMPAT_POINTER` aliases to keep prior audit/handoff references working.
- **Code/UX compatibility exceptions:** 13 source-used README/TASKS/operational-document filenames deliberately retain stable names; each has a separate timestamped canonical copy at `2026-10-08T0756Z`. Tests and regular product entry points still find the old paths.
- **Non-document technical file:** `consumer/requirements.txt` is a dependency manifest and must retain its expected fixed name.
- **Oversized documents:** 13 files above 10 KiB in the verified pre-split 275-file-tree descendant (earlier report counted 14 under a different inventory/criterion), including 189,382-byte frozen engineering log. All 13 indexed and segmented into 60 time-stamped parts, with original Git blob SHAs in indices. Source text was concatenation-checked before each change. The original complete Git blobs remain retrievable.
- **Post-migration inventory:** 259 .md/.txt tracked documents (including retained aliases/canonical copies and 60 archive parts), 0 above 10 KiB. Of 54 paths without a full filename timestamp, 40 are pointers, 13 are stable API/UX compatibility names, 1 is `consumer/requirements.txt`. Each of the 53 legacy documentary paths has a timestamped canonical counterpart; only aliases/compatibility entrypoints use older filename shapes.

## Notes on preservation and validation
- No original substantive document was simply discarded to meet the size rule. Part content is verbatim after a new dated fragment heading; original Git object SHAs are indexed.
- Physical historical file names are NOT all erased. Compatibility aliases are intentional; claiming "zero filenames without timestamp" would be false and could break old links and automated governance.
- Some section anchors into an indexed archival document now require following its segment links. References to original filenames remain valid.
- The previous 51/14 counts are not used as final facts; this ledger inventories the actual PCE011 working tree.
- GitHub object/tree size, branch-tip inspection and nonexecution source checks were performed through connected GitHub. Full Windows/Python suites and live runtime/browser canary remain NOT RUN. The accompanying source regression `windows-relay/tests/test_pce11_documentation_contract.py` is intended to prevent future naming/size drift.

## Follow-up
Future agents must use `docs/roadmap/ROADMAP_2026-10-08T0735Z_PCE11_ONE_CLICK_GO_RECOVERY.md` first. Resolve external signed Firefox distribution before claiming Firefox consumer-ready. Keep stable README/operational entrypoints and time-stamped canonical companions rather than breaking backward paths.
