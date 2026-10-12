# Windows Relay identity diagnostic parser failure — 2026-10-12

## User-observed incident

The operator safely fast-forwarded the Main-Build checkout from `8e86089` to `63ef192`. Immediately afterward, the read-only PowerShell identity diagnostic refused to parse at its Firefox add-on matching clause. Windows PowerShell reported an unexpected `FIREFOX_REGISTRATION_IS_NOT_LOADED_CODE_PROOF=True` token and a cascade of missing quote, bracket and try/catch terminators.

**This was a bug in the assistant-authored GitHub diagnostic**, not proof of a broken relay or an old-build process. The error occurred at parse time, before the script could enumerate any Windows listener, shortcut, Firefox registration or config. Consequently no results about the current loaded runtime can be inferred from this failed diagnostic.

## Verified cause

In `windows-relay/tools/Inspect-Relay-Runtime-Identity.ps1`, a generated editing operation inserted the diagnostic footer **inside** the PowerShell regex used to recognize the Firefox add-on name. The script broke around lines 128–133, after `$addonName -notmatch '^GPT (Windows Relay|One-Click Go Relay)` and before `){continue}`. A literal PowerShell `$'` substring was also mishandled by JavaScript's string-replacement interpolation in an initial in-memory repair attempt (that first attempted repair was rejected by sanity checks and never pushed).

## Repair and verification boundaries

- Source fix commit `ead7e2f43f743451723941b9870959e67fc51902` restores the entire Firefox name-matching condition and keeps the status footer at the end of the file.
- Test repair commit `9c98bad998976e6a6043d96f5dc1a83858bb8638` supplies explicit corruption assertions **plus native Windows PowerShell AST parsing** without running the diagnostic. A generated intermediate test edit was also corrupted before being replaced with the complete corrected test; it was pushed but superseded before operator re-pull.
- GitHub readback confirmed the corrected regex, exactly one status footer, no embedded footer, matched delimiter pairs and balanced quoting in a static scan. A locally reconstructed version of the Python regression test compiled successfully. **The PowerShell AST check itself still requires a real Windows test run**; no Windows pass is claimed yet.

## Next step

Fast-forward Main-Build on the same branch, run `python -m unittest discover -s windows-relay/tests -p test_runtime_identity_diagnostic.py -v` in a way that resolves the actual checkout, and execute the diagnostic only if the native parser test succeeds. A failing test is a stop condition for running this diagnostic, **not** a Windows Relay execution-governance gate.

No runtime process, pairing token, Firefox profile, queued action or deployed Client was modified by the source-only repair.
