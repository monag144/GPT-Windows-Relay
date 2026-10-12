# Windows Relay full-stack build provenance — 2026-10-11

## Scope

This review tracks **the complete Windows Relay stack**, not just its launcher. GitHub source was reviewed on the active development branch `wip/windows-relay-rebuilt-resynced-2047-101026`; the installed PC's actual processes, shortcuts, Firefox add-on and loaded code require native proof. The October 11 Codex read-only audit observed **no listener** on 127.0.0.1:8766 at that time, no proven matching relay task/process and an **unknown loaded Firefox extension**. These findings do **not** prove an old backend was running.

| Layer | Intended current Main-Build component | Connection and limitation |
|---|---|---|
| Developer checkout | `%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build` | Source edits first land on GitHub WIP branch, then are pulled locally without overwriting uncommitted changes |
| Launcher | `windows-relay/START-GPT-WINDOWS-RELAY.bat` | Uses `%~dp0`, launches same-directory watchdog and `relay-control.ps1`; source does not hardcode old Client |
| Controller | `windows-relay/relay-control.ps1` | Uses `$PSScriptRoot`, checks canonical PID/executable path, refuses a foreign listener on 8766 |
| Supervisor/backend | `windows-relay/run.ps1` → `windows-relay/windows_relay.py server` | Both self-relative; Python HTTP backend binds `127.0.0.1:8766` if correctly started |
| Watchdog | `windows-relay/relay-watchdog-loop.ps1` | Self-relative; monitors canonical backend, supervisor, HUD. Earlier missing-HUD ordering bug is corrected in source, not live verified |
| HUD | `windows-relay/hud.py` | Implements START/STOP/RESTART/OFF/KILL; reads backend status and browser events. Firefox failure display updated to `ACTION FAILED`, not yet live verified |
| Local pairing | `%APPDATA%\GPTWindowsRelay\bridge.json` | Contains bearer token and backend port; **private local state, never publish or print token** |
| Persistent Firefox source | `windows-relay/extension-persistent/` | Manifest `gpt-windows-relay@local`, version 0.3.17; worker targets localhost:8766. Source existence is **not loaded Firefox proof** |
| Firefox installed extension | Firefox profile registration and/or signed extension enterprise policy | Actual install path/version and XPI byte parity can be examined read-only. Loaded runtime still needs `about:debugging#/runtime/this-firefox` verification |
| Firefox dispatch | `extension-persistent/content.js` → `service_worker.js` → `POST /action` | **Broken source integration:** worker sends `{packet}`; backend demands `{packet,issuance,owner}` plus prior operator-approved backend conversation bind |
| Backend results | `windows_relay.py` persisted wire result → service worker → content script composer | Backend result and browser delivery logic exist; no successful complete installed-product round trip yet proven |
| Consumer product | `consumer/` with `windows-relay/extension/` | One-Click Go is a separate consumer workflow (often 8767) and must not be mistaken for persistent GPT Windows Relay source |
| Legacy installed Client | `%USERPROFILE%\Downloads\Dev\GPT\Client\Relay` | Historical deployment with different critical hashes; existence and current process references must be measured rather than inferred |
| Legacy browser repair tool | `windows-relay/install-browser-fix.ps1` | **Still defaults to old Client**; do not use for the Main-Build release |
| Legacy installer | `windows-relay/install.ps1` | Builds the sibling `extension/` config and contains stale armed-start documentation; not canonical persistent Firefox rollout |
| Signed XPI creation | `windows-relay/sign-extension.ps1`, `build-extension-xpi.ps1` | Both default to `extension-persistent/`; installed XPI parity requires observed artifact/profile records |
| Shortcut/scheduler/autorun | Windows shortcuts, task scheduler, startup registry entries | Cannot be proven by GitHub code; a copied old shortcut could still point to Client even though Main-Build scripts are self-relative |

## Read-only verification

After an operator-approved `git pull --ff-only`, run:

```bat
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%USERPROFILE%\Downloads\Dev\GPT-Windows-Relay-Main-Build\windows-relay\tools\Inspect-Relay-Runtime-Identity.ps1"
```

The inspector reports: branch/HEAD and dirty-entry count; presence and SHA comparison of backend, controller, watchdog, HUD, launcher and persistent-extension files against old Client; 8766 PID and classified source; relay processes; scheduled tasks; registry startup references; Start Menu/Desktop shortcuts; Firefox profile add-on registration; enterprise XPI policy and signed-XPI byte parity **when available**. It avoids printing token material, raw Firefox profile metadata or private command lines. It does not start/stop the relay, modify the registry, install Firefox extensions, or send network actions.

**If `PORT_8766=NOT_LISTENING`** the extension cannot connect, regardless of pairing. **If `PORT_8766=LISTENING ... SOURCE=OLD_CLIENT`**, the old backend is actually running. **If `SOURCE=MAIN_BUILD`**, backend provenance is positive but Firefox pairing and issuance/owner protocol can still fail. **If Firefox registration/policy says OLD_CLIENT**, this is installed-file evidence only, not proof that the live tab is running those exact bytes. If the extension is distributed as a signed XPI, profile/canonical XPI SHA parity is useful provenance, but `about:debugging` and an active-tab runtime identity check remain necessary.

The standalone Firefox popup's `Relay unavailable: NetworkError` means a failed localhost request; it does **not** by itself identify old-build targeting, wrong token, loaded extension source or a successful backend action. Wrong/missing pairing is a separate error path.

## Source-readiness and rollout distinction

GitHub pull updates the checkout but **does not restart Python, rewire a running shortcut, deploy a signed XPI, reload the active Firefox add-on, change pairing, or alter the protected old Client**. Those are separate operator-controlled steps with loaded-path and rollback evidence.

STOP, pairing, operator authorization, conversation ownership, atomic action claiming, collision refusal and no replay remain mandatory backend protections. Administrative engineering governance is abolished; it must not reenter runtime. The source transport mismatch must be fixed without bypassing these protections.

Other Firefox behavior: the content script includes a narrowly matched GitHub `Always allow` automation. Its code and operator-source history are documented in `docs/facts/WINDOWS_RELAY_GITHUB_APPROVAL_BEHAVIOR_2026-10-11.md`; its *loaded Firefox state* cannot be inferred merely from the repository.

**Verification status:** GitHub source provenance reviewed; real Windows process and loaded Firefox add-on comparison awaits read-only inspector output and Firefox about:debugging observation. No actual old-client-running claim has been proven.
