"""Ensure native ChatGPT relay reuses the original top-right HUD exclusively."""
from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD = (ROOT / "hud.py").read_text(encoding="utf-8")
LAUNCH = (ROOT / "START-CHATGPT-DESKTOP-NATIVE.cmd").read_text(encoding="utf-8")
RECONCILE = (ROOT / "tools" / "Reconcile-OriginalDesktopHUD.ps1").read_text(encoding="utf-8")
NATIVE = (ROOT / "desktop_native_relay.py").read_text(encoding="utf-8")

class OriginalHUDReuseTests(unittest.TestCase):
    def test_existing_top_right_layout_retained(self):
        self.assertIn("W,COMPACT_H,EXPANDED_H=560,184,386", HUD)
        self.assertIn("root.overrideredirect(True)", HUD)
        for label in ("START", "STOP", "RESTART", "OFF", "KILL"):
            self.assertIn("text=\""+label+"\"", HUD)
        self.assertIn("OWNER LOCK: ?", HUD)
        self.assertIn("NATIVE_MODE_FILE", HUD)
        self.assertIn("native_snapshot()", HUD)

    def test_native_status_and_buttons_do_not_touch_browser(self):
        self.assertIn("def native_control(action):", HUD)
        self.assertIn("def native_snapshot():", HUD)
        self.assertIn("if native_mode():", HUD)
        self.assertIn("native_control(action)", HUD)
        self.assertIn("OWNER LOCK: N/A", HUD)
        self.assertIn("if native_mode():return", HUD)
        self.assertIn("native_action=", HUD)
        self.assertIn("choices=(\"run\", \"arm\", \"stop\", \"off\", \"restart\", \"kill\"", NATIVE)

    def test_native_hud_exposes_blocked_sender_without_new_window(self):
        self.assertIn("delivery_blocked=bool(report.get('delivery_blocked'))", HUD)
        self.assertIn("DELIVERY BLOCKED", HUD)
        self.assertIn("last_delivery_error", HUD)
        self.assertIn("title='STALLED'", HUD)
        self.assertIn("Auto Send: OFF", HUD)
        self.assertIn("Auto Send: ON", HUD)
        self.assertIn("def native_auto_send(enabled):", HUD)
        self.assertIn("auto-send-on", NATIVE)
        self.assertIn("auto-send-off", NATIVE)
        self.assertIn('if not cfg["auto_send"] and not delivery_force_clear_path(aid).is_file():', NATIVE)
        self.assertIn("FORCE RESEND", HUD)
        self.assertIn("ABORT SEND", HUD)
        self.assertIn("Reconcile a known receipt", HUD)
        self.assertIn("messagebox.askyesno(\"Force Resend\"", HUD)
        self.assertIn("CLEAR QUEUE", HUD)
        self.assertIn("abort-delivery", NATIVE)
        self.assertIn("clear-pending-deliveries", NATIVE)
        self.assertIn("force-delivery", NATIVE)
        self.assertIn('native_delivery_control("force-delivery",aid)', HUD)
        self.assertIn("def focus_chatgpt_for_forced_delivery():", HUD)
        self.assertIn("ChatGPT could not be brought to the foreground", HUD)

    def test_native_arm_and_big_go_preserve_original_hud_controls(self):
        self.assertIn("'native_armed':armed, 'native_off':off",HUD)
        self.assertIn('start_btn.configure(text="ARMED" if armed else "ARM"',HUD)
        self.assertIn('command=lambda:relay_control("start")',HUD)
        self.assertIn('start_btn.configure(text="START",state="normal"',HUD)
        self.assertIn('go_btn=tk.Button(footer,text="GO"',HUD)
        self.assertIn('font=("Segoe UI",11,"bold")',HUD)
        self.assertIn('go_btn.pack(side="right",padx=(5,0))',HUD)
        self.assertIn('auto_send_btn.pack(side="right")',HUD)
        self.assertLess(HUD.index('go_btn.pack(side="right"'),HUD.index('auto_send_btn.pack(side="right")'))
        self.assertIn('go_btn.configure(command=on_go)',HUD)
        self.assertIn('courier_hud_cli("go")',HUD)
        self.assertIn('name="command-courier-go",daemon=True',HUD)
        self.assertIn('GO…',HUD)
        action=HUD.split('    def on_go():',1)[1].split('    go_btn.configure(command=on_go)',1)[0]
        for forbidden in ('force-delivery','abort-delivery','clear-pending-deliveries',
                          'native_delivery_control(','relay_control(','consumer/GO.bat'):
            self.assertNotIn(forbidden,action)

    def test_go_status_depends_on_receiver_and_native_policy(self):
        self.assertIn("'native_phase':phase",HUD)
        self.assertIn('go_state["waiting"]=(kind=="waiting")',HUD)
        self.assertIn('COURIER_GO=WAITING_FOR_DESTINATION',HUD)
        self.assertIn('destination_ready=(snap.get("native_phase")',HUD)
        self.assertIn('not armed or snap.get("native_off")',HUD)
        self.assertIn('go_btn.configure(text="GO…" if go_state["busy"] else',HUD)
        self.assertIn('go_results.put(("waiting",None))',HUD)

    def test_recovery_buttons_follow_actual_last_delivery_phase(self):
        self.assertIn("'native_delivery_phase':delivery_phase",HUD)
        self.assertIn("delivery_phase=snap.get('native_delivery_phase')",HUD)
        self.assertIn("delivery_phase=='PRE_SUBMIT_FAILED' else 'disabled'",HUD)
        self.assertIn("delivery_phase in ('READY','PRE_SUBMIT_FAILED')",HUD)
        self.assertNotIn("force_command_btn.configure(state='normal');",HUD)

    def test_details_panel_is_not_rewritten_when_content_unchanged(self):
        self.assertIn('details_cache={"text":None}',HUD)
        self.assertIn('if value==details_cache["text"]:return',HUD)
        self.assertLess(HUD.index('if value==details_cache["text"]:return'),
                        HUD.index('details.configure(state="normal"); details.delete('))

    def test_hud_reconcile_reuses_existing_visible_process_until_source_changes(self):
        for marker in (
            "Get-Item -LiteralPath $original",
            "LastWriteTimeUtc",
            "StartTime.ToUniversalTime()",
            "if($reusable)",
            "ORIGINAL_HUD_START=EXISTING_PROCESS_REUSED",
            "ORIGINAL_HUD_OLD_CODE_RESTARTED",
            "for($i=0;$i -lt 12;$i++)",
            "ORIGINAL_HUD_VISIBLE_WINDOW_COUNT=",
        ):
            self.assertIn(marker,RECONCILE)
        self.assertLess(RECONCILE.index("if($reusable)"),
                        RECONCILE.index("Stop-HudProcess $p 'ORIGINAL_HUD_OLD_CODE_RESTARTED'"))
        self.assertNotIn("Start-Process -WindowStyle Hidden",RECONCILE)

    def test_desktop_launcher_never_starts_mini_hud(self):
        self.assertIn("hud-mode", LAUNCH)
        self.assertIn("Reconcile-OriginalDesktopHUD.ps1", LAUNCH)
        self.assertNotIn("desktop_native_hud.py", LAUNCH)
        self.assertNotIn("START-GPT-WINDOWS-RELAY.bat", LAUNCH)
        self.assertFalse((ROOT / "desktop_native_hud.py").exists())

    def test_reconciliation_affects_only_canonical_hud_files(self):
        self.assertIn("desktop_native_hud.py", RECONCILE)
        self.assertIn("hud.py", RECONCILE)
        self.assertIn("Get-CimInstance Win32_Process", RECONCILE)
        self.assertIn("StringComparison]::OrdinalIgnoreCase", RECONCILE)
        self.assertIn("ORIGINAL_HUD_FILE=hud.py", RECONCILE)
        self.assertIn("ORIGINAL_HUD_TRANSPORT=NATIVE_CHATGPT_APP", RECONCILE)
        self.assertIn("$label+'_ALREADY_EXITED_PID='", RECONCILE)
        self.assertIn("$label+'_STOP_FAILED_PID='", RECONCILE)
        self.assertIn("ORIGINAL_HUD_VISIBLE_WINDOW_COUNT=", RECONCILE)
        self.assertIn("ORIGINAL_HUD_HOST_PROCESS_COUNT=", RECONCILE)
        self.assertNotIn("relay-control.ps1", RECONCILE)
        self.assertNotIn("http://127.0.0.1", RECONCILE)

if __name__ == "__main__":
    unittest.main()
