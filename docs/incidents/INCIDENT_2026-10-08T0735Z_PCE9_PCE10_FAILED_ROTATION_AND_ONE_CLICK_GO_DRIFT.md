# Incident — PCE9/PCE10 operational failure and One-Click GO mission drift — 2026-10-08T0735Z

**Director classification:** PCE9 and PCE10 operational outcomes were failures, although their source contains reusable improvements. PCE7 was comparatively usable. PCE8's auto-rotation to PCE9 was promising but did not yield sustainable unattended operation. These are operational assessments, not claims that every individual source patch failed.

**Symptom:** repeated Firefox tab/extension identity probes, wrong repository commits, overrun 100-operation rotation budgets, lost packets, stalled DISCOVERED states, premature result acknowledgment, stale runtime snapshots and Director rescue. Independent One-Click GO consumer shipping slipped from focus.

**Specific bounded evidence:** `docs/INCIDENT_2026-10-07_PCE9_OPERATION_BUDGET_REPO_DRIFT_AND_REPEAT_PROBES.md` records OP101..OP179A2 and seven redundant restart-proofs. PCE10.018 stuck DISCOVERED ~3,774 s, PCE10.021 ~784 s, PCE10.025 false suppression, PCE10.037 exact resolver zero match. PCE10.035 source green did not prove live activation.

**Impact:** no evidence of accepted persistent Firefox production recovery or Chrome/Edge consumer acceptance. Source/live 19/38 mismatches at PCE10.036. Backup of broken state is not a working recovery baseline.

**Disposition:** preserve safety/restore refs and proven PCE6–8 mechanisms; quarantine PCE9/10 as non-release production baselines; shift PCE011 priority to r28 One-Click GO consumer, with GitHub-first exact Firefox fix and eventual controlled canary. Never silently count tests, temporary addons, or commits as distributable builds.
