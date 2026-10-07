# Incident: PCE9 used Python without pytest

## Observation
OP009 invoked `python -m pytest`, which resolved to the global Python 3.13 installation. That interpreter does not have pytest installed.

## Classification
Engineering harness defect. No product test failure occurred because the suite never started.

## Permanent rule
Before claiming targeted/full-suite results, resolve a repository/test-capable interpreter and prove `import pytest` succeeds. Preserve and reuse that interpreter for the remaining rotation unless repository state changes.
