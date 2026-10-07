import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HUD=(ROOT/'hud.py').read_text(encoding='utf-8')
CONTROL=(ROOT/'relay-control.ps1').read_text(encoding='utf-8')
WATCHDOG=(ROOT/'relay-watchdog-loop.ps1').read_text(encoding='utf-8')
class HudFullControlSurfacePce9Tests(unittest.TestCase):
 def test_hud_exposes_historical_five_control_surface(self):
  expected={'START':'command=lambda:relay_control("start")','STOP':'command=lambda:relay_control("stop")','RESTART':'command=lambda:relay_control("restart")','RETRY':'command=lambda:relay_control("retry")','OFF':'command=lambda:relay_control("off")','KILL':'command=lambda:relay_control("kill")'}
  for label,callback in expected.items():self.assertIn(f'text="{label}"',HUD,label);self.assertIn(callback,HUD,callback)
 def test_retry_control_is_preserved_alongside_delivery_retry_state(self):
  self.assertIn('text="RETRY"',HUD);self.assertIn('relay_control("retry")',HUD);self.assertIn('relay_result_delivery_retry_deferred',HUD)
 def test_backend_accepts_off_and_kill_without_losing_existing_verbs(self):
  for verb in ('status','start','stop','restart','pause','resume','retry','off','kill'):self.assertRegex(CONTROL,rf'(?i)[\'\"]{verb}[\'\"]')
  self.assertRegex(CONTROL,r'(?i)\$Action\s*-eq\s*[\'\"]off[\'\"]');self.assertRegex(CONTROL,r'(?i)\$Action\s*-eq\s*[\'\"]kill[\'\"]')
 def test_minimize_and_watchdog_operator_intent_contract(self):
  self.assertIn('text="—"',HUD);self.assertIn('min_btn.configure(command=minimize_hud)',HUD);self.assertIn('root.iconify()',HUD)
  for token in ('KILL FAILED','KILLING RELAY','KILLING HUD'):self.assertIn(token,HUD)
  for token in ('WATCHDOG_OFF_LATCH_EXIT','WATCHDOG_KILL_LATCH_EXIT',"$off=Join-Path $root '.relay-off'","$kill=Join-Path $root '.relay-kill'"):self.assertIn(token,WATCHDOG)
 def test_start_and_restart_clear_shutdown_latches_and_relaunch_watchdog(self):
  clear=r'Remove-Item \$pause,?\$?off?,?\$?kill?.*'
  self.assertRegex(CONTROL,r'(?s)if\(\$Action -eq \'restart\'\)\{.*?Remove-Item \$off,\$kill,\$killHud,\$killFailed.*?StartWatchdog.*?StartSupervisor')
  self.assertRegex(CONTROL,r'(?s)elseif\(\$Action -in @\(\'start\',\'resume\'\)\) \{.*?Remove-Item \$pause,\$off,\$kill,\$killHud,\$killFailed.*?StartWatchdog.*?StartSupervisor')
  self.assertGreaterEqual(CONTROL.count('StartWatchdog'),3)
if __name__=='__main__':unittest.main()
