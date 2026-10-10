# One-Click Go consumer guide — 2026-10-09

**Document type:** user navigation for the `consumer/` portion of `monag144/GPT-Windows-Relay`; not proof a particular browser integration has passed release acceptance.

## Using the application

1. Obtain the verified Windows consumer package or canonical source checkout and launch `consumer/GO.bat` using the supported setup path.
2. In the GUI, select the browser you intend to use. Use the application's **Setup Browser** flow and sign into ChatGPT in its chosen session if requested.
3. Wait for the GUI to report a connected/ready state before choosing the intended ChatGPT tab, supplying a mission and selecting **GO**. A browser window merely opening is not connectivity proof.
4. Use the application's update functionality only after confirming its configured canonical repository and branch.

## Browser-compatibility caveat

The October 9 inspection found contradictory historical documentation: `consumer/README.txt` said Firefox was disabled until a signed add-on, while `consumer/release.json` configured automatic temporary Firefox installation and recovery. These reflect different maturity/installation paths. **Neither alone establishes the user's currently loaded Firefox extension or a persistent signed release.** Check the installed GUI/runtime and current release acceptance instead of proclaiming either one universally supported or unsupported.

The application uses local browser/relay pairing, runtime state, and browser-specific setup; keep credentials and applicant profiles in local application data, not in GitHub. Preserve the existing browser-ownership and mission-scoping safety requirements.

**Agent/chat switching is separate from consumer setup:** manual one-shot user-requested `Run-Copy-Contents.cmd` only; alternative switch methods are on hold under the October 9 Pacific-local instruction documented in `docs/policy/POLICY_2026-10-10T0331Z_MANUAL_AGENT_HANDOFF_AND_AUTOMATED_ROTATION_HOLD.md`.

Historical consumer v1.1.0 instructions remain recoverable from `consumer/README.txt` in GitHub commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8`. Verify actual installed application behavior before following an old version-specific section.
