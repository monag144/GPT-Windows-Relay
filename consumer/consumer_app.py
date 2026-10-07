#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.error
import urllib.request
from urllib.parse import quote

import browser_manager
from browser_manager import BrowserError
from mission_transport import MissionError, build_mission_message
import updater

APP_VERSION = "1.1.0"
APPDATA = Path(os.environ.get("APPDATA", Path.home() / ".config"))
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local"))
CONFIG_PATH = APPDATA / "GPTWindowsRelayConsumer" / "bridge.json"
RECOVERY_STATE_PATH = LOCALAPPDATA / "GPTWindowsRelayConsumer" / "recovery-supervisor.json"
HERE = Path(__file__).resolve().parent
RELEASE_PATH = HERE / "release.json"


def _release_revision() -> int:
    try:
        data = json.loads(RELEASE_PATH.read_text(encoding="utf-8-sig"))
        value = data.get("revision", 0)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0
    except (OSError, json.JSONDecodeError):
        return 0


APP_REVISION = _release_revision()
APP_DISPLAY_VERSION = f"{APP_VERSION} r{APP_REVISION}" if APP_REVISION else APP_VERSION
_SINGLE_INSTANCE_NAME = r"Local\GPTOneClickGoConsumerGui"
_single_instance_kernel32 = None
_single_instance_handle = None


def acquire_single_instance() -> bool:
    """Return False when another One-Click GUI already owns the Windows mutex."""
    global _single_instance_kernel32, _single_instance_handle
    if os.name != "nt":
        return True

    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_bool

    ctypes.set_last_error(0)
    handle = kernel32.CreateMutexW(None, True, _SINGLE_INSTANCE_NAME)
    if not handle:
        raise OSError(ctypes.get_last_error(), "Could not create One-Click GUI mutex.")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return False

    _single_instance_kernel32 = kernel32
    _single_instance_handle = handle
    return True


def release_single_instance() -> None:
    global _single_instance_kernel32, _single_instance_handle
    if _single_instance_kernel32 is not None and _single_instance_handle:
        try:
            _single_instance_kernel32.CloseHandle(_single_instance_handle)
        finally:
            _single_instance_handle = None
            _single_instance_kernel32 = None


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


