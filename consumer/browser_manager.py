#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Iterable
import urllib.error
import urllib.request

APPDATA = Path(os.environ.get("APPDATA", Path.home() / ".config"))
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local"))
SETTINGS_PATH = APPDATA / "GPTWindowsRelayConsumer" / "consumer-settings.json"
HERE = Path(__file__).resolve().parent

BROWSER_DEFS = (
    {
        "id": "edge",
        "name": "Microsoft Edge",
        "family": "chromium",
        "setup_mode": "cdp_auto",
        "paths": (
            r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe",
            r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe",
            r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe",
        ),
    },
    {
        "id": "chrome",
        "name": "Google Chrome",
        "family": "chromium",
        "setup_mode": "cdp_auto",
        "paths": (
            r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
            r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        ),
    },
    {
        "id": "brave",
        "name": "Brave",
        "family": "chromium",
        "setup_mode": "auto_try",
        "paths": (
            r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
        ),
    },
    {
        "id": "vivaldi",
        "name": "Vivaldi",
        "family": "chromium",
        "setup_mode": "auto_try",
        "paths": (
            r"%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe",
            r"%PROGRAMFILES%\Vivaldi\Application\vivaldi.exe",
            r"%PROGRAMFILES(X86)%\Vivaldi\Application\vivaldi.exe",
        ),
    },
    {
        "id": "chromium",
        "name": "Chromium",
        "family": "chromium",
        "setup_mode": "auto_try",
        "paths": (
            r"%LOCALAPPDATA%\Chromium\Application\chrome.exe",
            r"%PROGRAMFILES%\Chromium\Application\chrome.exe",
            r"%PROGRAMFILES(X86)%\Chromium\Application\chrome.exe",
        ),
    },
    {
        "id": "opera",
        "name": "Opera",
        "family": "chromium",
        "setup_mode": "auto_try",
        "paths": (
            r"%LOCALAPPDATA%\Programs\Opera\opera.exe",
            r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe",
        ),
    },
    {
        "id": "firefox",
        "name": "Mozilla Firefox",
        "family": "firefox",
        "setup_mode": "firefox_temp_auto",
        "paths": (
            r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe",
            r"%PROGRAMFILES(X86)%\Mozilla Firefox\firefox.exe",
            r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe",
        ),
    },
)


class BrowserError(RuntimeError):
    pass


def _expand(path: str) -> Path:
    return Path(os.path.expandvars(path)).expanduser()


def load_settings() -> dict:
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, SETTINGS_PATH)


def _first_existing(paths: Iterable[str]) -> Path | None:
    for raw in paths:
        p = _expand(raw)
        if p.is_file():
            return p.resolve()
    return None


def detect_browsers() -> list[dict]:
    settings = load_settings()
    found: list[dict] = []

    for item in BROWSER_DEFS:
        exe = _first_existing(item["paths"])
        if exe is None:
            continue
        supported = item["family"] in {"chromium", "firefox"}
        setup_mode = item.get("setup_mode", "manual")
        found.append(
            {
                "id": item["id"],
                "name": item["name"],
                "family": item["family"],
                "setup_mode": setup_mode,
                "path": str(exe),
                "supported": supported,
                "reason": (
                    ""
                    if supported
                    else "Automatic integration is not available for this browser."
                ),
            }
        )

    custom = settings.get("custom_browser")
    if isinstance(custom, dict):
        raw_path = custom.get("path")
        if isinstance(raw_path, str) and Path(raw_path).is_file():
            resolved = str(Path(raw_path).resolve())
            custom_id = custom.get("id")
            if not isinstance(custom_id, str) or not custom_id.startswith("custom-"):
                custom_id = "custom-" + hashlib.sha256(
                    resolved.casefold().encode("utf-8")
                ).hexdigest()[:10]
            found.insert(
                0,
                {
                    "id": custom_id,
                    "name": str(custom.get("name") or "Custom Chromium browser"),
                    "family": "chromium",
                    "setup_mode": "auto_try",
                    "path": resolved,
                    "supported": True,
                    "reason": "",
                },
            )

    return found


def supported_browsers() -> list[dict]:
    return [b for b in detect_browsers() if b["supported"]]


def get_selected_browser() -> dict | None:
    browsers = detect_browsers()
    settings = load_settings()
    selected = settings.get("browser_id")
    for browser in browsers:
        if browser["supported"] and browser["id"] == selected:
            return browser
    return next((b for b in browsers if b["supported"]), None)


