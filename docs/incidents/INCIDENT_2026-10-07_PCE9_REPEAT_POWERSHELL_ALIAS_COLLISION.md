# Incident: repeated PowerShell alias collision

OP020 defined helper function R. PowerShell resolved R to Invoke-History, causing COMMAND_FAILED before product modification.

This repeats the PCE8 H/Get-History failure class.

## Permanent rule
Do not use one-letter helper function names in relay engineering scripts. Prefer explicit names such as EmitSourceRange and verify command resolution when helpers matter.
