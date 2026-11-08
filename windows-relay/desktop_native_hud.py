#!/usr/bin/env python3
"""Independent ChatGPT Windows desktop relay HUD. No Firefox backend controls."""
from __future__ import annotations
import msvcrt
import sys
import tkinter as tk
from tkinter import font
from pathlib import Path

import desktop_native_relay as native

BG = "#202124"
FG = "#e8eaed"
DIM = "#a9b1ba"
BLUE = "#8ab4f8"
STOP = "#f28b82"
GREEN = "#81c995"


def run():
    native.HOME.mkdir(parents=True, exist_ok=True)
    lock = (native.HOME / "desktop-hud.lock").open("a+b")
    if (native.HOME / "desktop-hud.lock").stat().st_size == 0:
        lock.write(b"x")
        lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock.close()
        return 0

    app = tk.Tk()
    app.title("GPT Windows Desktop Relay")
    app.configure(bg=BG)
    app.attributes("-topmost", True)
    app.geometry("450x154+40+40")
    app.resizable(False, False)

    container = tk.Frame(app, bg=BG, padx=14, pady=10)
    container.pack(fill="both", expand=True)
    title = tk.Label(container, text="GPT WINDOWS DESKTOP RELAY", bg=BG, fg=BLUE,
                     font=("Segoe UI", 11, "bold"))
    title.pack(anchor="w")
    state_text = tk.StringVar(value="STARTING")
    state_label = tk.Label(container, textvariable=state_text, bg=BG, fg=GREEN,
                           font=("Segoe UI", 10, "bold"))
    state_label.pack(anchor="w")
    action_text = tk.StringVar(value="Native ChatGPT app • separate from browser")
    action_label = tk.Label(container, textvariable=action_text, bg=BG, fg=DIM,
                            font=("Segoe UI", 9))
    action_label.pack(anchor="w", pady=(3, 6))

    buttons = tk.Frame(container, bg=BG)
    buttons.pack(fill="x")

    def apply(command):
        try:
            native.update_control(command)
            refresh()
        except Exception as exc:
            action_text.set(f"Control error: {type(exc).__name__}")

    for name, command, background in (
        ("ARM", "arm", "#174ea6"),
        ("STOP", "stop", "#822828"),
        ("OFF", "off", "#3c4043"),
    ):
        b = tk.Button(buttons, text=name, command=lambda c=command: apply(c),
                      bg=background, fg="white", activeforeground="white",
                      font=("Segoe UI", 9, "bold"), relief="flat",
                      padx=15, pady=3)
        b.pack(side="left", padx=(0, 8))

    def refresh():
        try:
            st = native.get_status()
            if st["native_off"]:
                state_text.set("OFF")
                state_label.configure(fg=STOP)
            elif st["native_armed"]:
                state_text.set("NATIVE ARMED")
                state_label.configure(fg=GREEN)
            else:
                state_text.set("STOPPED / DISARMED")
                state_label.configure(fg=STOP)
            phase = st.get("phase") or "UNKNOWN"
            action = str(st.get("last_action") or "none")[:60]
            action_text.set(f"Native process: {phase}  •  Last: {action}")
        except Exception:
            state_text.set("STATUS UNAVAILABLE")
            state_label.configure(fg=STOP)
        app.after(1000, refresh)

    def close():
        app.destroy()
        try:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        lock.close()

    app.protocol("WM_DELETE_WINDOW", close)
    refresh()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(run())
