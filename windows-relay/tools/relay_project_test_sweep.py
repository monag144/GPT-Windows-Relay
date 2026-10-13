"""2026-10-12 full repository unittest sweep; no logs/backups written to disk.

Run from canonical source with `python -B`. Separately test Windows Relay
and One-Click Go consumer, and print bounded results to stdout only.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITES = (
    ("windows-relay", ROOT / "windows-relay"),
    ("consumer", ROOT / "consumer"),
)
MAX_SECONDS_PER_SUITE = 125


def one_suite(name: str, cwd: Path) -> dict:
    if not (cwd / "tests").is_dir():
        return {"suite": name, "outcome": "MISSING_TEST_FOLDER", "exit_code": None}
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    args = [
        sys.executable, "-B", "-m", "unittest", "discover",
        "-s", "tests", "-p", "test_*.py", "-q",
    ]
    started = time.monotonic()
    try:
        response = subprocess.run(
            args, cwd=str(cwd), env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=MAX_SECONDS_PER_SUITE, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"suite": name, "outcome": "TIMEOUT", "seconds": MAX_SECONDS_PER_SUITE,
                "exit_code": None}
    except OSError as exc:
        return {"suite": name, "outcome": "RUNNER_ERROR",
                "error_type": type(exc).__name__, "exit_code": None}

    combined = response.stdout + "\n" + response.stderr
    summary = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", combined)
    failures = re.findall(r"(?m)^(?:FAIL|ERROR): ([^\r\n]+)", combined)
    traceback_endings = re.findall(
        r"(?m)^(?:AssertionError|AttributeError|TypeError|ValueError|"
        r"RuntimeError|FileNotFoundError|PermissionError|ModuleNotFoundError|"
        r"ImportError|SyntaxError|windows_relay\.RelayError):[^\r\n]*",
        combined,
    )
    final_summary = re.search(r"(?m)^(FAILED \([^\r\n]+\)|OK(?: \([^\r\n]*\))?)$", combined)
    return {
        "suite": name,
        "outcome": "PASS" if response.returncode == 0 else "FAIL",
        "exit_code": response.returncode,
        "seconds": round(time.monotonic() - started, 2),
        "tests_executed": int(summary.group(1)) if summary else None,
        "unittest_summary": final_summary.group(1) if final_summary else "UNAVAILABLE",
        "failing_tests": failures[:35],
        "additional_failures_omitted": max(0, len(failures) - 35),
        # Avoid 7 KB traceback tails printing entire HUD/source files:
        # capture short per-error exception summaries and test identities only.
        "exception_messages": [line[:480] for line in traceback_endings[:35]],
        "exception_messages_omitted": max(0, len(traceback_endings)-35),
    }


def main() -> int:
    results = []
    for name, cwd in SUITES:
        print("RUNNING_OFFLINE_UNITTEST_SUITE=" + name, flush=True)
        item = one_suite(name, cwd)
        results.append(item)
        print(json.dumps(item, indent=2, sort_keys=True), flush=True)
    passed = all(x["outcome"] == "PASS" for x in results)
    print("REPOSITORY_TEST_SWEEP=" + ("PASS" if passed else "HAS_FAILURES"), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