def select_browser(browser_id: str) -> dict:
    browser = next((b for b in detect_browsers() if b["id"] == browser_id), None)
    if browser is None:
        raise BrowserError(f"Browser is not installed or no longer available: {browser_id}")
    if not browser["supported"]:
        raise BrowserError(browser["reason"] or f"{browser['name']} is not supported by this build.")
    settings = load_settings()
    settings["browser_id"] = browser_id
    save_settings(settings)
    return browser


def set_custom_browser(path: str, name: str | None = None) -> dict:
    exe = Path(path).expanduser().resolve()
    if not exe.is_file() or exe.suffix.lower() != ".exe":
        raise BrowserError("Choose a Chromium-compatible browser .exe file.")
    browser_id = "custom-" + hashlib.sha256(
        str(exe).casefold().encode("utf-8")
    ).hexdigest()[:10]
    settings = load_settings()
    settings["custom_browser"] = {
        "id": browser_id,
        "path": str(exe),
        "name": (name or exe.stem).strip() or "Custom Chromium browser",
    }
    settings["browser_id"] = browser_id
    save_settings(settings)
    selected = get_selected_browser()
    if selected is None or selected["id"] != browser_id:
        raise BrowserError("Custom browser selection could not be persisted.")
    return selected


def extension_source_path() -> Path:
    candidates = (
        HERE / "runtime" / "extension",
        HERE.parent / "windows-relay" / "extension",
    )
    for candidate in candidates:
        if (candidate / "manifest.json").is_file():
            return candidate.resolve()
    raise BrowserError("Relay browser extension is missing.")


def _bridge_config() -> dict:
    path = APPDATA / "GPTWindowsRelayConsumer" / "bridge.json"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BrowserError("Local relay configuration is missing. Run GO.bat first.") from exc
    if not isinstance(cfg.get("port"), int) or not isinstance(cfg.get("token"), str):
        raise BrowserError("Local relay configuration is invalid.")
    return cfg


def prepared_extension_path(browser_id: str) -> Path:
    source = extension_source_path()
    target = LOCALAPPDATA / "GPTWindowsRelayConsumer" / "Extensions" / browser_id
    target.mkdir(parents=True, exist_ok=True)

    for src in source.rglob("*"):
        if not src.is_file() or src.name == "config.js":
            continue
        rel = src.relative_to(source)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # GPT_CONSUMER_CANONICAL_CONTENT_SOURCE_V1
    canonical_candidates = (
        HERE / "runtime" / "extension" / "content.js",
        HERE / "runtime" / "content.js",
        HERE.parent / "windows-relay" / "extension" / "content.js",
    )
    canonical = next((path for path in canonical_candidates if path.is_file()), None)
    if canonical is not None:
        shutil.copy2(canonical, target / "content.js")

    cfg = _bridge_config()
    config_js = (
        f"export const RELAY_PORT = {int(cfg['port'])};\n"
        f"export const RELAY_TOKEN = {json.dumps(str(cfg['token']))};\n"
        f"export const RELAY_BROWSER_ID = {json.dumps(browser_id)};\n"
    )
    (target / "config.js").write_text(config_js, encoding="utf-8")
    return target.resolve()


def profile_path(browser_id: str) -> Path:
    safe = "".join(ch for ch in browser_id if ch.isalnum() or ch in "-_") or "browser"
    return LOCALAPPDATA / "GPTWindowsRelayConsumer" / "BrowserProfiles" / safe


