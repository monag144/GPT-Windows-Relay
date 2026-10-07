from pathlib import Path
import unittest
from unittest.mock import patch
import windows_workflow as wf

class WindowsWorkflowTests(unittest.TestCase):
    def test_marker_and_rejects_arbitrary_execution(self):
        self.assertTrue(wf.GPT_WINDOWS_WORKFLOW_V1)
        with self.assertRaises(ValueError): wf.validate_plan({"version":1,"steps":[{"id":"x","op":"shell.exec","args":{}}]})

    def test_rejects_duplicate_ids_and_ambiguous_mutation_selector(self):
        with self.assertRaises(ValueError): wf.validate_plan({"version":1,"steps":[{"id":"x","op":"clipboard.read"},{"id":"x","op":"clipboard.read"}]})
        with self.assertRaises(ValueError): wf.validate_plan({"version":1,"steps":[{"id":"x","op":"uia.invoke","args":{"window_title":"W","control_type":"Button"}}]})

    def test_success_sequence_uses_fixed_adapters(self):
        plan={"version":1,"name":"proof","steps":[{"id":"w","op":"clipboard.write","args":{"text":"abc"}},{"id":"t","op":"firefox.list_tabs"},{"id":"i","op":"uia.inspect","args":{"window_title":"W","control_type":"Button"}}]}
        with patch.object(wf.wt,"clipboard_write_text") as cw, patch.object(wf.ff,"list_tabs",return_value={"ok":True,"tabs":[]}) as lt, patch.object(wf.wt,"control_inspect",return_value={"ok":True,"match_count":1}) as ci:
            out=wf.execute_workflow(plan)
        self.assertTrue(out["ok"]);self.assertEqual(out["status"],"completed");self.assertEqual([x["id"] for x in out["steps"]],["w","t","i"]);cw.assert_called_once_with("abc");lt.assert_called_once();ci.assert_called_once()

    def test_failure_stops_and_promotes_fallback_attachment(self):
        plan={"version":1,"steps":[{"id":"bad","op":"uia.invoke","args":{"window_title":"W","control_type":"Button","control_name":"Duplicate"},"fallback_screenshot":{"target":"window","window_title":"W"}},{"id":"never","op":"clipboard.clear"}]}
        cap={"ok":True,"managed":True,"chatgpt_attachment":{"kind":"image","name":"screenshot-20260101T000000-000000001.png","mime":"image/png"}}
        with patch.object(wf.wt,"control_invoke",side_effect=RuntimeError("CONTROL_MATCH_COUNT_2")), patch.object(wf.wt,"screenshot_capture",return_value=cap) as sc, patch.object(wf.wt,"clipboard_clear") as cc:
            out=wf.execute_workflow(plan)
        self.assertFalse(out["ok"]);self.assertEqual(out["status"],"needs_visual_reasoning");self.assertEqual(out["failed_step"],"bad");self.assertEqual(out["chatgpt_attachment"]["kind"],"image");sc.assert_called_once();cc.assert_not_called()

    def test_automatic_fallback_disallows_full_screen(self):
        with self.assertRaises(ValueError): wf.validate_plan({"version":1,"steps":[{"id":"x","op":"clipboard.read","fallback_screenshot":{"target":"screen"}}]})

if __name__=="__main__": unittest.main()
