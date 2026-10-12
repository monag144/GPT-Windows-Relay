# Firefox migration rollback record

Prepared only; no extension was removed, reloaded, activated, or deployed.

Pre-cutover identities:

- `GPT/Client/Relay/extension` — GPT One-Click Go Relay 1.1.0; content SHA256 `34500934B214423AFC2D3C267877A961CD0EC46521E5860ED149502D7F4E2AE5`.
- `GPT-Windows-Relay-Main-Build/windows-relay/extension` — GPT One-Click Go Relay 1.1.0; content SHA256 `5169E84985E9452E9E55EA29D5BCD56F4484E0B02EE7853C21D8CBE2BC3C151A`.

Target package: `windows-relay/extension-persistent`, GPT Windows Relay 0.3.17, Gecko ID `gpt-windows-relay@local`.

Rollback rule: restore only the recorded add-on registrations after an approved cutover failure. Preserve backend state, STOP, attempted IDs, owner state, and PCE16.035 hold. Never clear state or resend an operation.
