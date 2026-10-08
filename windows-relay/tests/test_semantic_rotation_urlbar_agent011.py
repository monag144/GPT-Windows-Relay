"""Safe, real-PowerShell tests for Firefox's scheme-less UIA URL bar.

Only extract and invoke pure URL-parser helpers on synthetic input; no UI
interaction, no worker execution, no clicks or navigation.
"""
import base64
import shutil
import subprocess
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"semantic_agent_rotation.ps1"
UUID="123e4567-e89b-12d3-a456-426614174000"


class FirefoxUrlbarRotationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=SCRIPT.read_text(encoding="ascii")

    def test_normalizer_at_every_source_home_and_handoff_identity_gate(self):
        for token in (
            "function Normalize-RotationConversationUrl(",
            "function Test-RotationHomeAddress(",
            "try{$url=Normalize-RotationConversationUrl $rawSourceUrl}",
            "Normalize-RotationConversationUrl (UrlBar $window)",
            "Test-RotationHomeAddress $newUrl",
            "Test-RotationHomeAddress (UrlBar $window)",
            "try{$canonicalNewUrl=Normalize-RotationConversationUrl $newUrl}",
            "$state.new_url=$canonicalNewUrl",
            "ROTATION_CONVERSATION_ADDRESS_UNTRUSTED",
        ):
            with self.subTest(token=token):
                self.assertIn(token,self.src)

    def test_real_powershell_scheme_less_url_and_lookalike_rejection(self):
        exe=shutil.which("powershell.exe")
        if not exe:
            self.skipTest("Windows PowerShell not installed")
        start=self.src.index("function Normalize-RotationConversationUrl(")
        end=self.src.index("function DocumentBody($window){",start)
        pure_helpers=self.src[start:end]
        valid=["chatgpt.com/c/"+UUID,"https://chatgpt.com/c/"+UUID,
               "chatgpt.com/c/"+UUID+"/","https://chatgpt.com/c/"+UUID+"/"]
        invalid=["https://chatgpt.com.evil.org/c/"+UUID,
                 "http://chatgpt.com/c/"+UUID,
                 "chatgpt.com:443/c/"+UUID,
                 "chatgpt.com/c/"+UUID+"?share=1",
                 "chatgpt.com/c/"+UUID+"#section",
                 "chatgpt.com/g/"+UUID,
                 "chatgpt.com/c/short",
                 "chatgpt.com@evil.org/c/"+UUID,
                 "https://evil.org/c/"+UUID,
                 "chatgpt.com/c/"+("a"*130),
                 "chatgpt.com/c/"+UUID+"/other","chatgpt.com/"]
        home_valid=["chatgpt.com","chatgpt.com/","https://chatgpt.com","https://chatgpt.com/"]
        home_invalid=["chatgpt.com/c/"+UUID,"chatgpt.com.evil.org",
                      "chatgpt.com/?model=x","http://chatgpt.com","chatgpt.com:443/"]
        def ps_array(items):
            return "@("+",".join("'"+x+"'" for x in items)+")"
        ps=pure_helpers+"\n"
        ps+="$valid="+ps_array(valid)+"\n"
        ps+="$invalid="+ps_array(invalid)+"\n"
        ps+="$home_valid="+ps_array(home_valid)+"\n"
        ps+="$home_invalid="+ps_array(home_invalid)+"\n"
        ps+="foreach($x in $valid){$result=Normalize-RotationConversationUrl $x;if($result -cne 'https://chatgpt.com/c/"+UUID+"'){throw 'VALID_ADDRESS_REJECTED'}}\n"
        ps+="foreach($x in $invalid){$rejected=$false;try{$null=Normalize-RotationConversationUrl $x}catch{$rejected=$true};if(-not $rejected){throw 'INVALID_ADDRESS_ACCEPTED'}}\n"
        ps+="foreach($x in $home_valid){if(-not(Test-RotationHomeAddress $x)){throw 'VALID_HOME_REJECTED'}}\n"
        ps+="foreach($x in $home_invalid){if(Test-RotationHomeAddress $x){throw 'INVALID_HOME_ACCEPTED'}}\n"
        ps+="Write-Output ROTATION_URLBAR_CONTRACT_OK\n"
        encoded=base64.b64encode(ps.encode("utf-16le")).decode("ascii")
        result=subprocess.run([exe,"-NoProfile","-NonInteractive","-EncodedCommand",encoded],
                              capture_output=True,text=True,encoding="utf-8",
                              errors="replace",timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+"\n"+result.stderr)
        self.assertIn("ROTATION_URLBAR_CONTRACT_OK",result.stdout)


if __name__=="__main__":
    unittest.main()
