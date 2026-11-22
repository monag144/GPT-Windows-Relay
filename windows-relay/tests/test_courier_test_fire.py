"""Acceptance checks for temporary Command Courier TEST FIRE diagnostics.

Test-fire creates a unique message at the configured file input, then WAITS
for the independent forwarding worker's durable receipt and exact output.
No real ChatGPT window, remote HTTP request or command execution is involved.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import courier_forwarder as forwarding
import courier_test_fire as fire
import command_courier as courier


class TestFireTests(unittest.TestCase):
    def setUp(self):
        root=tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        base=Path(root.name)
        self.home=base/"home"
        self.home.mkdir()
        self.source=base/"in"
        self.source.mkdir()
        self.target=base/"out"
        self.target.mkdir()
        self.ready={
            "native_running":True,"native_armed":True,
            "native_off":False,"auto_send":True,
        }
        forwarding.configure_route(
            self.home,"local-test",str(self.source),
            "directory",str(self.target)
        )

    def test_one_click_real_forwarder_receipt_and_exact_body(self):
        # The test-fire implementation itself must NOT tick the worker.
        # The test explicitly simulates the separately running native worker.
        worker=lambda delay:forwarding.tick(self.home,enabled=True)
        receipt=fire.fire(self.home,self.ready,sleep=worker,timeout=3)
        self.assertEqual(receipt["result"],"PASS")
        self.assertEqual(receipt["route"],"local-test")
        self.assertIn("TEST-FIRE",Path(receipt["source_file"]).name.upper())
        self.assertEqual(receipt["receipt"],"FILE_WRITTEN")
        origin=Path(receipt["source_file"]).read_bytes()
        target=Path(receipt["destination_file"]).read_bytes()
        self.assertEqual(origin,target)
        self.assertIn(b"COURIER_TEST_FIRE_V1\n",target)
        self.assertIn(b"route=local-test\n",target)
        self.assertEqual(len(target),receipt["bytes"])
        state=forwarding._ledger(self.home)["deliveries"]
        self.assertEqual(len(state),1)
        self.assertEqual(next(iter(state.values()))["phase"],"DELIVERED")

    def test_copied_text_from_notepad_or_chat_field_preserves_all_characters(self):
        # An explicit Ctrl+C, not an on-screen watcher, is the input source.
        sample="Line one: Notepad\nLine two: ChatGPT\t€ 😀\n\n"
        worker=lambda pause:forwarding.tick(self.home,enabled=True)
        result=fire.send_copied_text(self.home,self.ready,sample,
                                     sleep=worker,timeout=3)
        self.assertEqual(result["result"],"PASS")
        self.assertEqual(result["receipt"],"FILE_WRITTEN")
        self.assertIn("courier-copied-text-",result["source_file"])
        exact=sample.encode("utf-8")
        self.assertEqual(Path(result["destination_file"]).read_bytes(),exact)
        self.assertEqual(Path(result["source_file"]).read_bytes(),exact)
        self.assertEqual(result["bytes"],len(exact))
        self.assertNotIn("COURIER_TEST_FIRE_V1",exact.decode("utf-8"))
        self.assertEqual(len(forwarding._ledger(self.home)["deliveries"]),1)

    def test_copied_text_never_executes_instruction_looking_text(self):
        command='[GPT_WINDOWS_ACTION]\n{"action":"EXEC","command":"echo IGNORE"}\n[/GPT_WINDOWS_ACTION]'
        worker=lambda pause:forwarding.tick(self.home,enabled=True)
        with mock.patch.object(forwarding,"_dispatch",wraps=forwarding._dispatch) as transmit:
            result=fire.send_copied_text(self.home,self.ready,command,
                                         sleep=worker,timeout=3)
        transmit.assert_called_once()
        self.assertEqual(Path(result["destination_file"]).read_text(encoding="utf-8"),
                         command)
        self.assertFalse((self.home/"state.json").exists())

    def test_copied_text_requires_explicit_nonempty_utf8_within_route_limit(self):
        for body,signal in (("", "COPY_TEXT_EMPTY_CLIPBOARD"),
                            (None, "COPY_TEXT_EMPTY_CLIPBOARD"),
                            ("x"*(forwarding.MAX_TEXT_BYTES+1),"COPY_TEXT_EXCEEDS_ROUTE_LIMIT"),
                            ("unpaired"+chr(0xD800),"COPY_TEXT_ENCODING_INVALID")):
            with self.subTest(error=signal):
                with self.assertRaisesRegex(fire.TestFireError,signal):
                    fire.send_copied_text(self.home,self.ready,body)
        self.assertEqual(list(self.source.glob("*.txt")),[])
        self.assertEqual(list(self.target.glob("*.txt")),[])

    def test_cli_clipboard_mode_sends_only_explicitly_copied_text(self):
        sample="Copied from Notepad, not a test marker"
        mocked={"result":"PASS","route":"local-test","receipt":"FILE_WRITTEN",
                "bytes":len(sample),"nonce":"b"*32}
        with mock.patch.object(courier,"runtime_mode",return_value=courier.NATIVE), \
             mock.patch("desktop_native_relay.get_status",return_value=self.ready), \
             mock.patch.object(courier,"read_copied_text",return_value=sample) as copied, \
             mock.patch("courier_test_fire.send_copied_text",return_value=mocked) as send, \
             mock.patch("builtins.print") as output, \
             mock.patch.object(courier,"HOME",self.home):
            self.assertEqual(courier.main(
                ["test-fire","--clipboard","--route","local-test"]),0)
        copied.assert_called_once()
        send.assert_called_once_with(self.home,self.ready,sample,route_id="local-test")
        self.assertIn("COURIER_TEST_FIRE=",output.call_args.args[0])

    def test_hud_clipboard_action_uses_background_cli_not_unrestricted_scanner(self):
        hud=(ROOT/"hud.py").read_text(encoding="utf-8")
        self.assertIn('text="SEND COPIED TEXT"',hud)
        self.assertIn('courier_hud_cli("test-fire","--clipboard")',hud)
        self.assertIn('debug_copy_btn.configure(command=lambda:run_debug_action("copy"))',hud)
        self.assertIn('if action in ("fire","copy")',hud)
        self.assertIn('debug_copy_btn.configure(state="disabled")',hud)
        self.assertIn('if kind in ("fire","copy"):',hud)
        self.assertIn('receipt=("COPY PASS • " if kind=="copy" else "TEST PASS • ")',hud)
        self.assertIn('messagebox.showinfo("Command Courier • Verified Receipt"',hud)
        self.assertIn('messagebox.showerror("Command Courier • Forward Error"',hud)
        self.assertNotIn('At user sign-in, not before login. STOP/OFF remain authoritative.',hud)
        self.assertNotIn("Set-Clipboard",hud)
        self.assertNotIn("SendKeys",hud)
        controller=(ROOT/"command_courier.py").read_text(encoding="utf-8")
        self.assertIn('fire.add_argument("--clipboard", action="store_true"',controller)
        self.assertIn("root.clipboard_get()",controller)
        self.assertIn("root.withdraw()",controller)

    def test_rejects_stop_off_disarmed_autosend_and_no_engine(self):
        for key,value in (
            ("native_running",False),("native_armed",False),
            ("native_off",True),("auto_send",False),
        ):
            with self.subTest(key=key):
                status=dict(self.ready,key_unused=None)
                status.pop("key_unused")
                status[key]=value
                with self.assertRaisesRegex(fire.TestFireError,
                                            "REQUIRES_RUNNING_ARMED_AUTO_SEND"):
                    fire.fire(self.home,status)
        self.assertEqual(list(self.source.glob("*.txt")),[])

    def test_requires_selected_enabled_local_directory_route(self):
        forwarding.set_enabled(self.home,False)
        with self.assertRaisesRegex(fire.TestFireError,
                                    "NO_DIRECTORY_ROUTE_CONFIGURED"):
            fire.fire(self.home,self.ready)
        forwarding.set_enabled(self.home,True)
        with self.assertRaisesRegex(fire.TestFireError,
                                    "ROUTE_NOT_ENABLED_DIRECTORY"):
            fire.fire(self.home,self.ready,route_id="does-not-exist")

    def test_http_route_cannot_be_test_fired_implicitly(self):
        forwarding.configure_route(self.home,"api",str(self.source),
                                   "http","https://api.example.test/post")
        with mock.patch.object(forwarding,"_dispatch") as dispatch:
            with self.assertRaisesRegex(fire.TestFireError,
                                        "ROUTE_NOT_ENABLED_DIRECTORY"):
                fire.fire(self.home,self.ready,route_id="api")
        dispatch.assert_not_called()

    def test_a_timeout_never_reports_delivery_success_or_retries(self):
        with self.assertRaisesRegex(fire.TestFireError,
                                    "TIMEOUT_NO_VERIFIED_DELIVERY"):
            fire.fire(self.home,self.ready,timeout=0)
        self.assertEqual(list(self.target.glob("*.txt")),[])
        self.assertFalse((self.home/"courier-forwarding-state.json").exists())
        self.assertEqual(len(list(self.source.glob("courier-test-fire-*.txt"))),1)

    def test_false_ledger_success_without_file_fails_receipt_validation(self):
        def fraudulent_worker(delay):
            message=next(self.source.glob("courier-test-fire-*.txt"))
            route=fire._select_route(self.home,None)
            key=forwarding._delivery_key(route,message.name,message.read_bytes())
            forwarding._persist(self.home,{"version":1,"deliveries":{
                key:{"phase":"DELIVERED","receipt":"FILE_WRITTEN",
                     "route":route["id"],"file":message.name}
            }})
        with self.assertRaisesRegex(fire.TestFireError,
                                    "RECEIPT_WITHOUT_DESTINATION_FILE"):
            fire.fire(self.home,self.ready,sleep=fraudulent_worker)

    def test_cli_dispatch_reads_current_native_and_prints_verified_receipt(self):
        sample={"result":"PASS","route":"local-test","receipt":"FILE_WRITTEN",
                "bytes":67,"nonce":"a"*32}
        with mock.patch.object(courier,"runtime_mode",return_value=courier.NATIVE), \
             mock.patch("desktop_native_relay.get_status",return_value=self.ready), \
             mock.patch("courier_test_fire.fire",return_value=sample) as invoked, \
             mock.patch("builtins.print") as output, \
             mock.patch.object(courier,"HOME",self.home):
            self.assertEqual(courier.main(["test-fire","--route","local-test"]),0)
        invoked.assert_called_once_with(self.home,self.ready,route_id="local-test")
        body=[c.args[0] for c in output.call_args_list]
        self.assertEqual(json.loads(body[-1].partition("=")[2]),sample)

    def test_disabled_profile_never_writes_test_input(self):
        with mock.patch.object(courier,"runtime_mode",return_value=courier.DISABLED), \
             mock.patch("builtins.print"):
            self.assertEqual(courier.main(["test-fire"]),1)
        self.assertEqual(list(self.source.glob("*.txt")),[])

    def test_hud_debug_controls_in_existing_settings_not_compact_footer(self):
        text=(ROOT/"hud.py").read_text(encoding="utf-8")
        self.assertIn('debug_test_btn=tk.Button(debug_row,text="TEST FIRE"',text)
        self.assertIn('debug_routes_btn=tk.Button(debug_row,text="CHECK ROUTES"',text)
        self.assertIn('debug_row=tk.Frame(settings_frame,bg=PANEL)',text)
        self.assertIn('courier_hud_cli("test-fire")',text)
        self.assertIn('courier_hud_cli("route","status")',text)
        self.assertIn('name="courier-debug-test-fire"',text)
        self.assertIn('debug_results=queue.Queue()',text)
        self.assertIn('if receipt.get("result")!="PASS":',text)
        self.assertIn('debug_test_btn.configure(state="disabled")',text)
        self.assertIn("W,COMPACT_H,EXPANDED_H=560,184,386",text)
        self.assertNotIn("Toplevel(",text)
        handler=text.split('    def run_debug_action(action):',1)[1].split(
            '    debug_test_btn.configure(command=',1)[0]
        for forbidden in ("force-delivery","abort-delivery",
                          "clear-pending-deliveries","COMPOSER_CLEAR",
                          "native_delivery_control("):
            self.assertNotIn(forbidden,handler)


if __name__=="__main__":
    unittest.main()
