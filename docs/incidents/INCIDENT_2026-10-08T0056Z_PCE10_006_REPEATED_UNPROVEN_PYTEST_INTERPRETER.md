# PCE10.006 repeated unproven pytest interpreter incident — 2026-10-08T0056Z

## Observation

PCE10.006 completed canonical-repository, per-turn control-read, and stale-settle structural gates, then failed before live staging because it selected:

`Client/Relay/.venv/Scripts/python.exe`

solely because the executable existed and invoked `-m pytest`. That interpreter does not contain pytest.

## Classification

**REPEATED ENGINEERING HARNESS DEFECT / PREVIOUS PERMANENT RULE VIOLATED**

This repeats `INCIDENT_2026-10-07_PCE9_WRONG_PYTEST_INTERPRETER.md`, whose permanent rule already required proving `import pytest` before claiming pytest-based acceptance.

## Impact

- targeted/full tests did not start;
- no live browser files were staged;
- no add-on reload or page refresh occurred;
- no rollback is required;
- PCE10.006 consumed an operation without advancing acceptance.

## Reflection

Selecting a test interpreter by path existence is not a capability check.

The current Windows Relay and consumer tests do not contain pytest-specific imports, marks, fixtures, or pytest APIs. Therefore the lower-dependency acceptance path is Python stdlib `unittest`.

## Corrective rule

1. Prefer the stdlib `unittest` runner for the current suite.
2. If any external test runner is selected, capability-probe the exact interpreter/runner before starting the suite.
3. Never infer runner capability from executable existence.
4. Run acceptance bytecode-free and fail closed on any test failure.
5. Reintroduce pytest only when repository tests actually require it or a named acceptance gate explicitly requires pytest.
