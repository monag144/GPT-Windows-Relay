# Windows Relay migration and redundancy review — 2026-10-11

## Result

`GPT-Windows-Relay-Main-Build` is the single development checkout for the
Windows Relay repository. Its `windows-relay/` directory is the canonical
Windows Relay source layout; `windows-relay/extension-persistent/` is the
persistent Firefox release source. The separate `consumer/` tree is retained
as the GPT One-Click Go consumer product and is not an alternate Windows Relay
backend.

The installed Client at `Downloads/Dev/GPT/Client/Relay` remains the protected
runtime until a separately approved, rollback-tested cutover. No live process,
Firefox profile, credential, queue, result ledger, or operational state was
changed by this consolidation.

## Accounted-for development roots

| Root | Disposition | Reason |
|---|---|---|
| `GPT-Windows-Relay-Main-Build` | **Development checkout** | Git checkout and canonical source tree. |
| `GPT/Client/Relay` | **Protected installed runtime** | Historical/working installation; not safe to relocate while it may be referenced by launchers or watchdogs. |
| `GPT` (other subtrees) | **Historical/runtime provenance** | Contains Client backups, rollback snapshots, and older product copies; no automatic deletion or merge. |
| `Legacy` | **Archive** | Historical builds and rollback material; preserved. |
| `Prototype-Developing` | **Experimental root** | Empty in the supplied inventory; no source was inferred or fabricated. |
| `bug-bounties` | **Unrelated** | Outside Windows Relay scope. |

The supplied inventory indexed 5,289 files across the relevant roots. Its
reports remain local at the checkout root; they are not committed because
`file-metadata.csv` contains a machine-wide personal path inventory.

## Hash comparison of critical components

These SHA-256 values were computed from the files on disk during this review:

| Component | Main-Build | Installed Client | Assessment |
|---|---|---|---|
| `windows_relay.py` | `BA29B6BFAAA453BE6669C47D5B5C4E8A9F36A07AAB9FAB046849CD93EC39F002` | `3AD004FDF3D22AA9B4927B369D17A5313E27D3FB29D40000805CA3860372B1DA` | Different; requires controlled compatibility review before cutover. |
| `hud.py` | `363C3D55446DF3E850CE53DC1C4DEF6CCAA1FF665126A5A41FF1D93B24CBC44E` | `363C3D55446DF3E850CE53DC1C4DEF6CCAA1FF665126A5A41FF1D93B24CBC44E` | Identical; five-button HUD source is preserved. |
| `relay-control.ps1` | `04EDFA01B2EBDA8933ED636ED09A2C2F518D123CD224B3A2F33129BDB334CCFE` | `79264E06AE53F54BFE5F43CAC6664F967C32244FFC1201F46F280A4D6E9850FC` | Different; do not replace the installed controller implicitly. |
| `relay-watchdog-loop.ps1` | `0C41060188A752755CD41B2D5D4798E8CB8794929C07339ACA19CADF1DEFCA6B` | `38B5FE08D8230658C9153925FB7D4F8CC3AF846CB2AA447CF6837B850B748DDE` | Different; runtime ownership/cutover remains unresolved. |
| `START-GPT-WINDOWS-RELAY.bat` | `174995B2A2133021C280FF4D9B9101E6FFAB90BFE67F1560BB8DEF5D1CA86B22` | `F912E4C90AF26113EFE70D7052461A87E2FAB200B68309E53FE154B3137BB1CF` | Different; launch behavior must be validated before cutover. |
| `extension-persistent/manifest.json` | `85418070F6C0CF3249844A88E868B3BB79F31F1D9077EC39D024AC3503585073` | `5644C059C27973BA07230979915643D66C04B2B565EBE02DB956911154706B7E` | Different; loaded Firefox identity is not proven by disk equality. |

The Main-Build also contains `windows-relay/runtime/` and the sibling
`windows-relay/extension/` tree. They are retained as consumer/temporary
compatibility and provenance inputs because packaging scripts reference them;
they are not presented as additional authoritative release sources.

## Generated and experimental material

Prototype acceptance profiles, candidate packages, release-candidate files,
and test evidence remain under `Prototype/` for reproducibility. Python
`__pycache__` directories are generated artifacts and are excluded from source
review; they are safe to remove later in a separately reviewed cleanup.

## Validation

The bounded offline test run used Python `unittest` with
`PYTHONPATH=windows-relay`:

- `test_control_launch_runtime.py`: PASS (3)
- `test_result_turn_recognition.py`: PASS (1)
- `test_whole_product_stop_contract.py`: PASS (15)
- `test_hud.py`: 16 passed, 4 failures

The four HUD failures are existing source/test-contract drift around the
expected STOP display marker and watchdog reconciliation ordering. They were
not silently waived or changed during consolidation. `pytest` is unavailable
in the installed Python environment (`No module named pytest`).

## Remaining blockers and rollback

The installed Client and Main-Build backend/controller/watchdog/extension do
not have identical bytes. Therefore this is a source consolidation, not a
live deployment certification. The safe rollback is to leave the protected
Client untouched and use its existing rollback/backups; no runtime files were
overwritten. A future cutover must first reconcile the differing hashes,
resolve the four HUD contract failures, verify launcher ownership, and perform
an operator-approved isolated restart with a tested rollback.
