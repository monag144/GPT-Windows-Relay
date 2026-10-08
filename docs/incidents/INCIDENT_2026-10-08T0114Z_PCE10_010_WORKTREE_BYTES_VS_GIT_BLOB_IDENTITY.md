# PCE10.010 working-tree bytes vs Git blob identity incident — 2026-10-08T0114Z

## Observation

PCE10.010 failed before tests or live staging while verifying the 42-entry migration-evidence manifest.

The first preserved historical file had manifest Git blob SHA:

`dc25feff024293c2bade60bd27a2a43ee03b9444`

but hashing the checked-out Windows working-tree bytes as a synthetic Git blob produced:

`5544755a11841cc43fd3834d41c22df691008d17`.

The repository has no root `.gitattributes` file defining checkout normalization behavior.

## Classification

**MIGRATION-EVIDENCE VERIFICATION HARNESS DEFECT**

The manifest was generated from committed Git tree/blob identities, but PCE10.010 verified checkout bytes. Those are different domains: working-tree filters or line-ending conversion may alter checkout bytes without changing the committed Git object.

## Safety boundary

The failure occurred before targeted tests, full suites, diff classification, or live staging.

No source/runtime/live mutation was performed by PCE10.010, and no rollback is required.

## Corrective rule

1. Migration provenance is defined by committed Git object identity.
2. Verify each manifest entry against the committed blob at `HEAD:<destination_path>` (or another explicitly named treeish), not by synthesizing a blob hash from working-tree bytes.
3. Working-tree cleanliness remains a separate gate.
4. A migrated evidence file is eligible for whitespace exemption only when its committed blob SHA exactly equals the manifest entry.
5. Any edit to the committed file changes its blob SHA and automatically removes the exemption.
