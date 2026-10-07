from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "windows-relay"
GIT = Path(r"C:\Program Files\Git\cmd\git.exe")
PY = Path.home() / "Downloads" / "Dev" / "GPT" / "Client" / "Relay" / ".venv" / "Scripts" / "python.exe"
ROLLBACK_ROOT = Path.home() / "Downloads" / "Dev" / "GPT" / "Client" / "Relay" / "rollback"

FILES = (
    Path("windows-relay/relay-control.ps1"),
    Path("windows-relay/relay-watchdog-loop.ps1"),
    Path("windows-relay/tests/test_hud.py"),
)

CONTROL_NORMAL_OLD = r'''    Start-Process powershell.exe -WindowStyle Normal -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"'+$run+'\"')) | Out-Null'''
CONTROL_NORMAL_NEW = r'''    Start-Process powershell.exe -WindowStyle Normal -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $run + '"')) | Out-Null'''
CONTROL_HIDDEN_OLD = r'''    Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"'+$watchdog+'\"')) | Out-Null'''
CONTROL_HIDDEN_NEW = r'''    Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $watchdog + '"')) | Out-Null'''
WATCHDOG_HUD_OLD = r'''  Start-Process -FilePath $hudPy -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @(('\"' + $hud + '\"')) | Out-Null'''
WATCHDOG_HUD_NEW = r'''  Start-Process -FilePath $hudPy -WindowStyle Hidden -WorkingDirectory $root -ArgumentList @(('"' + $hud + '"')) | Out-Null'''

TEST_METHOD = r'''
 def test_control_launch_paths_quote_space_paths_without_backslashes(self):
  from pathlib import Path
  root=Path(hud.__file__).resolve().parent
  control=(root/'relay-control.ps1').read_text(encoding='utf-8')
  watchdog=(root/'relay-watchdog-loop.ps1').read_text(encoding='utf-8')
  self.assertIn("('\"' + $run + '\"')",control)
  self.assertIn("('\"' + $watchdog + '\"')",control)
  self.assertIn("('\"' + $hud + '\"')",watchdog)
  launch_lines=[x for x in (control+'\\n'+watchdog).splitlines() if 'Start-Process' in x and '-ArgumentList' in x and ('$run' in x or '$watchdog' in x or '$hud' in x)]
  self.assertEqual(len(launch_lines),3)
  for x in launch_lines:
   self.assertNotIn('\\\\\"',x)

 def test_powershell_start_process_handles_space_paths(self):
  import os,subprocess,tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory(prefix='relay quote ') as d:
   root=Path(d)
   script=root/'probe script.ps1'
   out=root/'probe result.txt'
   script.write_text("param([string]$Out)\\nSet-Content -LiteralPath $Out -Value 'GREEN' -Encoding ASCII\\n",encoding='utf-8')
   env=os.environ.copy()
   env['PCE_SCRIPT']=str(script)
   env['PCE_OUT']=str(out)
   ps="$s=$env:PCE_SCRIPT; $o=$env:PCE_OUT; $p=Start-Process powershell.exe -PassThru -Wait -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('\"' + $s + '\"'),'-Out',('\"' + $o + '\"')); exit $p.ExitCode"
   cp=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-Command',ps],env=env,text=True,capture_output=True,check=False)
   self.assertEqual(cp.returncode,0,cp.stderr)
   self.assertTrue(out.is_file(),cp.stdout+cp.stderr)
   self.assertEqual(out.read_text(encoding='ascii').strip(),'GREEN')
'''


def run(args, *, cwd=REPO, capture=False):
    cp = subprocess.run(
        [str(x) for x in args],
        cwd=str(cwd),
        text=True,
        capture_output=capture,
        check=False,
    )
    if capture:
        if cp.stdout:
            print(cp.stdout, end="")
        if cp.stderr:
            print(cp.stderr, end="", file=sys.stderr)
    if cp.returncode != 0:
        raise RuntimeError(f"command failed rc={cp.returncode}: {' '.join(map(str, args))}")
    return cp


def require_clean():
    cp = run([GIT, "status", "--porcelain"], capture=True)
    if cp.stdout.strip():
        raise RuntimeError("working tree is not clean before PCE7.447")


def backup():
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dst = ROLLBACK_ROOT / f"PCE7.447-source-pre-start-quote-fix-{stamp}"
    if dst.exists():
        raise RuntimeError(f"rollback already exists: {dst}")
    for rel in FILES:
        src = REPO / rel
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    print(f"BACKUP={dst}")
    return dst


def restore(dst: Path):
    for rel in FILES:
        shutil.copy2(dst / rel, REPO / rel)
    print("PCE7.447_SOURCE_ROLLBACK_COMPLETE", file=sys.stderr)


def replace_exact(path: Path, old: str, new: str):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"guard failed for {path.name}: expected 1 match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_sources():
    control = ROOT / "relay-control.ps1"
    watchdog = ROOT / "relay-watchdog-loop.ps1"
    tests = ROOT / "tests" / "test_hud.py"

    replace_exact(control, CONTROL_NORMAL_OLD, CONTROL_NORMAL_NEW)
    replace_exact(control, CONTROL_HIDDEN_OLD, CONTROL_HIDDEN_NEW)
    replace_exact(watchdog, WATCHDOG_HUD_OLD, WATCHDOG_HUD_NEW)

    text = tests.read_text(encoding="utf-8")
    old_test_name = "test_control_launch_paths_use_powershell_native_quote_escaping"
    new_test_name = "test_control_launch_paths_quote_space_paths_without_backslashes"
    if old_test_name in text or new_test_name in text:
        raise RuntimeError("launch-path regression test already present")
    marker = "\n\nif __name__=='__main__':unittest.main()\n"
    if marker not in text:
        raise RuntimeError("test insertion anchor missing")
    tests.write_text(text.replace(marker, "\n" + TEST_METHOD + marker, 1), encoding="utf-8")


def main():
    require_clean()
    rb = backup()
    try:
        patch_sources()
        run([PY, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=ROOT)
        run([GIT, "diff", "--check"], cwd=REPO)
        print("PCE7.447_SOURCE_TESTS_GREEN")
        run(
            [GIT, "--no-pager", "diff", "--"] + [str(x).replace("/", "\\") for x in FILES],
            cwd=REPO,
            capture=True,
        )
        return 0
    except BaseException as exc:
        restore(rb)
        print(f"PCE7.447_FAILED={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
