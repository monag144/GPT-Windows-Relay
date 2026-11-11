#!/usr/bin/env python3
"""Deterministic, side-effect-free Firefox target classifier.

Consumes observable HWND/tab evidence; NEVER focuses, clicks, pastes, sends,
authenticates an observer, or promotes a target for unattended execution.
The working PowerShell script's Get-Process | Select-Object -First 1 returns
a process MainWindowHandle; that is not an origin-tab identity guarantee.
"""
from __future__ import annotations


def _hwnd_valid(value: object) -> bool:
    return type(value) is int and value > 0


def classify_target(
    selected_hwnd: int,
    foreground_hwnd: int,
    visible_firefox_hwnds: list[int],
    *,
    invoking_hwnd: int | None = None,
    invoking_tab_id: str | None = None,
    active_tab_id: str | None = None,
) -> dict:
    """Classify one observation without authorizing any UI action.

    Current-window HWND equality does not prove active ChatGPT tab identity.
    Even matched user-supplied tab IDs are TRACE claims until independently
    authenticated. This read-only classifier therefore never sets can_send.
    """
    if (
        type(visible_firefox_hwnds) is not list
        or any(not _hwnd_valid(x) for x in visible_firefox_hwnds)
        or len(set(visible_firefox_hwnds)) != len(visible_firefox_hwnds)
        or not _hwnd_valid(selected_hwnd)
        or not _hwnd_valid(foreground_hwnd)
        or (invoking_hwnd is not None and not _hwnd_valid(invoking_hwnd))
        or any(x is not None and
               (not isinstance(x, str) or not x.strip() or len(x) > 128)
               for x in (invoking_tab_id, active_tab_id))
    ):
        raise ValueError("invalid HWND or tab observation")
    windows = set(visible_firefox_hwnds)
    common = {
        "visible_firefox_count": len(windows),
        "matches_foreground": selected_hwnd == foreground_hwnd,
        "invoking_hwnd_verified": invoking_hwnd is not None,
        "active_tab_identity_provided": active_tab_id is not None,
        "can_send": False,  # separate STOP/owner/loaded-code/exact-once gate
        "basis": "read-only observation; no live authenticated observer",
    }
    if not windows:
        status = "BLOCKED_NO_FIREFOX_WINDOW"
    elif selected_hwnd not in windows:
        status = "FAIL_SELECTED_WINDOW_NOT_VISIBLE"
    elif foreground_hwnd not in windows:
        status = "BLOCKED_FOREGROUND_NOT_FIREFOX"
    elif selected_hwnd != foreground_hwnd:
        status = "FAIL_BACKGROUND_WINDOW_SELECTED"
    elif invoking_hwnd is None:
        status = "BLOCKED_INVOKING_WINDOW_UNVERIFIED"
    elif invoking_hwnd != selected_hwnd:
        status = "FAIL_INVOKING_WINDOW_MISMATCH"
    elif invoking_tab_id is None or active_tab_id is None:
        status = "BLOCKED_TAB_UNVERIFIED"
    elif invoking_tab_id != active_tab_id:
        status = "FAIL_WRONG_TAB"
    else:
        status = "TRACE_TAB_MATCH_NOT_AUTHENTICATED"
    return {"status": status, **common}