def chromium_setup_helper_path() -> Path:
    candidates = (
        HERE / "runtime" / "chromium_extension_setup.ps1",
        HERE.parent / "windows-relay" / "chromium_extension_setup.ps1",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise BrowserError("Automatic browser setup helper is missing.")


def firefox_adapter_path() -> Path:
    candidates = (
        HERE / "runtime" / "firefox_adapter.py",
        HERE.parent / "windows-relay" / "firefox_adapter.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise BrowserError("Automatic Firefox setup helper is missing.")


def _run_firefox_adapter(*args: str, timeout: float = 20.0) -> dict:
    proc = subprocess.run(
        [sys.executable, str(firefox_adapter_path()), *args],
        text=True, capture_output=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise BrowserError((proc.stderr or proc.stdout or "Firefox automation failed.").strip()[-1200:])
    for line in reversed(proc.stdout.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("ok"):
            return payload
    raise BrowserError("Firefox automation returned no confirmation.")



# GPT_CONSUMER_MANAGED_CONVERSATION_IDENTITY_V1
def windows_tools_path() -> Path:
    for candidate in (HERE / "runtime" / "windows_tools.py", HERE.parent / "windows-relay" / "windows_tools.py"):
        if candidate.is_file():
            return candidate.resolve()
    raise BrowserError("Windows UI automation helper is missing.")


def _run_windows_tools(*args: str, timeout: float = 20.0) -> dict:
    proc = subprocess.run([sys.executable, str(windows_tools_path()), *args], text=True, capture_output=True, timeout=timeout)
    if proc.returncode != 0:
        raise BrowserError((proc.stderr or proc.stdout or "Windows UI automation failed.").strip()[-1200:])
    for line in reversed(proc.stdout.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise BrowserError("Windows UI automation returned no result.")


def _normalize_managed_conversation_url(url: str) -> str:
    raw = str(url or "").strip()
    if raw and "://" not in raw:
        raw = "https://" + raw
    prefix = "https://chatgpt.com/c/"
    if not raw.startswith(prefix):
        raise BrowserError("Managed ChatGPT URL is not a conversation URL.")
    ident = raw[len(prefix):].split("?", 1)[0].split("#", 1)[0].strip("/")
    if not ident or "/" in ident:
        raise BrowserError("Managed ChatGPT conversation identity is invalid.")
    return prefix + ident


def remember_managed_conversation_url(browser_id: str, url: str) -> str:
    normalized = _normalize_managed_conversation_url(url)
    settings = load_settings()
    values = settings.get("managed_conversation_urls")
    if not isinstance(values, dict):
        values = {}
    values[browser_id] = normalized
    settings["managed_conversation_urls"] = values
    save_settings(settings)
    return normalized


def get_managed_conversation_url(browser_id: str) -> str | None:
    values = load_settings().get("managed_conversation_urls")
    if not isinstance(values, dict) or not isinstance(values.get(browser_id), str):
        return None
    try:
        return _normalize_managed_conversation_url(values[browser_id])
    except BrowserError:
        return None


def read_managed_conversation_identity(browser_id: str) -> dict:
    browser = next((item for item in detect_browsers() if item.get("id") == browser_id), None)
    if not browser or browser.get("family") != "firefox":
        raise BrowserError("Independent managed-conversation readback is currently implemented for Firefox only.")
    profile = profile_path(browser_id)
    tabs = _run_firefox_adapter("list-tabs", "--profile-path", str(profile))
    window = tabs.get("window_name")
    pid = tabs.get("firefox_pid")
    if not isinstance(window, str) or not window or not isinstance(pid, int) or pid <= 0:
        raise BrowserError("Firefox tab identity did not provide a unique managed window.")
    result = _run_windows_tools(
        "control-inspect", "--window-title", window, "--control-type", "ComboBox",
        "--automation-id", "urlbar-input", "--process-id", str(pid), "--max-results", "5",
    )
    matches = result.get("matches")
    if result.get("match_count") != 1 or not isinstance(matches, list) or len(matches) != 1:
        raise BrowserError("Firefox managed address bar was not uniquely identifiable.")
    value = matches[0].get("value") if isinstance(matches[0], dict) else None
    url = _normalize_managed_conversation_url(str(value or ""))
    return {"ok": True, "browser_id": browser_id, "firefox_pid": pid, "window_name": window, "url": url}


def verify_managed_conversation(browser_id: str, expected_url: str) -> dict:
    expected = _normalize_managed_conversation_url(expected_url)
    identity = read_managed_conversation_identity(browser_id)
    actual = identity["url"]
    if actual != expected:
        raise BrowserError(f"Managed conversation mismatch: expected {expected}, got {actual}")
    return {**identity, "expected_url": expected, "matched": True}


# GPT_CONSUMER_MANAGED_CONVERSATION_REACQUISITION_V1
def reacquire_managed_conversation(browser_id: str, expected_url: str | None = None, timeout: float = 10.0) -> dict:
    raw = expected_url or get_managed_conversation_url(browser_id)
    if not raw:
        raise BrowserError("No managed ChatGPT conversation identity is stored.")
    expected = _normalize_managed_conversation_url(raw)
    try:
        current = verify_managed_conversation(browser_id, expected)
        return {**current, "reacquired": False, "method": "already_selected"}
    except BrowserError:
        pass
    browser = next((x for x in detect_browsers() if x.get("id") == browser_id), None)
    if not browser or not browser.get("supported") or browser.get("family") != "firefox":
        raise BrowserError("Managed conversation reacquisition is currently implemented for Firefox only.")
    profile = profile_path(browser_id)
    try:
        subprocess.Popen([browser["path"], "-profile", str(profile), "-new-tab", expected], close_fds=True)
    except OSError as exc:
        raise BrowserError("Firefox could not reopen the managed conversation: " + str(exc)) from exc
    deadline=time.monotonic()+max(0.25,float(timeout)); last=''
    while time.monotonic()<deadline:
        try:
            current=verify_managed_conversation(browser_id,expected)
            return {**current,"reacquired":True,"method":"open_exact_conversation"}
        except BrowserError as exc:
            last=str(exc); time.sleep(0.25)
    raise BrowserError("Managed conversation reacquisition timed out: "+last)


# GPT_CONSUMER_OUT_OF_BAND_GPT_V1
def send_out_of_band_recovery_prompt(browser_id: str, prompt_text: str) -> dict:
    if not prompt_text or not prompt_text.strip():
        raise BrowserError("Recovery prompt is empty.")
    browser = next((item for item in detect_browsers() if item.get("id") == browser_id), None)
    if not browser or not browser.get("supported"):
        raise BrowserError(f"Recovery browser is unavailable: {browser_id}")
    if browser.get("family") == "firefox":
        # GPT_CONSUMER_RECOVERY_PROMPT_B64_CALLER_V1
        # Keep the natural-language prompt opaque across Python -> PowerShell/native argv.
        encoded = base64.b64encode(prompt_text.encode("utf-8")).decode("ascii")
        return _run_firefox_adapter(
            "send-chatgpt-prompt", "--prompt-b64", encoded,
            "--profile-path", str(profile_path(browser_id)), timeout=20.0,
        )
    raise BrowserError(f"Out-of-band GPT prompt control is not implemented for {browser_id} yet.")


def read_out_of_band_chat(browser_id: str) -> str:
    browser = next((item for item in detect_browsers() if item.get("id") == browser_id), None)
    if not browser or not browser.get("supported"):
        raise BrowserError(f"Recovery browser is unavailable: {browser_id}")
    if browser.get("family") == "firefox":
        result = _run_firefox_adapter(
            "read-chatgpt-text", "--profile-path", str(profile_path(browser_id)), timeout=20.0,
        )
        value = result.get("text")
        return value if isinstance(value, str) else ""
    raise BrowserError(f"Out-of-band GPT readback is not implemented for {browser_id} yet.")


def _automatic_firefox_setup(browser: dict, extension: Path, profile: Path, url: str) -> dict:
    # GPT_CONSUMER_FIREFOX_ONE_CLICK_TEMP_ADDON_V1
    # GPT_CONSUMER_FIREFOX_PROFILE_IDENTITY_V1
    try:
        _run_firefox_adapter("close-profile", "--profile-path", str(profile), timeout=12.0)
    except (BrowserError, subprocess.SubprocessError):
        pass
    manifest = extension / "manifest.json"
    if not manifest.is_file():
        raise BrowserError("Prepared Firefox extension manifest is missing.")
    proc = subprocess.Popen(
        [
            browser["path"],
            "-no-remote",
            "-profile", str(profile),
            "-new-window", "about:debugging#/runtime/this-firefox",
        ],
        close_fds=True,
    )
    last_error = ""
    setup = None
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        try:
            setup = _run_firefox_adapter(
                "ensure-addon", "--manifest-path", str(manifest),
                "--addon-name", "GPT Windows Relay",
                "--profile-path", str(profile),
            )
            break
        except (BrowserError, subprocess.SubprocessError) as exc:
            last_error = str(exc)
            time.sleep(0.4)
    if setup is None:
        try:
            _run_firefox_adapter("close-profile", "--profile-path", str(profile), timeout=12.0)
        except Exception:
            pass
        raise BrowserError("Firefox temporary add-on setup failed: " + (last_error or "browser did not become automation-ready"))
    actual_pid = setup.get("firefox_pid")
    if not isinstance(actual_pid, int) or actual_pid <= 0:
        actual_pid = proc.pid
    _save_browser_pid(browser["id"], browser["path"], actual_pid)
    try:
        subprocess.Popen(
            [browser["path"], "-profile", str(profile), "-new-tab", url],
            close_fds=True,
        )
    except OSError as exc:
        stop_browser(browser["id"])
        raise BrowserError("Firefox could not open the managed ChatGPT tab: " + str(exc)) from exc
    return {"pid": actual_pid, "setup_method": str(setup.get("setup_method") or "firefox_uia_temporary")}

def _browser_connected(browser_id: str, timeout: float = 0.8) -> bool:
    cfg = _bridge_config()
    request = urllib.request.Request(
        f"http://127.0.0.1:{int(cfg['port'])}/browser-status?browser_id={browser_id}",
        headers={"X-GPT-Windows-Relay-Token": str(cfg["token"])},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return bool(payload.get("connected"))
    except (OSError, ValueError, urllib.error.URLError):
        return False


def wait_for_browser_connection(browser_id: str, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _browser_connected(browser_id):
            return True
        time.sleep(0.35)
    return False


def _save_browser_pid(browser_id: str, browser_path: str, pid: int) -> None:
    settings = load_settings()
    settings["browser_id"] = browser_id
    settings["last_browser_path"] = browser_path
    pids = settings.get("browser_pids")
    if not isinstance(pids, dict):
        pids = {}
    pids[browser_id] = int(pid)
    settings["browser_pids"] = pids
    save_settings(settings)


def _automatic_cdp_setup(browser: dict, extension: Path, profile: Path, url: str) -> dict:
    stop_browser(browser["id"])
    helper = chromium_setup_helper_path()
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(helper),
            "-BrowserExe",
            browser["path"],
            "-ProfilePath",
            str(profile),
            "-ExtensionPath",
            str(extension),
            "-Url",
            url,
        ],
        text=True,
        capture_output=True,
        timeout=45,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "Automatic browser setup failed.").strip()
        raise BrowserError(detail[-1200:])

    payload = None
    for line in reversed(proc.stdout.splitlines()):
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("ok"):
            payload = candidate
            break
    if payload is None:
        raise BrowserError("Automatic browser setup returned no confirmation.")

    pid = payload.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        raise BrowserError("Automatic browser setup returned no browser process.")
    _save_browser_pid(browser["id"], browser["path"], pid)
    return payload


def launch_chatgpt(browser_id: str | None = None, url: str = "https://chatgpt.com/") -> dict:
    if browser_id:
        browser = select_browser(browser_id)
    else:
        browser = get_selected_browser()
        if browser is None:
            raise BrowserError(
                "No supported Chromium-family browser was detected. "
                "Install one or choose a custom Chromium-compatible browser executable."
            )

    profile = profile_path(browser["id"])
    profile.mkdir(parents=True, exist_ok=True)
    extension = prepared_extension_path(browser["id"])

    if browser["family"] == "firefox":
        setup = _automatic_firefox_setup(browser, extension, profile, url)
        if not wait_for_browser_connection(browser["id"], timeout=20.0):
            stop_browser(browser["id"])
            raise BrowserError(
                f"{browser['name']} opened, but the One-Click integration did not connect automatically."
            )
        return {
            "browser": browser,
            "profile": str(profile),
            "extension": str(extension),
            "browser_id": browser["id"],
            "pid": int(setup["pid"]),
            "extension_id": "",
            "setup_method": str(setup.get("setup_method") or "firefox_uia_temporary"),
            "connected": True,
        }

    if browser["family"] != "chromium":
        raise BrowserError(browser["reason"] or "This browser is not supported by this build.")

    if browser.get("setup_mode") == "cdp_auto":
        if _browser_connected(browser["id"]):
            proc = subprocess.Popen(
                [
                    browser["path"],
                    "--no-first-run",
                    "--no-default-browser-check",
                    f"--user-data-dir={profile}",
                    url,
                ],
                close_fds=True,
            )
            _save_browser_pid(browser["id"], browser["path"], proc.pid)
            return {
                "browser": browser,
                "profile": str(profile),
                "extension": str(extension),
                "browser_id": browser["id"],
                "pid": proc.pid,
                "setup_method": "existing_session",
                "connected": True,
            }

        setup = _automatic_cdp_setup(browser, extension, profile, url)
        if not wait_for_browser_connection(browser["id"], timeout=20.0):
            stop_browser(browser["id"])
            raise BrowserError(
                f"{browser['name']} opened, but the One-Click integration did not connect automatically."
            )
        return {
            "browser": browser,
            "profile": str(profile),
            "extension": str(extension),
            "browser_id": browser["id"],
            "pid": int(setup["pid"]),
            "extension_id": str(setup.get("extension_id") or ""),
            "setup_method": "devtools_protocol",
            "connected": True,
        }

    args = [
        browser["path"],
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        f"--user-data-dir={profile}",
        *(
            [f"--load-extension={extension}"]
            if browser.get("setup_mode") == "auto_try"
            else []
        ),
        url,
    ]
    proc = subprocess.Popen(args, close_fds=True)
    time.sleep(0.35)
    if proc.poll() is not None and proc.returncode not in (0, None):
        raise BrowserError(f"{browser['name']} exited immediately with code {proc.returncode}.")

    _save_browser_pid(browser["id"], browser["path"], proc.pid)

    return {
        "browser": browser,
        "profile": str(profile),
        "extension": str(extension),
        "browser_id": browser["id"],
        "pid": proc.pid,
        "setup_method": browser.get("setup_mode"),
        "connected": _browser_connected(browser["id"]),
    }


def extensions_page(browser: dict) -> str:
    browser_id = browser.get("id", "")
    if browser_id == "edge":
        return "edge://extensions/"
    if browser_id == "brave":
        return "brave://extensions/"
    if browser_id == "vivaldi":
        return "vivaldi://extensions/"
    if browser_id == "opera":
        return "opera://extensions/"
    return "chrome://extensions/"


def open_extension_setup(browser_id: str, *, url: str | None = None) -> dict:
    browser = select_browser(browser_id)
    profile = profile_path(browser["id"])
    profile.mkdir(parents=True, exist_ok=True)
    extension = prepared_extension_path(browser["id"])
    url = _normalize_managed_conversation_url(url) if url is not None else "https://chatgpt.com/"

    if browser["family"] == "firefox":
        setup = _automatic_firefox_setup(browser, extension, profile, url)
        pid = int(setup["pid"])
        extension_id = ""
        method = str(setup.get("setup_method") or "firefox_uia_temporary")
    elif browser["family"] != "chromium":
        raise BrowserError(browser["reason"] or "This browser is not supported by this build.")
    elif browser.get("setup_mode") == "cdp_auto":
        setup = _automatic_cdp_setup(browser, extension, profile, url)
        pid = int(setup["pid"])
        extension_id = str(setup.get("extension_id") or "")
        method = "devtools_protocol"
    else:
        stop_browser(browser["id"])
        launched = launch_chatgpt(browser["id"], url)
        pid = int(launched["pid"])
        extension_id = ""
        method = "command_line"

    if not wait_for_browser_connection(browser["id"], timeout=20.0):
        raise BrowserError(
            f"{browser['name']} opened, but the One-Click integration did not connect automatically."
        )

    return {
        "browser": browser,
        "profile": str(profile),
        "extension": str(extension),
        "pid": pid,
        "extension_id": extension_id,
        "setup_method": method,
        "connected": True,
    }

def stop_browser(browser_id: str | None = None) -> bool:
    settings = load_settings()
    browser_id = browser_id or settings.get("browser_id")
    if not isinstance(browser_id, str) or not browser_id:
        return False
    pids = settings.get("browser_pids")
    if not isinstance(pids, dict):
        pids = {}
    if browser_id == "firefox" and os.name == "nt":
        try:
            result = _run_firefox_adapter(
                "close-profile", "--profile-path", str(profile_path("firefox")), timeout=12.0
            )
            stopped = bool(result.get("ok"))
        except (BrowserError, subprocess.SubprocessError):
            stopped = False
        pids.pop(browser_id, None)
        settings["browser_pids"] = pids
        save_settings(settings)
        return stopped
    pid = pids.get(browser_id)
    if not isinstance(pid, int) or pid <= 0:
        return False

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
        else:
            os.kill(pid, 15)
    except (OSError, subprocess.SubprocessError):
        return False
    finally:
        pids.pop(browser_id, None)
        settings["browser_pids"] = pids
        save_settings(settings)
    return True

def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    selected = sub.add_parser("select")
    selected.add_argument("browser_id")
    custom = sub.add_parser("custom")
    custom.add_argument("path")
    custom.add_argument("--name")
    launch = sub.add_parser("launch")
    launch.add_argument("--browser")
    launch.add_argument("--url", default="https://chatgpt.com/")
    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            _print_json({"browsers": detect_browsers(), "selected": get_selected_browser()})
        elif args.command == "select":
            _print_json(select_browser(args.browser_id))
        elif args.command == "custom":
            _print_json(set_custom_browser(args.path, args.name))
        elif args.command == "launch":
            _print_json(launch_chatgpt(args.browser, args.url))
        return 0
    except BrowserError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
