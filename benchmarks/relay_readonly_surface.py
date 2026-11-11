#!/usr/bin/env python3
"""Actual host read-only probes for Windows Relay; no credentials or browser effects.

This complements (never substitutes for) the R01-R20 behavioral trace suite.
A listening socket or on-disk hash is not proof of loaded Firefox behavior.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from relay_behavioral import digest, write_once


def listener_status(port: int = 8766, timeout: float = 2) -> dict:
    result = {"port": port, "tcp": "UNREACHABLE", "http_status": None,
              "http": "UNKNOWN", "pid": None}
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            result["tcp"] = "REACHABLE"
    except OSError as exc:
        result["detail"] = type(exc).__name__
        return result
    try:
        request = urllib.request.Request("http://127.0.0.1:%d/status" % port,
                                         method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result["http_status"] = response.status
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
    except (OSError, urllib.error.URLError) as exc:
        result["http"] = "UNKNOWN"
        result["detail"] = type(exc).__name__
        return result
    # No auth header is sent. 401 is an expected security response.
    result["http"] = ("EXPECTED_401" if result["http_status"] == 401
                      else "UNEXPECTED_STATUS")
    return result


def listener_pid(port: int = 8766) -> dict:
    if os.name != "nt":
        return {"state": "NOT_WINDOWS", "pid": None}
    try:
        proc = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True,
                              text=True, timeout=8, check=True)
    except (OSError, subprocess.SubprocessError):
        return {"state": "UNKNOWN", "pid": None}
    found = set()
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[3].upper() == "LISTENING":
            if parts[1].rsplit(":", 1)[-1] == str(port) and parts[1].startswith(("127.0.0.1:", "[::1]:")):
                if parts[4].isdigit():
                    found.add(int(parts[4]))
    return {"state": "UNIQUE" if len(found) == 1 else "AMBIGUOUS" if found else "NOT_FOUND",
            "pid": next(iter(found)) if len(found) == 1 else None}


def disk_hashes(repo: Path, client: Path) -> dict:
    paths = {
        "source_main": repo / "windows-relay" / "content.js",
        "source_temp": repo / "windows-relay" / "extension" / "content.js",
        "source_persistent": repo / "windows-relay" / "extension-persistent" / "content.js",
        "client_main": client / "content.js",
        "client_temp": client / "extension" / "content.js",
        "client_persistent": client / "extension-persistent" / "content.js"
    }
    hashes = {key: digest(path) if path.is_file() else None for key, path in paths.items()}
    source_equal = (all(hashes[x] is not None for x in ("source_main","source_temp","source_persistent"))
                    and len({hashes[x] for x in ("source_main","source_temp","source_persistent")}) == 1)
    client_equal = (all(hashes[x] is not None for x in ("client_main","client_temp","client_persistent"))
                    and len({hashes[x] for x in ("client_main","client_temp","client_persistent")}) == 1)
    return {
        "sha256": hashes, "source_mirrors_equal": source_equal,
        "client_mirrors_equal": client_equal,
        "disk_source_equals_client": bool(source_equal and client_equal and
                                          hashes["source_main"] == hashes["client_main"]),
        "active_loaded_script_sha256": None,
        "active_loaded_script_status": "NOT_VERIFIED"
    }


def observe(repo: Path, client: Path, port: int = 8766) -> dict:
    status = listener_status(port)
    owner = listener_pid(port)
    status["pid"] = owner["pid"]
    status["pid_state"] = owner["state"]
    hashes = disk_hashes(repo, client)
    return {
        "schema": "pce14-readonly-surface-v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "listener": status,
        "content_scripts": hashes,
        "capabilities": {
            "listener_socket": "PASS" if status["tcp"] == "REACHABLE" else "FAIL",
            "unauthenticated_endpoint_denied": ("PASS" if status["http"] == "EXPECTED_401"
                                                 else "BLOCKED" if status["http"] == "UNKNOWN" else "FAIL"),
            "listener_pid_identity": "PASS" if owner["state"] == "UNIQUE" else "BLOCKED",
            "source_mirror_consistency": "PASS" if hashes["source_mirrors_equal"] else "FAIL",
            "client_mirror_consistency": "PASS" if hashes["client_mirrors_equal"] else "FAIL",
            "source_runtime_disk_parity": "PASS" if hashes["disk_source_equals_client"] else "FAIL",
            "actual_loaded_runtime": "NOT_RUN",
            "real_paste_send_and_receipt": "NOT_RUN"
        },
        "notice": ("Read-only local evidence; no proof of current browser runtime, "
                   "successful UI submission, or 12h/24h reliability.")
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Safe localhost/disk capability probe")
    parser.add_argument("--repo", type=Path, default=Path.home() / "Downloads/Dev/GPT/GPT-Windows-Relay")
    parser.add_argument("--client", type=Path, default=Path.home() / "Downloads/Dev/GPT/Client/Relay")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port out of range")
    report = observe(args.repo, args.client, args.port)
    try:
        write_once(args.output, report)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print("RELAY_SURFACE_BENCHMARK " + json.dumps({
        "capabilities": report["capabilities"], "report": str(args.output)
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
