import os
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("windows_tools",HERE/"windows_tools.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class WindowsToolsContractTests(unittest.TestCase):
    def test_clipboard_marker_and_public_api(self):
        self.assertTrue(mod.GPT_WINDOWS_CLIPBOARD_V1)
        self.assertTrue(callable(mod.clipboard_read_text))
        self.assertTrue(callable(mod.clipboard_write_text))
        self.assertTrue(callable(mod.clipboard_clear))

    def test_write_rejects_non_string_before_clipboard_mutation(self):
        with self.assertRaises(TypeError):
            mod.clipboard_write_text(123)

    def test_cli_exposes_clipboard_commands(self):
        src=(HERE/"windows_tools.py").read_text(encoding="utf-8")
        self.assertIn('"clipboard-read"',src)
        self.assertIn('"clipboard-write"',src)
        self.assertIn('"clipboard-clear"',src)
        self.assertIn('CF_UNICODETEXT = 13',src)

    def test_field_entry_marker_and_fail_closed_selector(self):
        self.assertTrue(mod.GPT_WINDOWS_UIA_FIELD_ENTRY_V1)
        self.assertTrue(callable(mod.field_set_text))
        with self.assertRaises(ValueError):
            mod.field_set_text("Harness", "value")

    def test_field_entry_uses_semantic_uia_value_pattern(self):
        src=(HERE/"uia_text_entry.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("ControlType]::Edit",src)
        self.assertIn("FIELD_MATCH_COUNT_",src)
        self.assertIn("WINDOW_MATCH_COUNT_",src)
        self.assertIn("ValuePattern]::Pattern",src)
        self.assertIn('$pattern=$null',src)
        self.assertIn("SetValue($text)",src)
        self.assertIn("FIELD_READBACK_MISMATCH",src)
        self.assertNotIn("SendKeys",src)


    def test_control_adapter_marker_and_fail_closed_mutation_selector(self):
        self.assertTrue(mod.GPT_WINDOWS_UIA_CONTROL_ADAPTER_V1)
        self.assertTrue(callable(mod.control_inspect))
        self.assertTrue(callable(mod.control_invoke))
        self.assertTrue(callable(mod.control_select))
        self.assertTrue(callable(mod.control_set_toggle))
        with self.assertRaises(ValueError):
            mod.control_invoke("Harness", control_type="Button")
        with self.assertRaises(ValueError):
            mod.control_invoke("Harness", control_type="MadeUp", control_name="X")
        with self.assertRaises(TypeError):
            mod.control_set_toggle("Harness", 1, control_name="X")

    def test_control_adapter_is_semantic_pattern_based_and_no_sendkeys(self):
        src=(HERE/"uia_control_action.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("WINDOW_MATCH_COUNT_", src)
        self.assertIn("CONTROL_MATCH_COUNT_", src)
        self.assertIn("InvokePattern]::Pattern", src)
        self.assertIn("SelectionItemPattern]::Pattern", src)
        self.assertIn("TogglePattern]::Pattern", src)
        self.assertIn("SELECTION_READBACK_MISMATCH", src)
        self.assertIn("TOGGLE_READBACK_MISMATCH", src)
        self.assertNotIn("SendKeys", src)

    def test_copy_all_capture_contract_and_exact_dedupe(self):
        self.assertTrue(mod.GPT_WINDOWS_COPY_ALL_CAPTURE_V1)
        self.assertTrue(callable(mod.copy_all_capture))
        self.assertTrue(callable(mod.store_text_capture))
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); a=mod.store_text_capture("same bytes",source="test",root=root); b=mod.store_text_capture("same bytes",source="test",root=root)
            self.assertTrue(a["accepted"]); self.assertTrue(b["duplicate"]); self.assertEqual(a["sha256"],b["sha256"]); self.assertEqual(len(list(root.glob("*.txt"))),1)
        src=(HERE/"windows_tools.py").read_text(encoding="utf-8")
        self.assertIn("keybd_event",src); self.assertIn("copy-all-capture",src); self.assertNotIn("SendKeys",src)


if __name__=="__main__": unittest.main()
