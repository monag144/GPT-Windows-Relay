# Incident: PCE8.149A PowerShell alias collision + ChatGPT input-stream error

Observed: 2026-10-07 around 00:13Z / 2026-10-06 around 17:13 Pacific.

## Trigger

`PCE8.149A-map-core-live-topology-and-rollback` was intended to be a read-only deployment-topology audit after correlated whole-product STOP source acceptance.

## Action-side failure

The audit defined a one-character PowerShell helper named `H` and then invoked expressions such as `H <file-path>`.

PowerShell command resolution treated `H` / `h` as the existing `Get-History` alias. The file path was therefore interpreted as the positional history `Id` argument, producing an error equivalent to:

`Get-History : Cannot bind parameter 'Id'. Cannot convert value '<windows-relay file path>' to type System.Int64.`

The intended file-hash helper therefore never ran.

This was an audit-harness defect, not evidence of a relay product failure.

## ChatGPT/UI failure evidence

During delivery of the failed PCE8.149A action result, the ChatGPT conversation displayed a red `Error in input stream` error while the relay HUD remained in `DELIVERING` and identified packet `PCE8.149A-map-core-live-topology-and-rollback`.

This is useful recovery/error-handling evidence and should be retained as a regression case.

The causal relationship between the PowerShell action failure and the ChatGPT `Error in input stream` condition is not established by this observation alone. They occurred in the same delivery attempt and must be treated as two separately observable layers until reproduced or otherwise proven.

## Safety / expected impact

PCE8.149A was intended to be read-only. No product mutation was required by the failed command. The retry must independently verify:

- repository HEAD and cleanliness;
- accepted source content hashes;
- live browser content remains accepted v16;
- exactly one listener remains on 127.0.0.1:8766;
- listener ownership remains stable or otherwise explainable;
- no live cutover has occurred.

## Prevention

Do not use one-character or common PowerShell alias names for relay-script helper functions. Use explicit names such as `GetFileSha256OrMissing` and `GetFileBytesOrMissing`.

This incident should also be retained when validating ChatGPT UI-error detection/recovery because it produced a real `Error in input stream` condition during relay result delivery.

## Follow-up

Retry the original core live-topology audit with non-alias helper names. Do not mutate live during the retry.