# GPT_CONSUMER_RECOVERY_STATUS_VISIBLE_V1
def recovery_status_line(now_epoch: float | None = None) -> str | None:
    try:
        state = json.loads(RECOVERY_STATE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    recovery = state.get("recovery")
    if not isinstance(recovery, dict):
        return None
    phase = str(recovery.get("phase") or "")
    active = {
        "OOB_PROMPT_SENDING", "OOB_WAITING_ADVICE", "OOB_ADVICE_RECEIVED",
        "OOB_REPAIR_EXECUTING", "OOB_FAILED", "OOB_REPAIR_FAILED",
    }
    if phase not in active:
        return None
    incident = str(recovery.get("incident_id") or "unknown")
    detail = str(recovery.get("detail") or recovery.get("action") or "").strip()
    deadline = recovery.get("deadline_epoch")
    expired = isinstance(deadline, (int, float)) and float(deadline) < (now_epoch if now_epoch is not None else time.time())
    if phase in {"OOB_FAILED", "OOB_REPAIR_FAILED"}:
        label = "RECOVERY FAILED"
    elif expired:
        label = "RECOVERY STALLED"
    else:
        label = "RECOVERING"
    suffix = f" • {detail}" if detail else ""
    return f"{label} • {incident} • {phase}{suffix}"


def relay_request(path: str, body: dict | None = None, timeout: float = 1.5) -> dict:
    cfg = load_config()
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{int(cfg.get('port', 8767))}{path}",
        data=data,
        headers={
            "X-GPT-Windows-Relay-Token": str(cfg["token"]),
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class ConsumerApp:
    def __init__(self, *, start_status: bool = True) -> None:
        self.root = tk.Tk()
        self.root.title(f"GPT One-Click Go {APP_DISPLAY_VERSION}")
        self.root.geometry("820x590")
        self.root.minsize(680, 470)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frame = ttk.Frame(self.root, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(5, weight=1, minsize=90)

        ttk.Label(
            frame,
            text="GPT One-Click Go",
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            frame,
            text="Choose your browser, activate the ChatGPT tab you want, describe the mission, then press GO.",
            wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        self.status = tk.StringVar(value="Checking local relay…")
        ttk.Label(frame, textvariable=self.status).grid(row=2, column=0, sticky="w", pady=(0, 8))

        browser_row = ttk.Frame(frame)
        browser_row.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        browser_row.columnconfigure(1, weight=1)
        ttk.Label(browser_row, text="Browser:").grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.browser_value = tk.StringVar()
        self.browser_combo = ttk.Combobox(
            browser_row,
            textvariable=self.browser_value,
            state="readonly",
            width=40,
        )
        self.browser_combo.grid(row=0, column=1, sticky="ew")
        self.browser_combo.bind("<<ComboboxSelected>>", self._browser_selected)

        ttk.Button(
            browser_row,
            text="Refresh",
            command=self.refresh_browsers,
        ).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(
            browser_row,
            text="Choose .exe…",
            command=self.choose_custom_browser,
        ).grid(row=0, column=3, padx=(8, 0))

        self.target = tk.StringVar(
            value=(
                "Mission target: selected browser → its most recently active ChatGPT tab. "
                "The browser itself is user-supplied."
            )
        )
        ttk.Label(
            frame,
            textvariable=self.target,
            wraplength=760,
        ).grid(row=4, column=0, sticky="ew", pady=(0, 8))

        editor = ttk.Frame(frame)
        editor.grid(row=5, column=0, sticky="nsew")
        editor.columnconfigure(0, weight=1)
        editor.rowconfigure(0, weight=1)

        self.text = tk.Text(
            editor,
            wrap="word",
            undo=True,
            font=("Segoe UI", 11),
            height=8,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(editor, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.focus_set()

        settings = browser_manager.load_settings()
        settings_row = ttk.Frame(frame)
        settings_row.grid(row=6, column=0, sticky="ew", pady=(10, 0))

        self.one_click_go = tk.BooleanVar(value=bool(settings.get("one_click_go", True)))
        self.one_click_check = ttk.Checkbutton(
            settings_row,
            text="One-click GO upon entering prompt",
            variable=self.one_click_go,
            command=self._one_click_mode_changed,
        )
        self.one_click_check.pack(side="left")

        self.send_on_enter = tk.BooleanVar(value=bool(settings.get("send_on_enter", False)))
        self.send_on_enter_check = ttk.Checkbutton(
            settings_row,
            text="Send on Enter",
            variable=self.send_on_enter,
            command=self._send_on_enter_changed,
        )
        self.send_on_enter_check.pack(side="left", padx=(18, 0))
        self.text.bind("<Return>", self._text_return)

        self.button_bar = ttk.Frame(frame)
        self.button_bar.grid(row=7, column=0, sticky="ew", pady=(8, 0))

        self.go_button = ttk.Button(
            self.button_bar,
            text="GO",
            command=self.go,
            width=12,
        )
        self.go_button.pack(side="left")

        self.open_button = ttk.Button(
            self.button_bar,
            text="Open ChatGPT",
            command=self.open_chat,
        )
        self.open_button.pack(side="left", padx=(8, 0))

        self.setup_button = ttk.Button(
            self.button_bar,
            text="Setup Browser",
            command=self.setup_browser,
        )
        self.setup_button.pack(side="left", padx=(8, 0))

        self.update_button = ttk.Button(
            self.button_bar,
            text="Update",
            command=self.update,
        )
        self.update_button.pack(side="left", padx=(8, 0))

        ttk.Button(
            self.button_bar,
            text="Clear",
            command=lambda: self.text.delete("1.0", "end"),
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            self.button_bar,
            text="Close",
            command=self.root.destroy,
        ).pack(side="right")

        self.detail = tk.StringVar(value=f"Build {APP_DISPLAY_VERSION} • Ctrl+Enter always sends. Send on Enter is optional.")
        ttk.Label(
            frame,
            textvariable=self.detail,
            wraplength=760,
        ).grid(row=8, column=0, sticky="ew", pady=(10, 0))

        self.browser_map: dict[str, dict] = {}
        self.setup_in_progress = False
        self.update_in_progress = False
        self.go_in_progress = False
        self.relay_online = False
        self.browser_connected = False
        self.root.bind("<Control-Return>", self._go_shortcut)
        self.refresh_browsers()

        if start_status:
            self.root.after(250, self.refresh_status)

    def _go_shortcut(self, _event: tk.Event) -> str:
        self.go()
        return "break"

    def _one_click_mode_changed(self) -> None:
        settings = browser_manager.load_settings()
        settings["one_click_go"] = bool(self.one_click_go.get())
        browser_manager.save_settings(settings)
        if self.one_click_go.get():
            self.detail.set(
                "One-click GO enabled: GO will open/setup the selected browser if needed, then send the mission."
            )
        else:
            self.detail.set(
                "Manual mode: open/setup the browser first; GO becomes available after the integration connects."
            )
        self._sync_go_button_state()

    def _send_on_enter_changed(self) -> None:
        settings = browser_manager.load_settings()
        settings["send_on_enter"] = bool(self.send_on_enter.get())
        browser_manager.save_settings(settings)
        self.detail.set(
            "Send on Enter enabled: Enter sends; Shift+Enter inserts a newline."
            if self.send_on_enter.get()
            else "Send on Enter disabled: Enter inserts a newline; Ctrl+Enter still sends."
        )

    def _text_return(self, event: tk.Event) -> str | None:
        if not self.send_on_enter.get():
            return None
        if int(getattr(event, "state", 0)) & 0x0001:
            return None
        self.go()
        return "break"

    def _clear_mission_if_unchanged(self, mission: str) -> None:
        if self.text.get("1.0", "end").strip() == mission.strip():
            self.text.delete("1.0", "end")

    def _sync_go_button_state(self) -> None:
        browser = self._selected_browser()
        supported = bool(browser and browser.get("supported"))
        ready = bool(
            self.relay_online
            and supported
            and not self.go_in_progress
            and (self.one_click_go.get() or self.browser_connected)
        )
        self.go_button.state(["!disabled"] if ready else ["disabled"])

    def refresh_browsers(self) -> None:
        browsers = browser_manager.detect_browsers()
        selected = browser_manager.get_selected_browser()
        self.browser_map.clear()
        values: list[str] = []

        for browser in browsers:
            label = browser["name"]
            if not browser["supported"]:
                label += " — signed add-on required"
            if label in self.browser_map:
                label += f" ({browser['id']})"
            self.browser_map[label] = browser
            values.append(label)

        self.browser_combo["values"] = values

        if selected is not None:
            label = next(
                (label for label, browser in self.browser_map.items() if browser["id"] == selected["id"]),
                "",
            )
            self.browser_value.set(label)
        elif values:
            self.browser_value.set(values[0])
            browser = self.browser_map[values[0]]
            if not browser["supported"]:
                self.detail.set(browser["reason"])
        else:
            self.browser_value.set("")
            self.detail.set(
                "No browser detected. Install a Chromium-family browser or choose its executable manually."
            )

        self._sync_browser_button_state()

    def _selected_browser(self) -> dict | None:
        return self.browser_map.get(self.browser_value.get())

    def _sync_browser_button_state(self) -> None:
        browser = self._selected_browser()
        supported = bool(browser and browser.get("supported"))
        self.open_button.state(["!disabled"] if supported else ["disabled"])
        setup_enabled = supported and not self.setup_in_progress and not self.go_in_progress
        self.setup_button.state(["!disabled"] if setup_enabled else ["disabled"])
        self._sync_go_button_state()

    def _browser_selected(self, _event: tk.Event | None = None) -> None:
        browser = self._selected_browser()
        self._sync_browser_button_state()
        if not browser:
            return
        if not browser["supported"]:
            self.detail.set(browser["reason"])
            return
        try:
            browser_manager.select_browser(browser["id"])
            self.detail.set(
                f"Selected {browser['name']}. Open it here, then activate the ChatGPT tab you want GO to use."
            )
        except BrowserError as exc:
            messagebox.showerror("Browser selection failed", str(exc))

    def choose_custom_browser(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose Chromium-compatible browser executable",
            filetypes=[("Windows applications", "*.exe"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            browser_manager.set_custom_browser(path)
            self.refresh_browsers()
            self.detail.set(
                "Custom Chromium-compatible browser selected. Open ChatGPT to create its isolated One-Click profile."
            )
        except BrowserError as exc:
            messagebox.showerror("Browser selection failed", str(exc))

    def _browser_connected(self, browser: dict | None) -> bool:
        if not browser or not browser.get("supported"):
            return False
        try:
            status = relay_request(
                "/browser-status?browser_id=" + quote(str(browser["id"]), safe=""),
                timeout=0.6,
            )
            return bool(status.get("connected"))
        except Exception:
            return False

    def refresh_status(self) -> None:
        try:
            s = relay_request("/status", timeout=0.6)
            armed = "ARMED" if s.get("armed") else "DISARMED"
            pending = int(s.get("pending_missions", 0))
            browser = self._selected_browser()
            connected = self._browser_connected(browser)
            self.relay_online = True
            self.browser_connected = connected
            browser_name = browser["name"] if browser else "none"
            integration = "CONNECTED" if connected else "NOT CONNECTED"
            recovery_line = recovery_status_line()
            self.status.set(
                recovery_line if recovery_line else (
                    f"Relay ONLINE / {armed} / pending: {pending} / "
                    f"{browser_name}: {integration}"
                )
            )
            self._sync_go_button_state()
        except Exception:
            self.relay_online = False
            self.browser_connected = False
            self.status.set("Relay OFFLINE — close this window and run GO.bat to repair/start it.")
            self._sync_go_button_state()
        self.root.after(1500, self.refresh_status)

    def open_chat(self) -> None:
        browser = self._selected_browser()
        if not browser:
            messagebox.showwarning("Browser needed", "Choose a browser first.")
            return
        if not browser["supported"]:
            messagebox.showwarning("Browser not automatically supported", browser["reason"])
            return
        try:
            result = browser_manager.launch_chatgpt(browser["id"])
            self.detail.set(
                f"Opened {result['browser']['name']} with its One-Click profile. "
                "Activate the ChatGPT tab you want to receive the next mission."
            )
        except BrowserError as exc:
            messagebox.showerror("Could not open ChatGPT", str(exc))

    def setup_browser(self) -> None:
        if self.setup_in_progress:
            return
        browser = self._selected_browser()
        if not browser:
            messagebox.showwarning("Browser needed", "Choose a browser first.")
            return
        if not browser["supported"]:
            messagebox.showwarning("Browser not automatically supported", browser["reason"])
            return

        self.setup_in_progress = True
        self._sync_browser_button_state()
        self.detail.set(
            f"Setting up {browser['name']} automatically… One-Click will install its local integration and open ChatGPT."
        )

        def worker() -> None:
            try:
                result = browser_manager.open_extension_setup(browser["id"])
                self.root.after(0, lambda: self._finish_browser_setup(result, None))
            except Exception as exc:
                self.root.after(0, lambda exc=exc: self._finish_browser_setup(None, exc))

        threading.Thread(target=worker, name="oneclick-browser-setup", daemon=True).start()

    def _finish_browser_setup(self, result: dict | None, error: Exception | None) -> None:
        self.setup_in_progress = False
        self._sync_browser_button_state()
        if error is not None:
            self.detail.set("Automatic browser setup failed.")
            messagebox.showerror("Browser setup failed", str(error))
            return

        assert result is not None
        browser = result["browser"]
        if not result.get("connected"):
            self.detail.set(f"{browser['name']} opened, but its One-Click integration did not connect.")
            messagebox.showerror(
                "Browser setup failed",
                f"{browser['name']} opened, but One-Click could not verify the integration.",
            )
            return

        self.detail.set(
            f"{browser['name']} setup complete and CONNECTED. ChatGPT is open and ready for GO."
        )
        messagebox.showinfo(
            "Browser ready",
            f"{browser['name']} is configured and connected. No manual extension setup is required.",
        )

    def go(self) -> None:
        mission = self.text.get("1.0", "end").strip()
        browser = self._selected_browser()
        if not browser:
            messagebox.showwarning("Browser needed", "Choose a browser before sending a mission.")
            return
        if not browser["supported"]:
            messagebox.showwarning("Browser not automatically supported", browser["reason"])
            return
        if not mission:
            messagebox.showwarning("Mission needed", "Enter a mission before pressing GO.")
            return
        if self.go_in_progress:
            return

        if not self.one_click_go.get():
            if not self._browser_connected(browser):
                messagebox.showwarning(
                    "Browser integration not connected",
                    "Click Setup Browser. One-Click will configure the selected browser automatically "
                    "and verify the connection before GO is enabled.",
                )
                return
            self._queue_mission(mission, browser)
            return

        self.go_in_progress = True
        self._sync_browser_button_state()
        self.detail.set(
            f"One-click GO: preparing {browser['name']} and connecting it to ChatGPT…"
        )

        def worker() -> None:
            try:
                browser_manager.select_browser(browser["id"])
                if not self._browser_connected(browser):
                    setup = browser_manager.open_extension_setup(browser["id"])
                    if not setup.get("connected"):
                        raise BrowserError(
                            f"{browser['name']} opened, but the One-Click integration did not connect."
                        )
                mission_id = self._send_mission(mission, browser)
                self.root.after(0, lambda: self._finish_go(browser, mission_id, None, mission))
            except Exception as exc:
                self.root.after(0, lambda exc=exc: self._finish_go(browser, None, exc))

        threading.Thread(target=worker, name="oneclick-go", daemon=True).start()

    def _send_mission(self, mission: str, browser: dict) -> str:
        browser_manager.select_browser(browser["id"])
        mission_id, message = build_mission_message(mission)
        relay_request("/arm", {"armed": True}, timeout=1.5)
        result = relay_request(
            "/mission",
            {
                "id": mission_id,
                "text": message,
                "target_browser": browser["id"],
            },
            timeout=2.0,
        )
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "Relay rejected mission.")
        return mission_id

    def _queue_mission(self, mission: str, browser: dict) -> None:
        try:
            mission_id = self._send_mission(mission, browser)
            self._clear_mission_if_unchanged(mission)
            self.detail.set(
                f"Mission queued as {mission_id} for {browser['name']}. "
                "It will go only to that browser's active ChatGPT tab."
            )
        except MissionError as exc:
            messagebox.showwarning("Mission needed", str(exc))
        except (BrowserError, OSError, urllib.error.URLError, KeyError, ValueError, RuntimeError) as exc:
            messagebox.showerror("Could not send mission", str(exc))

    def _finish_go(
        self,
        browser: dict,
        mission_id: str | None,
        error: Exception | None,
        mission: str | None = None,
    ) -> None:
        self.go_in_progress = False
        if error is not None:
            self.detail.set("One-click GO could not complete browser setup/send.")
            messagebox.showerror("One-click GO failed", str(error))
        else:
            self.browser_connected = True
            if mission is not None:
                self._clear_mission_if_unchanged(mission)
            self.detail.set(
                f"One-click GO complete: {browser['name']} is connected and mission {mission_id} was queued."
            )
        self._sync_browser_button_state()

    def update(self) -> None:
        if self.update_in_progress:
            return
        self.update_in_progress = True
        self.update_button.state(["disabled"])
        self.detail.set("Checking and installing the latest consumer build…")

        def worker() -> None:
            try:
                result = updater.perform_update()
                self.root.after(0, lambda: self._finish_update(result, None))
            except Exception as exc:
                self.root.after(0, lambda exc=exc: self._finish_update(None, exc))

        threading.Thread(target=worker, name="oneclick-updater", daemon=True).start()

    def _finish_update(self, result: dict | None, error: Exception | None) -> None:
        self.update_in_progress = False
        self.update_button.state(["!disabled"])
        if error is not None:
            self.detail.set("Update failed.")
            messagebox.showerror("Update failed", str(error))
            return

        assert result is not None
        changed = bool(result.get("changed"))
        version = result.get("after") or result.get("version") or APP_VERSION
        if not changed:
            self.detail.set(f"Already up to date ({version}).")
            messagebox.showinfo("Up to date", f"GPT One-Click Go is already current ({version}).")
            return

        self.detail.set(f"Updated to {version}. Restart required.")
        if messagebox.askyesno(
            "Update installed",
            f"Updated to {version}. Restart GPT One-Click Go and its dedicated browser integration now?",
        ):
            self._restart_after_update()

    def _restart_after_update(self) -> None:
        browser = self._selected_browser()
        try:
            if browser and browser.get("supported"):
                browser_manager.stop_browser(browser["id"])
        except Exception:
            pass

        try:
            status = relay_request("/status", timeout=0.8)
            pid = status.get("pid")
            if isinstance(pid, int) and pid > 0 and os.name == "nt":
                subprocess.run(
                    ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                )
        except Exception:
            pass

        try:
            go = str(HERE / "GO.bat")
            restart_code = (
                "import os,sys,time;"
                "time.sleep(1.5);"
                "os.startfile(sys.argv[1])"
            )
            creationflags = 0
            if os.name == "nt":
                creationflags = (
                    getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    | getattr(subprocess, "DETACHED_PROCESS", 0)
                )
            subprocess.Popen(
                [sys.executable, "-c", restart_code, go],
                cwd=str(HERE),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=creationflags,
            )
            self.root.destroy()
        except OSError as exc:
            messagebox.showerror("Restart failed", str(exc))

    def layout_probe(self) -> dict:
        self.root.update_idletasks()
        self.root.update()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        def bounds(widget: tk.Widget) -> tuple[int, int, int, int]:
            return (
                widget.winfo_rootx() - root_x,
                widget.winfo_rooty() - root_y,
                widget.winfo_width(),
                widget.winfo_height(),
            )

        def visible(widget: tk.Widget) -> bool:
            x, y, w, h = bounds(widget)
            return (
                bool(widget.winfo_ismapped())
                and w > 1
                and h > 1
                and x >= 0
                and y >= 0
                and x + w <= root_w
                and y + h <= root_h
            )

        return {
            "root": [root_w, root_h],
            "go": list(bounds(self.go_button)),
            "setup": list(bounds(self.setup_button)),
            "update": list(bounds(self.update_button)),
            "go_visible": visible(self.go_button),
            "setup_visible": visible(self.setup_button),
            "update_visible": visible(self.update_button),
        }

    def run(self) -> int:
        self.root.mainloop()
        return 0


def run_layout_probe() -> int:
    app = ConsumerApp(start_status=False)
    results = []
    try:
        for width, height in ((820, 590), (760, 520), (680, 470)):
            app.root.geometry(f"{width}x{height}")
            app.root.update_idletasks()
            results.append({"requested": [width, height], **app.layout_probe()})
        ok = all(
            item["go_visible"] and item["setup_visible"] and item["update_visible"]
            for item in results
        )
        print(
            json.dumps(
                {
                    "version": APP_VERSION,
                    "revision": APP_REVISION,
                    "display_version": APP_DISPLAY_VERSION,
                    "ok": ok,
                    "results": results,
                },
                separators=(",", ":"),
            )
        )
        return 0 if ok else 2
    finally:
        app.root.destroy()


def main() -> int:
    import sys

    if "--layout-probe" in sys.argv[1:]:
        return run_layout_probe()

    if not acquire_single_instance():
        return 0
    try:
        return ConsumerApp().run()
    finally:
        release_single_instance()


if __name__ == "__main__":
    raise SystemExit(main())
