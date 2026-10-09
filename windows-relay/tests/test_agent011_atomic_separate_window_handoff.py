"""Agent011 separate-window handoff negative gates (NO browser interaction).
Windows PowerShell runs are intentionally limited to missing/bad handoff files:
they MUST return before UIAutomation assembly loading, focus, edit or send.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

WORKER = Path(__file__).resolve().parents[1] / "agent011_separate_window_handoff.ps1"
HELPER = Path(__file__).resolve().parents[1] / "agent011_editor_empty_state.ps1"


class AtomicSeparateWindowHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = WORKER.read_bytes()
        cls.source = cls.raw.decode("ascii")

    def test_ascii_and_two_separate_window_only_no_same_tab_navigator(self):
        s = self.source
        self.assertTrue(self.raw.isascii())
        self.assertIn("function Inspect-Windows", s)
        self.assertIn("SOURCE_DESTINATION_WINDOW_PAIR_NOT_UNIQUE", s)
        self.assertIn("DESTINATION_HAS_MULTIPLE_TABS", s)
        self.assertIn("SOURCE_TAB_TITLE_UNTRUSTED", s)
        self.assertIn("SOURCE_AND_DESTINATION_HWND_IDENTICAL", s)
        self.assertIn("SOURCE_EDITOR", s)
        self.assertIn("agent011_editor_empty_state.ps1", s)
        self.assertNotIn("function NewChatButton(", s)
        self.assertNotIn("SendWait('^t')", s)
        self.assertNotIn("SendWait('^l')", s)
        self.assertNotIn("Start-Process", s)
        self.assertNotIn("location.assign(", s)
        self.assertNotIn("NewChatButton.Invoke", s)

    def test_idempotency_receipt_and_stop_epoch_are_mandatory(self):
        s = self.source
        for token in (
            "[IO.FileMode]::CreateNew",
            "function Assert-Handoff",
            "HANDOFF_SHA256_MISMATCH",
            "HANDOFF_REQUIRED_MARKER_MISSING_",
            "HANDOFF_FILE_MISSING",
            "SOURCE_HEAD_NOT_PINNED",
            "PENDING_MISSIONS_CHANGED",
            "STOP_EPOCH_CHANGED",
            "OPERATOR_STOP_FILE",
            "RELAY_NOT_ARMED_OR_NOT_BROWSER_OWNER",
            "Assert-SourceCheckout",
            "ValidateOnly",
            "HANDOFF_SEND_UNCERTAIN_NO_RETRY",
            "HALT_SUBMISSION_UNCERTAIN_NO_RETRY",
            "HALT_AFTER_COMPOSE_NO_RETRY",
            "HALT_AFTER_FOCUS_NO_RETRY",
            "DISTINCT_NEW_CONVERSATION_VERIFIED_MESSAGE_PENDING",
            "SOURCE_COMPOSER_HAS_DRAFT",
        ):
            with self.subTest(token=token):
                self.assertIn(token, s)

    def test_all_side_effects_follow_durable_intent_and_gates(self):
        s = self.source
        assert_before = [
            ("Save-Receipt 'FOCUS_ATTEMPT_UNCERTAIN_NO_RETRY'", "[Agent011AtomicFocus]::SetForegroundWindow($home.handle)"),
            ("Save-Receipt 'COMPOSE_ATTEMPT_UNCERTAIN_NO_RETRY'", "$editor.pattern.SetValue($script:Handoff)"),
            ("Save-Receipt 'HANDOFF_SEND_UNCERTAIN_NO_RETRY'", "$send[0].invoke.Invoke()"),
            ("Assert-Handoff\n Save-Receipt", "Add-Type -AssemblyName UIAutomationClient"),
            ("Assert-SourceCheckout\n $null=Assert-Controls", "Add-Type -AssemblyName UIAutomationClient"),
            ("Save-Receipt 'DESTINATION_FOREGROUND_AND_STOP_VERIFIED'", "Save-Receipt 'COMPOSE_ATTEMPT_UNCERTAIN_NO_RETRY'"),
            ("Save-Receipt 'SEND_GATES_VERIFIED'", "Save-Receipt 'HANDOFF_SEND_UNCERTAIN_NO_RETRY'"),
        ]
        for first, second in assert_before:
            with self.subTest(earlier=first):
                self.assertIn(first, s)
                self.assertIn(second, s)
                self.assertLess(s.index(first), s.index(second))
        self.assertEqual(s.count("SetForegroundWindow($home.handle)"), 1)
        self.assertEqual(s.count("$send[0].invoke.Invoke()"), 1)
        self.assertEqual(s.count("$editor.pattern.SetValue($script:Handoff)"), 1)

    def test_worker_syntax_parse_without_executing_script(self):
        powershell = shutil.which("powershell.exe")
        if not powershell:
            self.skipTest("Windows PowerShell not installed")
        escaped = str(WORKER).replace("'", "''")
        ps = (
            "$tokens=$null;$errors=$null;"
            "[System.Management.Automation.Language.Parser]::ParseFile('"
            + escaped
            + "',[ref]$tokens,[ref]$errors)|Out-Null;"
            "if($errors.Count){$errors|ForEach-Object{$_.Message};exit 2};"
            "Write-Output 'AGENT011_ATOMIC_WORKER_PARSE_OK'"
        )
        p = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand",
             base64.b64encode(ps.encode("utf-16le")).decode("ascii")],
            capture_output=True, text=True, timeout=20, encoding="utf-8", errors="replace",
        )
        self.assertEqual(p.returncode, 0, p.stdout + "\n" + p.stderr)
        self.assertIn("AGENT011_ATOMIC_WORKER_PARSE_OK", p.stdout)

    def _negative_worker(self, handoff: Path, receipt: Path):
        powershell = shutil.which("powershell.exe")
        if not powershell:
            self.skipTest("Windows PowerShell not installed")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return subprocess.run(
            [powershell, "-STA", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(WORKER),
             "-SourcePacketId", "AGENT011-NEGATIVE-TEST-ONLY",
             "-HandoffFile", str(handoff),
             "-ExpectedHandoffSha256", "0" * 64,
             "-ExpectedSourceHead", "0" * 40,
             "-ReceiptFile", str(receipt)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=25, creationflags=flags,
        )

    @unittest.skipUnless(os.name == "nt", "Negative process acceptance requires Windows")
    def test_missing_handoff_stops_before_browser_and_creates_receipt(self):
        with tempfile.TemporaryDirectory(prefix="agent011-atomic-missing-") as d:
            missing = Path(d) / "never-created-handoff.md"
            receipt = Path(d) / "missing-receipt.json"
            proc = self._negative_worker(missing, receipt)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            data = json.loads(receipt.read_text(encoding="utf-8-sig"))
            self.assertEqual(data["phase"], "HALT_BEFORE_UI_MUTATION")
            self.assertIn("HANDOFF_FILE_MISSING", data["error"])
            for field in ("focus_attempted", "compose_attempted", "send_invoked",
                          "firefox_launched", "new_chat_clicked"):
                self.assertFalse(data[field], field)

    @unittest.skipUnless(os.name == "nt", "Negative process acceptance requires Windows")
    def test_wrong_digest_fails_before_ui_or_status(self):
        with tempfile.TemporaryDirectory(prefix="agent011-atomic-digest-") as d:
            handoff = Path(d) / "dummy.md"
            handoff.write_text("INVALID PLACEHOLDER NOT A HANDOFF", encoding="utf-8")
            receipt = Path(d) / "digest-receipt.json"
            proc = self._negative_worker(handoff, receipt)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            data = json.loads(receipt.read_text(encoding="utf-8-sig"))
            self.assertEqual(data["phase"], "HALT_BEFORE_UI_MUTATION")
            self.assertIn("HANDOFF_SHA256_MISMATCH", data["error"])
            self.assertFalse(data["focus_attempted"])
            self.assertFalse(data["send_invoked"])

    @unittest.skipUnless(os.name == "nt", "Negative process acceptance requires Windows")
    def test_existing_receipt_blocks_replay_without_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="agent011-atomic-replay-") as d:
            missing = Path(d) / "missing.md"
            receipt = Path(d) / "one-shot.json"
            first = self._negative_worker(missing, receipt)
            self.assertEqual(first.returncode, 2)
            first_contents = receipt.read_bytes()
            second = self._negative_worker(missing, receipt)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(receipt.read_bytes(), first_contents)
            self.assertIn("EXCLUSIVE_RECEIPT_NOT_CREATED", second.stdout + second.stderr)


if __name__ == "__main__":
    unittest.main()
