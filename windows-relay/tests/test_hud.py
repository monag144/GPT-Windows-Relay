import unittest
import io,json
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
import hud

class HudTests(unittest.TestCase):
 def test_latest_action_and_inflight(self):
  s={'processed':{'a':{'status':'OK','finished_at':'2026-01-01T00:00:00+00:00'},'b':{'status':'INFLIGHT','started_at':'2026-01-02T00:00:00+00:00'}}}
  cur,last=hud.latest_actions(s); self.assertEqual(cur[0][0],'b'); self.assertEqual(last[0],'b')

 def test_browser_state_tracks_runtime_and_recent_event(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc)
  events=[
   {'time':(now-timedelta(seconds=30)).isoformat(),'event':'content_script_started','detail':{'runtime':'v11-test','browser_id':'firefox'}},
   {'time':(now-timedelta(seconds=5)).isoformat(),'event':'action_result','detail':{'browser_id':'firefox'}},
  ]
  x=hud.browser_state(events,now); self.assertEqual(x['state'],'ACTIVE'); self.assertEqual(x['runtime'],'v11-test'); self.assertEqual(x['event'],'action_result'); self.assertEqual(x['browser_id'],'firefox')

 def test_browser_state_unknown_without_events(self):
  self.assertEqual(hud.browser_state([])['state'],'UNKNOWN')

 def test_idle_browser_age_does_not_mean_stalled(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc)
  events=[{'time':(now-timedelta(seconds=601)).isoformat(),'event':'content_port_connected','detail':{'browser_id':'firefox'}}]
  browser=hud.browser_state(events,now)
  self.assertEqual(browser['state'],'IDLE')
  self.assertEqual(hud.headline(True,{'phase':'READY'},browser),'READY')
  self.assertEqual(hud.headline(True,{'phase':'STALLED'},browser),'STALLED')
  self.assertEqual(hud.headline(True,{'phase':'READY'},{'state':'DISCONNECTED'}),'STALLED')

 def test_lifecycle_prefers_exact_backend_inflight_action(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc)
  state={'active_action':{'id':'op-400','status':'INFLIGHT','started_at':(now-timedelta(seconds=7)).isoformat(),'command':'Write-Output hello'}}
  x=hud.lifecycle([],state,now)
  self.assertEqual(x['phase'],'RUNNING'); self.assertEqual(x['packet_id'],'op-400'); self.assertEqual(x['age'],7)
  detail,active=hud.action_detail(state); self.assertTrue(active); self.assertEqual(detail['command'],'Write-Output hello')

 def test_engineering_collapsed_render_is_visible_without_consumer_mission(self):
  now=datetime(2026,10,8,2,0,0,tzinfo=timezone.utc)
  events=[{'time':(now-timedelta(seconds=2)).isoformat(),
           'event':'relay_engineering_action_render_collapsed',
           'detail':{'previous_result_id':'PCE10.017','safe_replay':False}}]
  life=hud.lifecycle(events,{},now)
  self.assertEqual(life['phase'],'RENDER COLLAPSED')
  self.assertIn('replay blocked',life['reason'])
  self.assertEqual(hud.headline(True,life,{'state':'ACTIVE'}),'RENDER COLLAPSED')
  self.assertEqual(hud.browser_state(events,now)['event'],'relay_engineering_action_render_collapsed')

 def test_lifecycle_explains_scanner_stall(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc)
  events=[{'time':(now-timedelta(seconds=3)).isoformat(),'event':'relay_scanner_stalled','detail':{'packet_id':'op-399','browser_id':'firefox'}}]
  x=hud.lifecycle(events,{},now)
  self.assertEqual(x['phase'],'STALLED'); self.assertEqual(x['packet_id'],'op-399'); self.assertIn('not consumed',x['reason'])

 def test_discovered_headline_uses_dynamic_operation_series(self):
  self.assertEqual(hud.operation_label('PCENG-A6.396-approval-helper-source-map'),'A6.396')
  self.assertEqual(hud.operation_label('PCENG-A7.001-next-agent'),'A7.001')

 def test_approval_required_is_distinct_from_stalled(self):
  browser={'state':'ACTIVE'}
  self.assertEqual(hud.headline(True,{'phase':'APPROVAL REQUIRED'},browser),'APPROVAL REQUIRED')
  self.assertNotEqual(hud.headline(True,{'phase':'APPROVAL REQUIRED'},browser),'STALLED')

 def test_command_preview_is_compact(self):
  self.assertEqual(hud.command_preview('a\n  b'),'a b')
  self.assertLessEqual(len(hud.command_preview('x'*200)),92)

 def test_recovery_advice_is_not_silent_ready(self):
  now=datetime(2026,10,6,2,0,10,tzinfo=timezone.utc)
  events=[{'time':'2026-10-06T02:00:00+00:00','event':'gpt_recovery_advice_observed','detail':{'incident_id':'RECOVERY-A7.1'}}]
  life=hud.lifecycle(events,{},now)
  self.assertEqual(life['phase'],'RECOVERY ADVICE')
  self.assertEqual(hud.headline(True,life,{'state':'ACTIVE'}),'RECOVERY ADVICE')

 def test_invalid_recovery_advice_is_explicit_failure_state(self):
  now=datetime(2026,10,6,2,0,10,tzinfo=timezone.utc)
  events=[{'time':'2026-10-06T02:00:00+00:00','event':'gpt_recovery_advice_invalid','detail':{'incident_id':'RECOVERY-A7.1'}}]
  life=hud.lifecycle(events,{},now)
  self.assertEqual(life['phase'],'RECOVERY INVALID')
  self.assertEqual(hud.headline(True,life,{'state':'ACTIVE'}),'RECOVERY INVALID')

 def test_once_cli_prints_snapshot_and_exits(self):
  expected={"title":"READY","online":True}
  with patch.object(hud,"snapshot",return_value=expected), patch("sys.stdout",new_callable=io.StringIO) as out:
   self.assertEqual(hud.main(["--once"]),0)
  self.assertEqual(json.loads(out.getvalue()),expected)


 def test_watchdog_reconciles_hud_before_listener_shortcut(self):
  from pathlib import Path
  text=(Path(hud.__file__).resolve().parent/'relay-watchdog-loop.ps1').read_text(encoding='utf-8')
  self.assertIn('GPT_RELAY_WATCHDOG_HUD_RECONCILIATION_V1',text)
  self.assertIn('function GenuineHudProcesses',text)
  self.assertIn('function EnsureHud',text)
  call='EnsureHud # GPT_RELAY_WATCHDOG_HUD_RECONCILE_CALL_V1'
  self.assertIn(call,text)
  self.assertLess(text.index(call),text.index('if(Listener)'))



 def test_github_approval_autoclick_is_exact_and_bottom_gated(self):
  from pathlib import Path
  text=(Path(hud.__file__).resolve().parent/'extension'/'content.js').read_text(encoding='utf-8')
  self.assertIn('GPT_CHATGPT_GITHUB_APPROVAL_AUTOCLICK_V1',text)
  self.assertIn("provider==='GitHub'",text)
  self.assertIn('allow chatgpt to use github\\?',text.lower())
  self.assertIn("/^always allow$/i",text)
  self.assertIn("/^deny$/i",text)
  self.assertIn("/^allow once$/i",text)
  self.assertIn('nearBottom(approvalScrollRoot)',text)
  self.assertIn("choice:'Always allow'",text)



 def test_result_dedupe_has_current_turn_wrapper_fallback(self):
  from pathlib import Path
  text=(Path(hud.__file__).resolve().parent/'extension'/'content.js').read_text(encoding='utf-8')
  self.assertIn('GPT_WINDOWS_RESULT_TURN_WRAPPER_FALLBACK_V1',text)
  self.assertIn('RESULT_TURN_SELECTOR',text)
  self.assertIn('article[data-testid^="conversation-turn-"]',text)
  self.assertIn('explicitAssistant && !explicitUser',text)
  self.assertIn('resultPacketIdFromUserUnit(nodes[i])===packetId',text)



 def test_operator_stop_start_controls_are_bound_to_pause_interlock(self):
  from pathlib import Path
  root=Path(hud.__file__).resolve().parent
  source=(root/'hud.py').read_text(encoding='utf-8')
  start=(root/'START-RELAY.bat').read_text(encoding='utf-8')
  stop=(root/'STOP-RELAY.bat').read_text(encoding='utf-8')
  control=(root/'relay-control.ps1').read_text(encoding='utf-8')
  self.assertIn('GPT_RELAY_HUD_OPERATOR_STOP_START_V1',source)
  self.assertIn('command=lambda:relay_control("stop")',source)
  self.assertIn('command=lambda:relay_control("start")',source)
  self.assertIn("Join-Path $root '.relay-paused'",control)
  self.assertIn('relay-control.ps1" start',start)
  self.assertIn('relay-control.ps1" stop',stop)
  self.assertNotIn('`r`n',start)
  self.assertNotIn('`r`n',stop)

 def test_hud_has_no_hidden_right_click_exit(self):
  from pathlib import Path
  source=(Path(hud.__file__).resolve().parent/'hud.py').read_text(encoding='utf-8')
  self.assertIn('GPT_RELAY_HUD_NO_HIDDEN_RIGHT_CLICK_EXIT_V1',source)
  self.assertNotIn('root.bind("<Button-3>",lambda _e:root.destroy())',source)

 def test_watchdog_source_is_single_and_not_replacement_corrupted(self):
  from pathlib import Path
  text=(Path(hud.__file__).resolve().parent/'relay-watchdog-loop.ps1').read_text(encoding='utf-8')
  self.assertEqual(text.count('function GenuineSupervisors'),1)
  self.assertEqual(text.count('function GenuineHudProcesses'),1)
  self.assertEqual(text.count('WATCHDOG_START pid='),1)
  self.assertEqual(text.count("GPTWindowsRelayWatchdog"),1)
  self.assertIn('GPT_RELAY_WATCHDOG_HUD_RECONCILE_CALL_V1',text)


 def test_operator_stop_is_presented_as_stopped(self):
  from pathlib import Path
  root=Path(hud.__file__).resolve().parent
  source=(root/'hud.py').read_text(encoding='utf-8')
  stop=(root/'STOP-RELAY.bat').read_text(encoding='utf-8')
  control=(root/'relay-control.ps1').read_text(encoding='utf-8')
  self.assertIn('intent=control_state()',source)
  self.assertIn('title_phase=headline(online,life,browser) if intent=="RUNNING" else intent',source)
  self.assertIn('if intent=="STOPPED":',source)
  self.assertIn('Relay STOPPED • operator stop',source)
  self.assertIn("$q=if($verified){'VERIFIED'}else{'UNVERIFIED'}",control)
  self.assertIn("BROWSER_QUIESCENCE=",control)
  self.assertIn("GENERATION=",control)
  self.assertIn("if($Action -eq 'stop'){Write-Output ('STOPPED BROWSER_QUIESCENCE='+$q+' GENERATION='+$stopGeneration)}",control)
  self.assertIn("else{Write-Output ('PAUSED BROWSER_QUIESCENCE='+$q+' GENERATION='+$stopGeneration)}",control)
  self.assertIn('Relay is STOPPED.',stop)



 def test_retry_control_is_explicit(self):
  from pathlib import Path
  root=Path(hud.__file__).resolve().parent
  source=(root/'hud.py').read_text(encoding='utf-8')
  control=(root/'relay-control.ps1').read_text(encoding='utf-8')
  self.assertIn('text="RETRY"',source)
  self.assertIn('relay_control("retry")',source)
  self.assertIn("$Action -eq 'retry'",control)


if __name__=='__main__':unittest.main()
