"""Agent011 synthetic user-turn proof: no Firefox, no Send, no mutation."""
import base64
from pathlib import Path
import shutil
import subprocess
import re
import unittest

RELAY = Path(__file__).resolve().parents[1]
WORKER = RELAY / "agent011_separate_window_handoff.ps1"
PROOF = RELAY / "agent011_user_turn_proof.ps1"


class Agent011UserTurnProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = WORKER.read_text(encoding="ascii")
        cls.helper = PROOF.read_text(encoding="ascii")

    def test_only_scoped_user_message_group_can_pass(self):
        h = self.helper
        self.assertIn("GetParent($all[$i])", h)
        self.assertIn("[Windows.Automation.ControlType]::Group", h)
        self.assertIn("$parent.FindAll([Windows.Automation.TreeScope]::Descendants,$condition)", h)
        self.assertNotIn("$Window.FindAll([Windows.Automation.TreeScope]::Subtree", h)
        self.assertIn("$users -ne 1 -or $assistants -ne 0", h)
        self.assertIn("$proved -gt 1", h)
        self.assertIn("return ($proved -eq 1)", h)

    def test_distinct_url_only_never_proves_handoff(self):
        s = self.worker
        old = "Save-Receipt 'DISTINCT_NEW_CONVERSATION_VERIFIED_MESSAGE_PENDING'"
        probe = "if(Test-Agent011DeliveredUserTurn $destination.window)"
        marker = "$script:State.user_turn_verified=$true"
        success = "Save-Receipt 'DISTINCT_NEW_CONVERSATION_USER_TURN_MARKERS_VERIFIED_TITLE_PENDING'"
        self.assertIn("agent011_user_turn_proof.ps1", s)
        self.assertLess(s.index("$send[0].invoke.Invoke()"), s.index(old))
        self.assertLess(s.index(old), s.index(probe))
        self.assertLess(s.index(probe), s.index(marker))
        self.assertLess(s.index(marker), s.index(success))
        self.assertIn("DESTINATION_USER_TURN_MARKERS_NOT_VISIBLE_NO_RETRY", s)
        self.assertIn("HALT_SUBMISSION_UNCERTAIN_NO_RETRY", s)
        self.assertIn("title_verified=$false", s)
        self.assertEqual(s.count("$send[0].invoke.Invoke()"), 1)
        self.assertEqual(s.count("$editor.pattern.SetValue($script:Handoff)"), 1)
        self.assertEqual(s.count("SetForegroundWindow($destination.handle)"), 1)

    def test_worker_avoids_powershell_protected_home_variable(self):
        s = self.worker
        self.assertIsNone(re.search(r"\$home\b", s, re.IGNORECASE))
        self.assertEqual(s.count("$destination=@($windows|Where-Object"), 1)
        self.assertEqual(len(re.findall(r"\$destination\b", s)), 17)
        self.assertIn("Test-Agent011DeliveredUserTurn $destination.window", s)
        self.assertIn("SetForegroundWindow($destination.handle)", s)
        self.assertIn("Active-SendButtons $destination.window", s)

    @unittest.skipUnless(shutil.which("powershell.exe"), "Requires Windows PowerShell")
    def test_real_powershell_destination_assignment_not_protected_home(self):
        ps = (
            "$ErrorActionPreference='Stop';"
            "$before=[string]$HOME;"
            "$destination=[ordered]@{kind='home';handle=[IntPtr]::new(19)};"
            "if($destination.kind -cne 'home'){throw 'DESTINATION_KIND_MISMATCH'};"
            "if($destination.handle -ne [IntPtr]::new(19)){throw 'DESTINATION_HANDLE_MISMATCH'};"
            "if([string]$HOME -cne $before){throw 'POWERSHELL_HOME_CHANGED'};"
            "Write-Output 'AGENT011_PROTECTED_HOME_ASSIGNMENT_SAFE'"
        )
        p = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand",
             base64.b64encode(ps.encode("utf-16le")).decode("ascii")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.assertEqual(p.returncode, 0, p.stdout + "\n" + p.stderr)
        self.assertIn("AGENT011_PROTECTED_HOME_ASSIGNMENT_SAFE", p.stdout)

    def test_strictmode_send_result_is_a_real_array(self):
        s = self.worker
        self.assertIn(
            "if(@(Active-SendButtons $w).Count -ne 0){throw 'DESTINATION_HAS_PREEXISTING_SEND'}", s
        )
        self.assertIn("$send=@(Active-SendButtons $destination.window)", s)
        self.assertIn("if($send.Count -ne 1)", s)
        self.assertIn("$send[0].invoke.Invoke()", s)
        self.assertNotIn("if((Active-SendButtons $w).Count", s)
        self.assertNotIn("$send=Active-SendButtons $destination.window", s)

    @unittest.skipUnless(shutil.which("powershell.exe"), "Requires Windows PowerShell")
    def test_real_powershell_strictmode_zero_one_two_send_results(self):
        ps = r"""
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
function NoSend(){ return @() }
function OneSend(){ return [pscustomobject]@{token='one'} }
function TwoSend(){ return @([pscustomobject]@{token='first'},[pscustomobject]@{token='second'}) }
$zero=@(NoSend)
$one=@(OneSend)
$two=@(TwoSend)
if($zero.Count -ne 0 -or @(NoSend).Count -ne 0){throw 'ZERO_SEND_INVALID'}
if($one.Count -ne 1 -or $one[0].token -cne 'one'){throw 'ONE_SEND_INVALID'}
if($two.Count -ne 2){throw 'TWO_SEND_INVALID'}
Write-Output 'AGENT011_STRICT_SEND_CARDINALITY_0_1_2_PASS'
"""
        p = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand",
             base64.b64encode(ps.encode("utf-16le")).decode("ascii")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.assertEqual(p.returncode, 0, p.stdout + "\n" + p.stderr)
        self.assertIn("AGENT011_STRICT_SEND_CARDINALITY_0_1_2_PASS", p.stdout)

    def test_four_strong_markers_in_same_group_required(self):
        h = self.helper
        for token in (
            "[GPT_ENGINEERING_ROTATION_HANDOFF_V1]",
            "PCE12 takeover",
            "PCE12.000",
            "[/GPT_ENGINEERING_ROTATION_HANDOFF_V1]",
        ):
            with self.subTest(token=token):
                self.assertIn(token, h)

    @unittest.skipUnless(shutil.which("powershell.exe"), "Requires Windows PowerShell")
    def test_real_powershell_pure_synthetic_groups(self):
        p = str(PROOF).replace("'", "''")
        ps = r"""
$ErrorActionPreference='Stop'
. '%s'
$markers=@(
 '[GPT_ENGINEERING_ROTATION_HANDOFF_V1]',
 'PCE12 takeover',
 'PCE12.000',
 '[/GPT_ENGINEERING_ROTATION_HANDOFF_V1]'
)
$fixtures=@(
 @{name='unique user group';roles=@('You said:');text=$markers;expected=$true},
 @{name='assistant role with full handoff';roles=@('ChatGPT said:');text=$markers;expected=$false},
 @{name='no role with full handoff';roles=@();text=$markers;expected=$false},
 @{name='duplicate user labels';roles=@('You said:','User:');text=$markers;expected=$false},
 @{name='user plus assistant label';roles=@('You said:','ChatGPT said:');text=$markers;expected=$false},
 @{name='begin only';roles=@('You said:');text=@('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]');expected=$false},
 @{name='no closing marker';roles=@('You said:');text=@('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]','PCE12 takeover','PCE12.000');expected=$false},
 @{name='no pce12 ordinal';roles=@('You said:');text=@('[GPT_ENGINEERING_ROTATION_HANDOFF_V1]','PCE12 takeover','[/GPT_ENGINEERING_ROTATION_HANDOFF_V1]');expected=$false},
 @{name='tokens split into nodes';roles=@('You said:');text=@('opening [GPT_ENGINEERING_ROTATION_HANDOFF_V1]','unrelated content','PCE12 takeover','PCE12.000','[/GPT_ENGINEERING_ROTATION_HANDOFF_V1]');expected=$true}
)
$count=0
foreach($fixture in $fixtures){
 $actual=Test-Agent011TurnGroupProof -RoleLabels $fixture.roles -TextNodes $fixture.text
 if([bool]$actual -ne [bool]$fixture.expected){throw ('FIXTURE_MISMATCH_'+$fixture.name)}
 $count++
}
Write-Output ('AGENT011_USER_TURN_PURE_FIXTURES_PASS_'+$count)
""" % p
        result = subprocess.run(
            ["powershell.exe", "-STA", "-NoProfile", "-NonInteractive", "-EncodedCommand",
             base64.b64encode(ps.encode("utf-16le")).decode("ascii")],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=18,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertIn("AGENT011_USER_TURN_PURE_FIXTURES_PASS_9", result.stdout)

    @unittest.skipUnless(shutil.which("powershell.exe"), "Requires Windows PowerShell")
    def test_helper_powershell_parser_without_execution(self):
        p = str(PROOF).replace("'", "''")
        ps = (
            "$tok=$null;$err=$null;"
            "[System.Management.Automation.Language.Parser]::ParseFile('"
            + p
            + "',[ref]$tok,[ref]$err)|Out-Null;"
            "if($err.Count){$err|ForEach-Object{$_.Message};exit 2};"
            "Write-Output 'AGENT011_TURN_PROOF_PARSE_OK'"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand",
             base64.b64encode(ps.encode("utf-16le")).decode("ascii")],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=18,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertIn("AGENT011_TURN_PROOF_PARSE_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
