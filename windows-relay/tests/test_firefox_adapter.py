import base64
import importlib.util
from pathlib import Path
import os
import subprocess
import unittest
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("firefox_adapter",HERE/"firefox_adapter.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class FirefoxAdapterContractTests(unittest.TestCase):
    def test_marker_and_public_api(self):
        self.assertTrue(mod.GPT_WINDOWS_FIREFOX_TAB_ADAPTER_V1)
        self.assertTrue(callable(mod.list_tabs));self.assertTrue(callable(mod.select_tab))
        self.assertTrue(mod.GPT_WINDOWS_FIREFOX_RECOVERY_ADAPTER_V2)
        self.assertTrue(callable(mod.reload_addon));self.assertTrue(callable(mod.refresh_tab));self.assertTrue(callable(mod.ensure_addon));self.assertTrue(callable(mod.close_profile));self.assertTrue(callable(mod.send_chatgpt_prompt));self.assertTrue(callable(mod.read_chatgpt_text))
    def test_cli_json_is_ascii_safe_for_unicode_tab_titles(self):
        src=(HERE/"firefox_adapter.py").read_text(encoding="utf-8")
        self.assertIn("json.dumps(result,ensure_ascii=True)",src)

    def test_recovery_prompt_base64_transport_preserves_exact_text(self):
        prompt='Recovery request with spaces, JSON {"reason":"semantic recovery prompt received."}, and [GPT_RELAY_RECOVERY_ADVICE]'
        encoded=base64.b64encode(prompt.encode("utf-8")).decode("ascii")
        self.assertEqual(mod.decode_prompt_input(None,encoded),prompt)
        self.assertEqual(mod.decode_prompt_input(prompt,None),prompt)
        with self.assertRaises(ValueError): mod.decode_prompt_input(prompt,encoded)
        with self.assertRaises(ValueError): mod.decode_prompt_input(None,"not base64!")
        src=(HERE/"firefox_adapter.py").read_text(encoding="utf-8")
        self.assertIn("GPT_WINDOWS_FIREFOX_PROMPT_B64_TRANSPORT_V1",src)
        self.assertIn('"--prompt-b64"',src)

    def test_select_requires_exactly_one_selector(self):
        with self.assertRaises(ValueError): mod.select_tab()
        with self.assertRaises(ValueError): mod.select_tab(tab_name="A",contains="A")
    def test_recovery_actions_are_semantic_and_fail_closed(self):
        src=(HERE/"firefox_tab_adapter.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("'reload-addon'",src)
        self.assertIn("'refresh-tab'",src)
        self.assertIn("'ensure-addon'",src)
        self.assertIn("FIREFOX_LOAD_TEMP_ADDON_BUTTON_COUNT_",src)
        self.assertIn("-not $b.Current.IsOffscreen -and ([string]$b.Current.Name) -like 'Load Temporary Add-on*'",src)
        self.assertIn("FIREFOX_ADDON_FILE_DIALOG_NOT_FOUND",src)
        self.assertIn("ValuePattern]::Pattern",src)
        self.assertIn("MANIFEST_PATH_NOT_FOUND",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_MANAGED_PROCESS_TREE_V1",src)
        self.assertIn("Get-CimInstance Win32_Process",src)
        self.assertIn("ParentProcessId",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_MANAGED_PROFILE_IDENTITY_V1",src)
        self.assertIn("FIREFOX_PROFILE_ROOT_COUNT_",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_PROFILE_CLOSE_IDEMPOTENT_V1",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_PROFILE_CLOSE_BARRIER_V1",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_OUT_OF_BAND_PROMPT_V1",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_OUT_OF_BAND_READBACK_V1",src)
        self.assertIn("'read-chatgpt-text'",src)
        self.assertIn("DocumentRange.GetText(-1)",src)
        self.assertIn("'send-chatgpt-prompt'",src)
        self.assertIn("'Ask ChatGPT'",src)
        self.assertIn("'ProseMirror'",src)
        self.assertIn("FIREFOX_CHATGPT_COMPOSER_READBACK_MISMATCH",src)
        self.assertIn("FIREFOX_CHATGPT_SEND_BUTTON_COUNT_",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_COMPOSER_CLIPBOARD_FALLBACK_V1",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_PROMPT_SUBMIT_CONFIRMATION_V1",src)
        self.assertIn("FIREFOX_CHATGPT_CLIPBOARD_PASTE_READBACK_MISMATCH",src)
        self.assertIn("FIREFOX_CHATGPT_SUBMIT_NOT_CONFIRMED",src)
        self.assertIn("[System.Windows.Forms.Clipboard]::SetText($PromptText)",src)
        self.assertIn("[System.Windows.Forms.Clipboard]::SetDataObject($oldClipboard,$true)",src)
        self.assertIn("FIREFOX_PROFILE_CLOSE_TIMEOUT",src)
        self.assertIn("remaining_count=0",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_FILE_DIALOG_TELEMETRY_V1",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_WINDOW_IDENTITY_TELEMETRY_V1",src)
        self.assertIn("visible_mozilla=",src)
        self.assertIn("GPT_WINDOWS_FIREFOX_DEBUG_WINDOW_SEMANTIC_SELECTION_V1",src)
        self.assertIn("FIREFOX_DEBUGGING_WINDOW_COUNT_",src)
        self.assertIn("FIREFOX_DEBUGGING_TAB_SELECTION_PATTERN_UNAVAILABLE",src)
        self.assertIn("$debugTarget=$tab",src)
        self.assertIn("'close-profile'",src)
        self.assertIn("FIREFOX_ADDON_CARD_COUNT_",src)
        self.assertIn("FIREFOX_ADDON_RELOAD_BUTTON_COUNT_",src)
        self.assertIn("AutomationId -eq 'reload-button'",src)
        self.assertIn("InvokePattern]::Pattern",src)

    def test_powershell_adapter_has_no_generated_tail_duplication(self):
        src=(HERE/"firefox_tab_adapter.ps1").read_text(encoding="utf-8-sig")
        self.assertEqual(src.count("if($Action -eq 'list-tabs'){"),1)
        self.assertEqual(src.count("GPT_WINDOWS_FIREFOX_OUT_OF_BAND_PROMPT_V1"),1)
        self.assertEqual(src.count("GPT_WINDOWS_FIREFOX_OUT_OF_BAND_READBACK_V1"),1)
        self.assertLess(len(src),22000)

    @unittest.skipUnless(os.name=="nt","PowerShell AST parse is a Windows acceptance gate")
    def test_powershell_adapter_parses_on_windows(self):
        script=HERE/"firefox_tab_adapter.ps1"
        command=(
            "$t=$null;$e=$null;"
            "[System.Management.Automation.Language.Parser]::ParseFile("
            + repr(str(script))
            + ",[ref]$t,[ref]$e)|Out-Null;"
            "if($e.Count){$e|ForEach-Object{Write-Error $_.Message};exit 1}"
        )
        cp=subprocess.run(["powershell.exe","-NoProfile","-Command",command],capture_output=True,text=True,timeout=15)
        self.assertEqual(cp.returncode,0,cp.stderr or cp.stdout)

    def test_script_scopes_real_browser_tabs_semantically(self):
        src=(HERE/"firefox_tab_adapter.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("MozillaWindowClass",src)
        self.assertIn("tabbrowser-tabs",src)
        self.assertIn("SelectionItemPattern]::Pattern",src)
        self.assertIn("FIREFOX_TAB_MATCH_COUNT_",src)
        self.assertIn("FIREFOX_TAB_SELECTION_READBACK_MISMATCH",src)
        self.assertIn("[System.Windows.Forms.SendKeys]::SendWait('^v')",src)
        self.assertIn("[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')",src)
        self.assertIn("$composers[0].SetFocus()",src)
if __name__=="__main__": unittest.main()
