# PCE10.003 ordinal escape and duplicate override incident — 2026-10-08T0018Z

## Observation

PCE10.003 reached the canonical Windows clone, positively read the required Harness v3 / TODO / roadmap files, and then failed closed in targeted source tests before any live copy or restart.

Three targeted failures shared one cause family:

- `engineering_operation_ordinal("PCE10.005")` returned `None`;
- the five-turn audit reminder therefore did not fire for `PCE10.005`;
- the rotation source assertion expected an over-escaped JavaScript regex literal.

Inspection additionally found two definitions of `operationOrdinal(id)` in `extension/service_worker.js`; the later legacy function overrides the earlier engineering-aware function.

## Classification

**SOURCE GENERATION / ESCAPE CONTRACT DEFECT + DUPLICATE FUNCTION OVERRIDE**

No live relay file was mutated because the targeted test gate failed before the live-cutover section.

## Reflection

The previous regex-generation work repeated the exact metacharacter hazard already documented by operational rule 14: source regex text was authored through layered string escaping without a structural single-definition assertion.

The smallest corrective change is:

1. fix the Python raw regexes to use single regex escapes;
2. remove the duplicate legacy JavaScript `operationOrdinal`;
3. correct the source-text test to assert the literal JavaScript regex;
4. add a structural assertion that exactly one `operationOrdinal(id)` definition exists.

## Acceptance

Re-run the targeted harness/protocol/rotation tests and language parse gates. Do not stage the live reminder until they are green.
