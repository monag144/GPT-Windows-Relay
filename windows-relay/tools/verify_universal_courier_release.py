"""Validate both suites without leaking unittest stderr into PowerShell errors.

Only records test outcomes; never touches the running engine, HUD, queue or
operator's main worktree. Called before any cutover side effects.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def suite(name: str, cwd: Path, args: list[str]) -> bool:
    try:
        process = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", *args],
            cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=170,
        )
        output = process.stdout + "\n" + process.stderr
        totals = re.findall(r"Ran \d+ tests? in [^\r\n]+", output)
        summaries = re.findall(r"^(?:OK|FAILED[^\r\n]*)$", output, re.M)
        names = re.findall(r"^(?:FAIL|ERROR):[^\r\n]*", output, re.M)
        passed = process.returncode == 0
        print(
            name + "=" + ("PASS" if passed else "FAIL")
            + "; " + (totals[-1] if totals else "NO_TEST_COUNT")
            + "; " + (summaries[-1] if summaries else "NO_RESULT"),
            flush=True,
        )
        if not passed:
            print(name + "_FAILING_TESTS=" + " | ".join(names[:15]), flush=True)
            # Include the assertion summaries as well as test names so
            # GitHub can be repaired without asking for the complete log.
            lines = output.splitlines()
            lines = [line.strip() for line in lines
                     if ("AssertionError:" in line or "SyntaxError:" in line
                         or "Error:" in line or "Traceback " in line
                         or "ModuleNotFoundError:" in line)]
            print(name + "_ASSERTIONS=" + " | ".join(lines[:15])[:1400], flush=True)
            print(name + "_LOG_TAIL=" + output[-1400:].replace("\r", " ").replace("\n", " | "),
                  flush=True)
        return passed
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(name + "_ERROR=" + type(exc).__name__, flush=True)
        return False


def main() -> int:
    relay = suite("RELAY", ROOT, ["windows-relay/tests", "-p", "test_*.py"])
    consumer = suite("CONSUMER", ROOT / "consumer", ["tests", "-p", "test_*.py"])
    good = relay and consumer
    print("OFFLINE_QUALIFICATION=" + ("PASS" if good else "FAIL"), flush=True)
    print("RUNTIME_RESTARTED=NO; JOURNAL_CHANGED=NO", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
