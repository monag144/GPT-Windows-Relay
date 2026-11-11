"""PCE14 read-only observer privacy and fail-closed regressions."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import relay_uia_readonly as observer  # noqa: E402


class NativeObserverContracts(unittest.TestCase):
    def test_control_counts_from_native_accessibility_tree(self):
        result = observer.classify({
            "visited": 16, "max_depth": 4,
            "control_counts": {"TabItem": 2, "Document": 1, "Pane": 5},
        })
        self.assertEqual(result["control_counts"]["TabItem"], 2)
        self.assertFalse(result["can_send"])
        self.assertFalse(result["originating_tab_verified"])
        self.assertFalse(result["exact_user_message_verified"])

    def test_private_names_and_values_never_emitted(self):
        result = observer.classify({
            "visited": 2, "max_depth": 2,
            "control_counts": {"Tab": 1},
            "name": "A private conversation",
            "url": "https://some-private-page.example/",
            "value": "A private draft",
        })
        self.assertNotIn("private", str(result).lower())
        self.assertNotIn("url", result)
        self.assertNotIn("name", result)

    def test_rejects_negative_and_impossible_counts(self):
        samples = [
            {"visited": -1, "max_depth": 1, "control_counts": {}},
            {"visited": 2, "max_depth": 1, "control_counts": {"Tab": 3}},
            {"visited": 4, "max_depth": 1, "control_counts": {"Tab": 3, "Pane": 3}},
            {"visited": True, "max_depth": 1, "control_counts": {}},
        ]
        for item in samples:
            with self.subTest(item=item), self.assertRaises(ValueError):
                observer.classify(item)

    def test_unknown_control_type_rejected(self):
        with self.assertRaises(ValueError):
            observer.classify({"visited": 4, "max_depth": 2,
                               "control_counts": {"EmailText": 1}})

    def test_bad_window_handle_cannot_be_injected_into_shell(self):
        for handle in (-1, True, 0, "123;exit 0"):
            with self.subTest(handle=handle), self.assertRaises(ValueError):
                observer.uia_command(handle)

    def test_valid_script_has_no_input_mutation_interfaces(self):
        script = observer.uia_command(19466700)
        self.assertIn("19466700", script)
        self.assertIn("GetFirstChild", script)
        for snippet in ("SetForegroundWindow", "SendKeys", "mouse_event",
                        "Clipboard", "GetCurrentPattern", "InvokePattern",
                        "Get-Content", "WriteAllText"):
            with self.subTest(snippet=snippet):
                self.assertNotIn(snippet, script)

    def test_foreground_not_firefox_refuses_uia(self):
        with mock.patch.object(observer, "foreground_firefox",
                               return_value={"status": "FOREGROUND_NOT_FIREFOX"}):
            report = observer.inspect()
        self.assertEqual(report["status"], "FOREGROUND_NOT_FIREFOX")
        self.assertFalse(report["can_send"])


if __name__ == "__main__":
    unittest.main()
