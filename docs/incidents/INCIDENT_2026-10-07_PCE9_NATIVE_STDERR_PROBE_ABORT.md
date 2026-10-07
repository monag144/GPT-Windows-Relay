# Incident: native stderr aborted interpreter discovery

## Trigger
OP010 probed candidate Python interpreters for `pytest` while global PowerShell `ErrorActionPreference` was `Stop`. A candidate without pytest wrote a traceback to stderr. PowerShell surfaced that stderr as a terminating NativeCommandError.

## Impact
Discovery stopped before a capable interpreter could be found. No product test ran and no production source was modified.

## Permanent control-harness rule
Expected-negative native process probes must temporarily use non-terminating error handling, redirect expected stderr, inspect `$LASTEXITCODE`, and restore strict error handling before continuing.
