"""Dynamic Agent011 regression of real result-envelope and strict DOM fallback.

Node runs extracted production functions with synthetic DOM units. This test does
not mutate or refresh any browser, and never simulates a real delivery event.
"""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIRRORS = (
    ROOT / "content.js",
    ROOT / "extension" / "content.js",
    ROOT / "extension-persistent" / "content.js",
)
PACKET = "PCE11.019-synthetic-bubble-result"

class StructuralUserBubbleReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = MIRRORS[0].read_text(encoding="utf-8")
        start = src.index("function resultPacketIdFromExactEnvelope(text){")
        end = src.index("\nfunction hydrateAttemptedFromConversation(){",start)
        parsing = src[start:end]
        user_check_start = src.index("function userTurnContainsPacketId(packetId){")
        user_check_end = src.index("\nfunction composerContainsPacketId(packetId){",user_check_start)
        checker = src[user_check_start:user_check_end]
        payload = {"version":1,"platform":"windows","action":"EXEC","id":PACKET,"status":"OK"}
        inline = "[GPT_WINDOWS_RESULT] " + json.dumps(payload) + " [/GPT_WINDOWS_RESULT]"
        multiline = "[GPT_WINDOWS_RESULT]\n" + json.dumps(payload,indent=2) + "\n[/GPT_WINDOWS_RESULT]"
        cases = {
            "valid_inline": {"text":inline},
            "valid_multiline": {"text":multiline},
            "no_parent": {"text":inline,"parent":False},
            "wrong_parent": {"text":inline,"parent_classes":["flex","flex-col","items-end"]},
            "wrong_parent_alignment": {"text":inline,"parent_classes":["flex","flex-col","items-start","gap-1"]},
            "missing_bubble_class": {"text":inline,"classes":["bg-user-message"]},
            "wrong_tag": {"text":inline,"tag":"SPAN"},
            "assistant_labeled_ancestor": {"text":inline,"closest":True},
            "form_ancestor": {"text":inline,"closest":True},
            "composer_owned": {"text":inline,"composer":True},
            "assistant_quote_prefix": {"text":"Assistant says: "+inline},
            "assistant_quote_suffix": {"text":inline+" Explanation"},
            "bare_id": {"text":PACKET},
            "no_markers": {"text":json.dumps(payload)},
            "malformed": {"text":'[GPT_WINDOWS_RESULT] {bad} [/GPT_WINDOWS_RESULT]'},
            "bad_identity": {"text":"[GPT_WINDOWS_RESULT] "+json.dumps(dict(payload,platform="other"))+" [/GPT_WINDOWS_RESULT]"},
        }
        js=(
            'const USER_SELECTOR="[data-message-role=user]";'
            'const RESULT_TURN_SELECTOR=USER_SELECTOR;'
            'let composer=null, roleNodes=[], bubbles=[], diagnostics=0;'
            'function findComposer(){return composer;}'
            'function emitResultTurnMatchDiagnostic(){diagnostics++;}'
            'const document={querySelectorAll:(selector)=>{'
            ' if(selector===USER_SELECTOR)return roleNodes;'
            ' if(selector===STRUCTURAL_RESULT_BUBBLE_SELECTOR)return bubbles;'
            ' return [];}};\n'
            +parsing+"\n"+checker+"\n"
            +"const cases="+json.dumps(cases)+";\n"
            +"function classList(classes){return {contains:(c)=>classes.includes(c)}}\n"
            +"function bubble(c){"
            +" const parent=c.parent===false?null:{classList:classList(c.parent_classes||['flex','flex-col','items-end','gap-1'])};"
            +" return {tagName:c.tag||'DIV',classList:classList(c.classes||['bg-user-message','text-user-message']),"
            +" parentElement:parent,textContent:c.text,closest:()=>c.closest?{}:null,"
            +" matches:()=>false,contains:()=>Boolean(c.composer)};}\n"
            +"const result={}; for(const [label,c] of Object.entries(cases)){"
            +" const unit=bubble(c); composer=c.composer?{}:null;"
            +" bubbles=[unit];roleNodes=[];"
            +" result[label]={parsed:resultPacketIdFromStructuralUserBubble(unit),"
            +" visible:userTurnContainsPacketId("+json.dumps(PACKET)+")};}\n"
            +"bubbles=[];composer=null;"
            +"roleNodes=[{textContent:cases.valid_inline.text,matches:()=>true,contains:()=>false}];"
            +"result.strict_role={visible:userTurnContainsPacketId("+json.dumps(PACKET)+")};"
            +"console.log(JSON.stringify(result));\n"
        )
        process=subprocess.run(["node","-e",js],capture_output=True,text=True,timeout=20)
        if process.returncode!=0:
            raise AssertionError("Structural DOM test harness rejected: "+process.stderr[-1400:])
        cls.output=json.loads(process.stdout.strip())
        cls.source=src

    def test_real_world_inline_bubble_accepted(self):
        self.assertEqual(self.output["valid_inline"],{"parsed":PACKET,"visible":True})

    def test_multiline_bubble_accepted(self):
        self.assertEqual(self.output["valid_multiline"],{"parsed":PACKET,"visible":True})

    def test_no_direct_right_aligned_parent_denied(self):
        for name in ("no_parent","wrong_parent","wrong_parent_alignment"):
            with self.subTest(name=name):
                self.assertEqual(self.output[name],{"parsed":None,"visible":False})

    def test_class_or_tag_deviation_denied(self):
        for name in ("missing_bubble_class","wrong_tag"):
            with self.subTest(name=name):
                self.assertEqual(self.output[name],{"parsed":None,"visible":False})

    def test_assistant_form_and_composer_denied(self):
        for name in ("assistant_labeled_ancestor","form_ancestor","composer_owned"):
            with self.subTest(name=name):
                self.assertEqual(self.output[name],{"parsed":None,"visible":False})

    def test_embedded_assistant_quote_denied(self):
        for name in ("assistant_quote_prefix","assistant_quote_suffix"):
            with self.subTest(name=name):
                self.assertEqual(self.output[name],{"parsed":None,"visible":False})

    def test_incomplete_or_corrupt_receipts_denied(self):
        for name in ("bare_id","no_markers","malformed","bad_identity"):
            with self.subTest(name=name):
                self.assertEqual(self.output[name],{"parsed":None,"visible":False})

    def test_strict_role_based_match_remains_supported(self):
        self.assertTrue(self.output["strict_role"]["visible"])

    def test_fallback_selector_is_separate_from_strict_role_selector(self):
        self.assertIn("const RESULT_TURN_SELECTOR=USER_SELECTOR;",self.source)
        self.assertIn("const STRUCTURAL_RESULT_BUBBLE_SELECTOR='div.bg-user-message.text-user-message';",self.source)
        self.assertIn("if(resultPacketIdFromUserUnit(nodes[i])===packetId)return true;",self.source)
        self.assertIn("if(resultPacketIdFromStructuralUserBubble(bubbles[i])===packetId)return true;",self.source)

    def test_hydrated_history_scans_strict_bubble_fallback(self):
        section=self.source.split("function hydrateAttemptedFromConversation(){",1)[1].split("\nfunction rememberAttempted",1)[0]
        self.assertIn("document.querySelectorAll(STRUCTURAL_RESULT_BUBBLE_SELECTOR)",section)
        self.assertIn("resultPacketIdFromStructuralUserBubble(nodes[i])",section)

    def test_all_mirrors_equal(self):
        self.assertEqual(MIRRORS[0].read_bytes(),MIRRORS[1].read_bytes())
        self.assertEqual(MIRRORS[0].read_bytes(),MIRRORS[2].read_bytes())

if __name__=="__main__":
    unittest.main()
