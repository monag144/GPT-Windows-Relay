# Timestamped compatibility reference — 2026-10-08T0755Z

GPT ONE-CLICK GO — CONSUMER 1.1.0 — Entry Point 2026-10-08T0650Z

WHAT THE USER DOES
1. Unzip the package or clone/fork the repository.
2. Double-click GO.bat.
3. In the main GUI, choose the browser you want One-Click Go to use.
4. Click Setup Browser once. One-Click Go configures the selected browser integration automatically and opens ChatGPT.
5. Sign in once in that browser's isolated One-Click profile if needed.
6. If several ChatGPT tabs are open there, activate the tab you want.
7. Once the GUI reports CONNECTED, describe the mission and click GO (or press Ctrl+Enter).
8. Click Update in the GUI whenever you want the latest consumer build.

BROWSER OWNERSHIP
- The browser is supplied by the user. One-Click Go does not install or replace it.
- Chromium-family browsers are supported through a local MV3 extension:
  Microsoft Edge, Google Chrome, Brave, Vivaldi, Chromium, Opera, plus a custom Chromium-compatible .exe.
- One-Click Go verifies the extension bridge before GO is enabled; merely starting a browser is not considered success.
- Setup Browser is a zero-touch consumer flow: it prepares the local extension, installs/loads it using the supported browser automation path, opens ChatGPT, and verifies the relay connection.
- Google Chrome uses a local DevTools setup channel with an ephemeral localhost debugging port to load the unpacked extension into the dedicated One-Click session. Because branded Chrome does not persist that unpacked load, One-Click keeps that isolated session alive; if the user closes it, Open ChatGPT transparently configures the next isolated session again.
- Other supported Chromium-family browsers use their automatic extension-loading path and are also connection-verified.
- The consumer UI does not require Developer mode, Load unpacked, Explorer navigation, or copying an extension folder path.
- Browser choice is saved locally.
- Each browser gets its own isolated One-Click profile and its own generated extension identity/configuration.
- A mission is bound to the browser selected in the GUI.
- Inside that browser, the most recently active connected ChatGPT tab receives the mission.
- This prevents two different connected browsers from racing for the same targeted mission.
- Release distinction: frozen consumer r28 intentionally disables Firefox. This repository's r29 DEVELOPMENT source attempts temporary Firefox add-on automation but has NOT passed signed/persistent Firefox restart or the complete consumer acceptance matrix. Do not advertise it as a released Firefox integration.

DEPENDENCIES
- Browser: user-supplied.
- Python: automatically detected or provisioned.
- Preferred automatic Python installation uses Windows Package Manager when available.
- If winget is absent, bootstrap downloads the pinned official Python installer from python.org and verifies its SHA-256 before installing.
- An isolated virtual environment is created under runtime\.venv.
- tkinter and required Python standard-library modules are verified.
- Third-party Python packages: NONE.
- requirements.txt is intentionally empty except for documentation comments.
- PowerShell is used only for Windows bootstrap/runtime supervision and is part of supported Windows installations.
- Packaged users do NOT need Git for updates.

SELF UPDATE
- The Update button lives in the main GUI.
- Packaged installs update directly from the configured GitHub repository/branch using Python's standard library; Git is not required.
- The updater preserves the local virtual environment and generated per-browser relay credentials/configuration.
- Source checkouts/forks update from their own current Git origin and branch using fast-forward-only pull.
- Source updates refuse to overwrite a dirty checkout.
- After an update, the GUI offers to restart One-Click Go.

HOW MISSION TARGETING WORKS
GUI-selected browser
  -> browser-specific One-Click extension
  -> most recently active ChatGPT tab in that browser
  -> mission delivery
  -> ChatGPT response
  -> normal GPT Windows Relay action/result automation

WHAT GO.BAT DOES
- Ensures Python 3.10+ with tkinter exists.
- Creates/verifies the isolated runtime environment.
- Installs any future declared requirements (currently zero).
- Creates/loads the localhost relay token.
- Starts/verifies the local relay.
- Launches the main GUI directly.
- It does NOT choose or install a browser.

SECURITY NOTES
- The relay listens on 127.0.0.1 only and uses a random local token.
- Base64 is transport encoding, not encryption.
- The relay is powerful when armed: ChatGPT can execute commands as the signed-in Windows user.
- Browser profiles and generated extension config remain local.
- The consumer package does not include the Workday/job-application engine.

DEVELOPERS / FORKS
- Consumer release metadata is in release.json. The GUI title shows both semantic version and release revision (for example, 1.1.0 r10).
- A fork can change repository/branch there for packaged self-updates.
- A Git checkout's Update button follows that checkout's own origin/current branch.
- Run build-package.ps1 to create dist\GPT-OneClick-Go.zip.
- Run consumer_app.py --layout-probe on Windows to verify GO and Update stay visible.


RELAY RENDERING RELIABILITY
- The first mission delivered to ChatGPT automatically includes the canonical Windows relay sandwich contract.
- Every browser-visible Windows relay result automatically ends with:
  Reply to this with the sandwich technique
- Any GPT_WINDOWS_ACTION must be emitted in one final assistant response as:
  visible prose header -> bare Markdown fence -> action envelope/JSON only -> visible prose footer.
- Language-tagged fences and commentary/progress relay packets are prohibited because they have caused folded/inaccessible relay packets in the ChatGPT client.
- Keep relay packets compact; use bounded local steps instead of giant inline scripts.

- The Windows GUI is single-instance: repeated GO.bat launches or accidental manual launches do not create duplicate control windows.
