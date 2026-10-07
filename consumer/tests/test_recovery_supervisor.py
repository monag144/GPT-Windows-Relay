import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

CONSUMER = Path(__file__).resolve().parents[1]
if str(CONSUMER) not in sys.path:
    sys.path.insert(0, str(CONSUMER))

import recovery_supervisor as rs


class RecoverySupervisorTests(unittest.TestCase):
    def snapshot(self, **updates):
        base = dict(
            sampled_at="2026-10-05T22:46:00+00:00",
            relay_online=True,
            armed=True,
            pending_missions=0,
            browser_id="edge",
            browser_expected=True,
            browser_connected=True,
            active_operation=None,
            last_operation=None,
            last_event=None,
            discovered_packet=None,
            discovered_age_seconds=None,
            discovery_stuck=False,
            approval_required=False,
        )
        base.update(updates)
        return rs.Snapshot(**base)

    def test_disconnected_browser_is_actionable_without_five_minute_wait(self):
        d = rs.decide(self.snapshot(browser_connected=False))
        self.assertEqual(d.phase, "RECOVERING")
        self.assertEqual(d.repair, "repair_browser")
        self.assertIn("disconnected", d.reason)

    def test_quiet_healthy_browser_is_idle_not_stalled(self):
        d = rs.decide(self.snapshot())
        self.assertEqual(d.phase, "IDLE")
        self.assertIsNone(d.repair)

    def test_approval_prompt_is_not_classified_as_relay_stall(self):
        d = rs.decide(self.snapshot(approval_required=True, last_event="chatgpt_tool_approval_prompt_detected"))
        self.assertEqual(d.phase, "APPROVAL REQUIRED")
        self.assertIsNone(d.repair)

    def test_discovery_without_progress_becomes_bounded_recovery(self):
        d = rs.decide(self.snapshot(
            discovery_stuck=True,
            discovered_packet="PCENG-A7.114-example",
            discovered_age_seconds=21.0,
        ))
        self.assertEqual(d.phase, "RECOVERING")
        self.assertIn("A7.114", d.reason)

    def test_discovery_progress_cancels_stall(self):
        events = [
            {"time": "2026-10-05T22:45:00+00:00", "event": "relay_packet_discovered",
             "detail": {"packet_id": "PCENG-A6.396-test", "browser_id": "edge"}},
            {"time": "2026-10-05T22:45:02+00:00", "event": "relay_action_execution_requested",
             "detail": {"packet_id": "PCENG-A6.396-test", "browser_id": "edge"}},
        ]
        stuck, packet, age = rs._discovery_stuck(events, 1791240330.0, "edge")
        self.assertFalse(stuck)
        self.assertEqual(packet, "PCENG-A6.396-test")
        self.assertIsNotNone(age)

    def test_repair_browser_reacquires_exact_managed_firefox_conversation(self):
        url="https://chatgpt.com/c/abc-123"
        with mock.patch.object(rs.browser_manager,"detect_browsers",return_value=[{"id":"firefox","family":"firefox","supported":True}]), mock.patch.object(rs.browser_manager,"get_managed_conversation_url",return_value=url), mock.patch.object(rs.browser_manager,"open_extension_setup",return_value={"connected":True}) as setup, mock.patch.object(rs.browser_manager,"reacquire_managed_conversation",return_value={"matched":True,"url":url}) as reacquire:
            ok,detail=rs._repair_browser("firefox")
        self.assertTrue(ok)
        setup.assert_called_once_with("firefox",url=url)
        reacquire.assert_called_once_with("firefox",url)
        self.assertIn("conversation",detail.lower())

    def test_repair_browser_fails_closed_without_managed_firefox_conversation(self):
        with mock.patch.object(rs.browser_manager,"detect_browsers",return_value=[{"id":"firefox","family":"firefox","supported":True}]), mock.patch.object(rs.browser_manager,"get_managed_conversation_url",return_value=None), mock.patch.object(rs.browser_manager,"open_extension_setup") as setup:
            ok,detail=rs._repair_browser("firefox")
        self.assertFalse(ok)
        setup.assert_not_called()
        self.assertIn("no managed",detail.lower())

    def test_repair_browser_fails_if_exact_reacquisition_fails(self):
        url="https://chatgpt.com/c/abc-123"
        with mock.patch.object(rs.browser_manager,"detect_browsers",return_value=[{"id":"firefox","family":"firefox","supported":True}]), mock.patch.object(rs.browser_manager,"get_managed_conversation_url",return_value=url), mock.patch.object(rs.browser_manager,"open_extension_setup",return_value={"connected":True}), mock.patch.object(rs.browser_manager,"reacquire_managed_conversation",side_effect=rs.browser_manager.BrowserError("wrong route")):
            ok,detail=rs._repair_browser("firefox")
        self.assertFalse(ok)
        self.assertIn("wrong route",detail)

    def test_repair_browser_uses_existing_cdp_setup_for_chromium(self):
        with mock.patch.object(rs.browser_manager, "detect_browsers", return_value=[
            {"id": "edge", "family": "chromium", "supported": True}
        ]), mock.patch.object(
            rs.browser_manager, "open_extension_setup", return_value={"connected": True}
        ) as setup:
            ok, detail = rs._repair_browser("edge")
        self.assertTrue(ok)
        setup.assert_called_once_with("edge")
        self.assertIn("rebuilt", detail)

    def test_windows_mutex_declares_explicit_ctypes_signatures(self):
        src = (CONSUMER / "recovery_supervisor.py").read_text(encoding="utf-8")
        self.assertIn("CreateMutexW.argtypes", src)
        self.assertIn("ctypes.c_wchar_p", src)
        self.assertIn("ReleaseMutex.argtypes", src)
        self.assertIn("CloseHandle.argtypes", src)

    def test_sample_uses_expected_managed_browser_and_exact_operation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            old_state, old_events = rs.RELAY_STATE_PATH, rs.EVENT_PATH
            try:
                rs.RELAY_STATE_PATH = root / "state.json"
                rs.EVENT_PATH = root / "events.jsonl"
                rs.RELAY_STATE_PATH.write_text(json.dumps({
                    "active_action": {"id": "PCENG-A7.1-test"},
                    "last_action": {"id": "PCENG-A6.999-old"},
                }), encoding="utf-8")
                rs.EVENT_PATH.write_text("", encoding="utf-8")
                with mock.patch.object(rs.browser_manager, "load_settings", return_value={
                    "browser_id": "edge", "browser_pids": {"edge": 1234}
                }), mock.patch.object(rs, "_relay_get", side_effect=[
                    {"ok": True, "armed": True, "pending_missions": 1},
                    {"ok": True, "connected": True},
                ]):
                    s = rs.sample(now_epoch=1791240330.0)
                self.assertTrue(s.browser_expected)
                self.assertTrue(s.browser_connected)
                self.assertEqual(s.active_operation, "PCENG-A7.1-test")
            finally:
                rs.RELAY_STATE_PATH, rs.EVENT_PATH = old_state, old_events


    def test_out_of_band_prompt_is_classified_and_bounded(self):
        s = self.snapshot(
            browser_id="firefox",
            browser_connected=False,
            last_operation="PCENG-A6.399af-example",
            last_event="relay_result_delivery_complete",
        )
        d = rs.decide(s)
        prompt = rs._build_gpt_recovery_prompt(s, d, "RECOVERY-TEST-1")
        self.assertIn("classification=BROWSER_INTEGRATION_DISCONNECTED", prompt)
        self.assertIn("incident_id=RECOVERY-TEST-1", prompt)
        self.assertIn("Do NOT send a GPT_WINDOWS_ACTION", prompt)
        self.assertIn("recommended_repairs", prompt)
        self.assertIn("rebuild_browser_integration", prompt)

    def test_recovery_advice_requires_matching_incident_and_whitelist(self):
        good = (
            "[GPT_RELAY_RECOVERY_ADVICE]\n"
            '{"version":1,"incident_id":"RECOVERY-TEST-2","classification":"BROWSER_INTEGRATION_DISCONNECTED",'
            '"recommended_repairs":["audited_update"],"reason":"source drift"}\n'
            "[/GPT_RELAY_RECOVERY_ADVICE]"
        )
        advice = rs._extract_gpt_recovery_advice(good, "RECOVERY-TEST-2")
        self.assertIsNotNone(advice)
        self.assertEqual(advice["recommended_repairs"], ["audited_update"])
        self.assertIsNone(rs._extract_gpt_recovery_advice(good, "RECOVERY-WRONG"))
        bad = good.replace('"audited_update"', '"powershell"')
        self.assertIsNone(rs._extract_gpt_recovery_advice(bad, "RECOVERY-TEST-2"))

    def test_out_of_band_consult_uses_browser_manager_not_relay_transport(self):
        s = self.snapshot(
            browser_id="firefox",
            browser_connected=False,
            last_operation="PCENG-A6.399af-example",
        )
        d = rs.decide(s)
        advice_text = (
            "[GPT_RELAY_RECOVERY_ADVICE]\n"
            '{"version":1,"incident_id":"PLACEHOLDER","classification":"BROWSER_INTEGRATION_DISCONNECTED",'
            '"recommended_repairs":["rebuild_browser_integration"],"reason":"integration absent"}\n'
            "[/GPT_RELAY_RECOVERY_ADVICE]"
        )
        captured = {}
        def send(browser_id, prompt):
            captured["prompt"] = prompt
            captured["incident"] = next(line.split("=", 1)[1] for line in prompt.splitlines() if line.startswith("incident_id="))
            return {"ok": True}
        def read(browser_id):
            return advice_text.replace("PLACEHOLDER", captured["incident"])
        with mock.patch.object(rs.browser_manager, "send_out_of_band_recovery_prompt", side_effect=send) as sender, \
             mock.patch.object(rs.browser_manager, "read_out_of_band_chat", side_effect=read) as reader, \
             mock.patch.object(rs, "_set_recovery_state") as recovery_state, \
             mock.patch.object(rs.time, "sleep"):
            ok, advice, detail = rs._consult_gpt_out_of_band(s, d)
        self.assertTrue(ok)
        self.assertEqual(advice["recommended_repairs"], ["rebuild_browser_integration"])
        sender.assert_called_once()
        reader.assert_called()
        phases=[call.args[1] for call in recovery_state.call_args_list]
        self.assertEqual(phases[:2], ["OOB_PROMPT_SENDING","OOB_WAITING_ADVICE"])
        self.assertEqual(phases[-1], "OOB_ADVICE_RECEIVED")
        self.assertTrue(any(call.kwargs.get("deadline_epoch") for call in recovery_state.call_args_list))
        self.assertIn("bounded GPT recovery advice", detail)

    def test_invalid_recovery_advice_gets_one_bounded_coaching_retry(self):
        s = self.snapshot(browser_id="firefox", browser_connected=False, last_operation="PCENG-A7.9-example")
        d = rs.decide(s)
        invalid = (
            '[GPT_RELAY_RECOVERY_ADVICE] {"version":1,"incident_id":"PLACEHOLDER",'
            '"recommended_repairs":["powershell"],"reason":"bad"} [/GPT_RELAY_RECOVERY_ADVICE]'
        )
        valid = (
            '[GPT_RELAY_RECOVERY_ADVICE] {"version":1,"incident_id":"PLACEHOLDER",'
            '"classification":"BROWSER_INTEGRATION_DISCONNECTED",'
            '"recommended_repairs":["rebuild_browser_integration"],"reason":"fixed"} '
            '[/GPT_RELAY_RECOVERY_ADVICE]'
        )
        captured = {"incident": None, "reads": 0}
        def send(_browser_id, prompt):
            if captured["incident"] is None:
                captured["incident"] = next(line.split("=",1)[1] for line in prompt.splitlines() if line.startswith("incident_id="))
            return {"ok": True}
        def read(_browser_id):
            captured["reads"] += 1
            raw = invalid if captured["reads"] == 1 else valid
            return raw.replace("PLACEHOLDER", captured["incident"])
        with mock.patch.object(rs.browser_manager, "send_out_of_band_recovery_prompt", side_effect=send) as sender, \
             mock.patch.object(rs.browser_manager, "read_out_of_band_chat", side_effect=read), \
             mock.patch.object(rs, "_set_recovery_state") as recovery_state, \
             mock.patch.object(rs.time, "sleep"):
            ok, advice, _detail = rs._consult_gpt_out_of_band(s, d)
        self.assertTrue(ok)
        self.assertEqual(advice["recommended_repairs"], ["rebuild_browser_integration"])
        self.assertEqual(sender.call_count, 2)
        phases=[call.args[1] for call in recovery_state.call_args_list]
        self.assertIn("OOB_ADVICE_RETRYING", phases)
        self.assertEqual(phases[-1], "OOB_ADVICE_RECEIVED")

    def test_recovery_obligation_is_persisted_with_deadline_and_operation(self):
        s = self.snapshot(browser_id="firefox", last_operation="PCENG-A7.12-example")
        with tempfile.TemporaryDirectory() as raw:
            old_path = rs.SUPERVISOR_STATE_PATH
            try:
                rs.SUPERVISOR_STATE_PATH = Path(raw) / "recovery-supervisor.json"
                rs._set_recovery_state(
                    "RECOVERY-TEST-DURABLE", "OOB_WAITING_ADVICE", snapshot=s,
                    classification="BROWSER_INTEGRATION_DISCONNECTED",
                    deadline_epoch=12345.0, detail="waiting",
                )
                state=json.loads(rs.SUPERVISOR_STATE_PATH.read_text(encoding="utf-8"))
            finally:
                rs.SUPERVISOR_STATE_PATH = old_path
        recovery=state["recovery"]
        self.assertEqual(recovery["incident_id"], "RECOVERY-TEST-DURABLE")
        self.assertEqual(recovery["phase"], "OOB_WAITING_ADVICE")
        self.assertEqual(recovery["operation_id"], "PCENG-A7.12-example")
        self.assertEqual(recovery["deadline_epoch"], 12345.0)


    def test_recovery_prompt_cannot_self_satisfy_advice_parser(self):
        s = self.snapshot(
            browser_id="firefox",
            browser_connected=False,
            last_operation="PCENG-A6.399au-example",
        )
        d = rs.decide(s)
        incident = "RECOVERY-NON-SELF-PARSE"
        prompt = rs._build_gpt_recovery_prompt(s, d, incident)
        self.assertIn("GPT_RELAY_RECOVERY_ADVICE", prompt)
        self.assertNotIn("[GPT_RELAY_RECOVERY_ADVICE]", prompt)
        self.assertNotIn("[/GPT_RELAY_RECOVERY_ADVICE]", prompt)
        self.assertIsNone(rs._extract_gpt_recovery_advice(prompt, incident))

    def test_streaming_partial_advice_does_not_trigger_correction(self):
        incident = "RECOVERY-STREAMING"
        partial = (
            "[GPT_RELAY_RECOVERY_ADVICE] "
            '{"version":1,"incident_id":"RECOVERY-STREAMING"'
        )
        complete = partial + '} [/GPT_RELAY_RECOVERY_ADVICE]'
        self.assertFalse(rs._recovery_advice_mentions_incident(partial, incident))
        self.assertTrue(rs._recovery_advice_mentions_incident(complete, incident))

    def test_independent_read_errors_are_observable_then_recover(self):
        s = self.snapshot(
            browser_id="firefox",
            browser_connected=False,
            last_operation="PCENG-A6.399au-example",
        )
        d = rs.decide(s)
        captured = {"incident": None, "reads": 0}
        def send(_browser_id, prompt):
            captured["incident"] = next(
                line.split("=", 1)[1] for line in prompt.splitlines()
                if line.startswith("incident_id=")
            )
            return {"ok": True}
        def read(_browser_id):
            captured["reads"] += 1
            if captured["reads"] == 1:
                raise RuntimeError("simulated UIA contention")
            return (
                "[GPT_RELAY_RECOVERY_ADVICE] "
                + json.dumps({
                    "version": 1,
                    "incident_id": captured["incident"],
                    "classification": "BROWSER_INTEGRATION_DISCONNECTED",
                    "recommended_repairs": ["rebuild_browser_integration"],
                    "reason": "read channel recovered",
                })
                + " [/GPT_RELAY_RECOVERY_ADVICE]"
            )
        with mock.patch.object(rs.browser_manager, "send_out_of_band_recovery_prompt", side_effect=send), \
             mock.patch.object(rs.browser_manager, "read_out_of_band_chat", side_effect=read), \
             mock.patch.object(rs, "_set_recovery_state") as recovery_state, \
             mock.patch.object(rs.time, "sleep"):
            ok, advice, _detail = rs._consult_gpt_out_of_band(s, d)
        self.assertTrue(ok)
        self.assertEqual(advice["recommended_repairs"], ["rebuild_browser_integration"])
        phases = [call.args[1] for call in recovery_state.call_args_list]
        self.assertIn("OOB_READ_RETRYING", phases)
        self.assertEqual(phases[-1], "OOB_ADVICE_RECEIVED")


    def test_visible_chatgpt_error_enters_screenshot_recovery(self):
        s = self.snapshot(
            browser_id="firefox",
            browser_connected=True,
            chatgpt_ui_error=True,
            chatgpt_ui_error_detail="Error in input stream Retry",
        )
        d = rs.decide(s)
        self.assertEqual(d.phase, "RECOVERING")
        self.assertEqual(d.repair, "capture_diagnostic")
        self.assertIn("Error in input stream", d.reason)
        with mock.patch.object(rs, "_capture_screenshot", return_value="shot.png") as capture, \
             mock.patch.object(rs, "_evidence") as evidence:
            ok, detail = rs.run_repair(s, d, 1)
        self.assertFalse(ok)
        self.assertIn("captured", detail)
        capture.assert_called_once()
        self.assertTrue(any(call.kwargs.get("screenshot") == "shot.png" for call in evidence.call_args_list))

    def test_visible_chatgpt_error_classification_is_explicit(self):
        s = self.snapshot(
            browser_id="firefox",
            chatgpt_ui_error=True,
            chatgpt_ui_error_detail="Error in input stream",
        )
        d = rs.decide(s)
        self.assertEqual(rs._recovery_classification(s, d), "CHATGPT_UI_ERROR")


if __name__ == "__main__":
    unittest.main()
