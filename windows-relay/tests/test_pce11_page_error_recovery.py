"""Regression contracts for bounded visible ChatGPT page-error recovery.

These tests deliberately DO NOT activate Firefox. Live/browser acceptance must
prove a real error banner, page refresh, new-chat click and verified handoff.
"""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
MIRRORS=[
    ROOT/"windows-relay"/"content.js",
    ROOT/"windows-relay"/"extension"/"content.js",
    ROOT/"windows-relay"/"extension-persistent"/"content.js",
]


class PCE11PageErrorRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=MIRRORS[0].read_text(encoding="utf-8")

    def test_three_content_scripts_match_exactly(self):
        data=[p.read_bytes() for p in MIRRORS]
        self.assertEqual(data[0],data[1])
        self.assertEqual(data[1],data[2])

    def test_new_error_surface_classification(self):
        s=self.source
        for marker in ("model_load_error","conversation_load_error",
                       "conversation_wait_error","interrupted_wait_error",
                       "error in input stream","something went wrong"):
            self.assertIn(marker,s)
        self.assertIn("main h1,main h2,main p",s)
        self.assertIn("if(alert.closest?.(ASSISTANT_SELECTOR+','+USER_SELECTOR))continue;",s)
        self.assertIn("if(visibleText.length>400)continue;",s)

    def test_refresh_is_persistent_single_attempt_not_a_loop(self):
        s=self.source
        self.assertIn("GPT_CHATGPT_PAGE_ERROR_REFRESH_NEW_CHAT_V1",s)
        self.assertIn("const PAGE_ERROR_RECOVERY_KEY=",s)
        self.assertIn("sessionStorage.setItem(PAGE_ERROR_RECOVERY_KEY,payload)",s)
        self.assertIn("sessionStorage.getItem(PAGE_ERROR_RECOVERY_KEY)!==payload",s)
        self.assertIn("st={phase:'refreshed',source_url:location.href",s)
        self.assertIn("pageErrorRecoverySave(st);",s)
        self.assertIn("location.reload(); // one refresh only",s)
        self.assertIn("if(st)return; // never loop another refresh",s)
        self.assertIn("PAGE_ERROR_POST_REFRESH_MS=12000",s)

    def test_new_chat_is_visible_click_with_one_shot_handoff(self):
        s=self.source
        self.assertIn("function exactVisibleNewChatControl()",s)
        self.assertIn("candidates.length===1?candidates[0]:null",s)
        self.assertIn("st.phase='new_chat_requested';",s)
        self.assertIn("button.click();",s)
        self.assertIn("location.pathname!=='/'",s)
        self.assertIn("st.phase='handoff_submitting';pageErrorRecoverySave(st)",s)
        self.assertIn("PAGE_ERROR_HANDOFF_TOKEN",s)
        self.assertIn("if(!await waitForUserToken(PAGE_ERROR_HANDOFF_TOKEN,15000))",s)
        self.assertIn("automatic_resend:false",s)
        self.assertIn("st.phase='verified';",s)
        self.assertNotIn("retryButton.click()",s)

    def test_stop_pending_result_and_existing_draft_block_navigation(self):
        s=self.source
        block=s.split("function pageErrorNavigationBlocker(){",1)[1].split(
            "\nfunction pageErrorBlocked(",1)[0]
        for gate in ("operatorPaused","outboundOwner!=='browser'","inflight.size",
                     "pending.size","deferredActions.size","activeRelayOperationId",
                     "submittedResults.size","draftRecoveryInFlight",
                     "consumerMissionInFlight","consumerMissionAwaitingAck()",
                     "elementText(composer).trim()"):
            self.assertIn(gate,block)
        self.assertIn("replay_allowed:false",s)
        self.assertIn("Do NOT repeat any command",s)

    def test_new_chat_acquires_fresh_conversation_url_without_replaying(self):
        s=self.source
        self.assertIn("const sourcePath=new URL(st.source_url).pathname;",s)
        self.assertIn("if(newPath===sourcePath",s)
        self.assertIn("!/^\/c\/[^/?#]+$/.test(newPath)",s)
        self.assertIn("['new_chat_requested','handoff_submitting'].includes(st.phase)",s)
        self.assertIn("if(recentUserTurnContainsToken(PAGE_ERROR_HANDOFF_TOKEN))",s)
        self.assertIn("if(st.phase==='handoff_submitting'){",s)
        self.assertIn("handoff_submission_unconfirmed_no_resend",s)
        self.assertIn("new_chat_composer_not_empty",s)
        self.assertIn("st.phase='verified';st.verified_at=Date.now()",s)

    def test_expired_recovery_record_holds_and_never_arms_second_refresh(self):
        s=self.source
        self.assertIn("return {...st,phase:'expired_hold'}",s)
        self.assertIn("if(st)return; // never loop another refresh",s)
        self.assertNotIn("sessionStorage.removeItem(PAGE_ERROR_RECOVERY_KEY);return null;",s)

    def test_existing_rotation_and_relay_packet_recovery_remain_present(self):
        s=self.source
        self.assertIn("function beginEngineeringRotation(m)",s)
        self.assertIn("function resumeEngineeringRotation()",s)
        self.assertIn("function backgroundPacketStatus(packetId)",s)
        self.assertIn("function maybeScheduleRecoveryRefresh(packetId,now=Date.now())",s)
        self.assertIn("function inspectChatGPTUiError()",s)
        self.assertIn("maybeRecoverChatGPTPageError(found,now);",s)

    def test_executable_error_matcher_examples_when_node_present(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("node is unavailable; separate node --check is mandatory")
        src=self.source
        start=src.index("function chatGPTUiErrorFromText(raw){")
        end=src.index("\nfunction visibleUiElement(",start)
        matcher=src[start:end]
        script=(matcher+"\n"+
            "const examples=[\n"+
            "['The model cannot be loaded','model_load_error'],\n"+
            "['Unable to load the conversation','conversation_load_error'],\n"+
            "['Waiting for conversation results','conversation_wait_error'],\n"+
            "['Connection interrupted. Waiting for the complete answer','interrupted_wait_error'],\n"+
            "['Error in input stream','input_stream_error'],\n"+
            "['Normal answer delivered',null]\n"+
            "];\n"+
            "for(const [txt,want] of examples){const got=chatGPTUiErrorFromText(txt)?.kind||null;"+
            "if(got!==want)throw new Error(JSON.stringify({txt,want,got}));}\n")
        proc=subprocess.run([node,"-e",script],capture_output=True,text=True,timeout=12)
        self.assertEqual(proc.returncode,0,proc.stderr[-1000:])


if __name__=="__main__":
    unittest.main()
