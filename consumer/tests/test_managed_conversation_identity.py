from pathlib import Path
import sys,tempfile,unittest
from unittest import mock

CONSUMER=Path(__file__).resolve().parents[1]
ROOT=CONSUMER.parent
sys.path.insert(0,str(ROOT/"windows-relay"))
import firefox_adapter as ff
sys.path.insert(0,str(CONSUMER))
import browser_manager as bm

class ManagedConversationIdentityTests(unittest.TestCase):
    def test_firefox_list_tabs_accepts_profile_scope(self):
        with mock.patch.object(ff,"_call",return_value={"ok":True}) as call:
            ff.list_tabs(profile_path="managed-profile")
        call.assert_called_once_with("list-tabs",firefox_pid=None,profile_path="managed-profile")

    def test_storage_is_per_browser_and_strict(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(bm,"SETTINGS_PATH",Path(td)/"settings.json"):
            url=bm.remember_managed_conversation_url("firefox","chatgpt.com/c/abc-123")
            self.assertEqual(url,"https://chatgpt.com/c/abc-123")
            self.assertEqual(bm.get_managed_conversation_url("firefox"),url)
            self.assertIsNone(bm.get_managed_conversation_url("edge"))
            with self.assertRaises(bm.BrowserError):
                bm.remember_managed_conversation_url("firefox","https://chatgpt.com/")

    def test_firefox_identity_uses_profile_scoped_tab_and_uia_urlbar(self):
        with mock.patch.object(bm,"detect_browsers",return_value=[{"id":"firefox","family":"firefox","supported":True}]), \
             mock.patch.object(bm,"profile_path",return_value=Path("managed-firefox")), \
             mock.patch.object(bm,"_run_firefox_adapter",return_value={"ok":True,"window_name":"PC Engineering - Mozilla Firefox","firefox_pid":77}) as ff, \
             mock.patch.object(bm,"_run_windows_tools",return_value={"ok":True,"match_count":1,"matches":[{"value":"chatgpt.com/c/abc-123"}]}) as uia:
            result=bm.read_managed_conversation_identity("firefox")
        self.assertEqual(result["url"],"https://chatgpt.com/c/abc-123")
        self.assertEqual(ff.call_args.args[0],"list-tabs")
        self.assertIn("--profile-path",ff.call_args.args)
        self.assertIn("urlbar-input",uia.call_args.args)

    def test_verification_fails_closed_on_mismatch(self):
        with mock.patch.object(bm,"read_managed_conversation_identity",return_value={"ok":True,"url":"https://chatgpt.com/c/wrong"}):
            with self.assertRaises(bm.BrowserError):
                bm.verify_managed_conversation("firefox","https://chatgpt.com/c/expected")

    def test_reacquire_uses_current_exact_conversation_without_launch(self):
        ident={"ok":True,"url":"https://chatgpt.com/c/abc","matched":True}
        with mock.patch.object(bm,"verify_managed_conversation",return_value=ident), mock.patch.object(bm.subprocess,"Popen") as popen:
            got=bm.reacquire_managed_conversation("firefox","https://chatgpt.com/c/abc",timeout=.1)
        self.assertFalse(got["reacquired"]);self.assertEqual(got["method"],"already_selected");popen.assert_not_called()

    def test_reacquire_opens_exact_stored_conversation_then_verifies(self):
        url="https://chatgpt.com/c/abc"; browser={"id":"firefox","family":"firefox","supported":True,"path":"firefox.exe"}; ident={"ok":True,"url":url,"matched":True}
        with mock.patch.object(bm,"get_managed_conversation_url",return_value=url), mock.patch.object(bm,"verify_managed_conversation",side_effect=[bm.BrowserError("wrong"),ident]), mock.patch.object(bm,"detect_browsers",return_value=[browser]), mock.patch.object(bm,"profile_path",return_value=Path("managed")), mock.patch.object(bm.subprocess,"Popen") as popen:
            got=bm.reacquire_managed_conversation("firefox",timeout=1)
        self.assertTrue(got["reacquired"]);self.assertEqual(got["method"],"open_exact_conversation");self.assertEqual(popen.call_args.args[0][-1],url)

    def test_reacquire_fails_closed_without_stored_identity(self):
        with mock.patch.object(bm,"get_managed_conversation_url",return_value=None):
            with self.assertRaises(bm.BrowserError): bm.reacquire_managed_conversation("firefox")

    def test_open_extension_setup_accepts_exact_conversation_url(self):
        url="https://chatgpt.com/c/abc-123"
        browser={"id":"firefox","family":"firefox","supported":True,"name":"Firefox","path":"firefox.exe"}
        with tempfile.TemporaryDirectory() as td, mock.patch.object(bm,"select_browser",return_value=browser), mock.patch.object(bm,"profile_path",return_value=Path(td)/"profile"), mock.patch.object(bm,"prepared_extension_path",return_value=Path(td)/"ext"), mock.patch.object(bm,"_automatic_firefox_setup",return_value={"pid":77,"setup_method":"firefox_uia_temporary"}) as setup, mock.patch.object(bm,"wait_for_browser_connection",return_value=True):
            result=bm.open_extension_setup("firefox",url=url)
        self.assertTrue(result["connected"])
        self.assertEqual(setup.call_args.args[3],url)

if __name__=="__main__":
    unittest.main()
