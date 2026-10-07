from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    ROOT / "windows-relay" / "content.js",
    ROOT / "windows-relay" / "extension" / "content.js",
    ROOT / "windows-relay" / "extension-persistent" / "content.js",
)

class ChatGPTContentContractTests(unittest.TestCase):
    def test_external_worked_for_status_has_bounded_recovery_path(self):
        src=(Path(__file__).resolve().parents[2]/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8")
        self.assertIn("GPT_ONE_CLICK_EXTERNAL_COLLAPSE_STATUS_V1",src)
        self.assertIn("consumer_relay_external_collapse_detected",src)
        self.assertIn("ctx.action_seen",src)
        self.assertIn("externalStatus",src)

    def test_current_composer_shape(self):
        for path in FILES:
            src = path.read_text(encoding="utf-8-sig")
            self.assertIn("GPT_CHATGPT_COMPOSER_MULTI_SHAPE_V1", src, path)
            self.assertIn("textarea#mobile-composer-prompt", src, path)
            self.assertIn('textarea[name="prompt"][aria-label="Chat with ChatGPT"]', src, path)

    def test_current_send_button_shape(self):
        for path in FILES:
            src = path.read_text(encoding="utf-8-sig")
            self.assertIn("GPT_CHATGPT_SEND_BUTTON_MULTI_SHAPE_V1", src, path)
            self.assertIn('button[aria-label="Send message"]', src, path)

    def test_consumer_mission_requires_visible_user_turn_ack(self):
        src = (ROOT / "windows-relay" / "content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_ONE_CLICK_MISSION_VISIBLE_ACK_V1", src)
        self.assertIn("GPT_ONE_CLICK_CLIENT_SYNC_DIVERGENCE_V1", src)
        self.assertIn("consumer_mission_client_sync_divergence", src)
        self.assertIn("CONSUMER_MISSION_ACK_KEY", src)
        self.assertIn("consumer_mission_user_turn_not_confirmed", src)

    def test_consumer_relay_collapse_recovery_contract(self):
        src = (ROOT / "windows-relay" / "content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_ONE_CLICK_RELAY_OUTPUT_CLASSIFIER_V1", src)
        self.assertIn("GPT_ONE_CLICK_COLLAPSE_AUTO_RECOVERY_V1", src)
        self.assertIn("COLLAPSED_STATUS_ARTIFACT", src)
        self.assertIn("Worked for", src)
        self.assertIn("echo RELAY_RENDER_PROBE_OK", src)
        self.assertIn("probe_proven_resume_expected", src)
        self.assertIn("DOCUMENT_POSITION_FOLLOWING", src)
        self.assertIn("CONSUMER_RECOVERY_MAX=2", src)

    def test_no_action_packet_is_valid_conversational_completion(self):
        src = (ROOT / "windows-relay" / "extension" / "content.js").read_text(encoding="utf-8-sig")
        self.assertIn("consumer_mission_completed_without_relay", src)
        self.assertIn("firstActionMissing && c.kind==='NO_ACTION_PACKET'", src)
        self.assertNotIn("c.kind==='NO_ACTION_PACKET'||c.kind==='INCOMPLETE_SANDWICH'", src)
        self.assertIn("firstActionMissing && c.kind==='INCOMPLETE_SANDWICH'", src)

    def test_recovery_prompt_contains_literal_closing_fence_contract(self):
        src = (ROOT / "windows-relay" / "extension" / "content.js").read_text(encoding="utf-8-sig")
        self.assertIn("const fence='```'", src)
        self.assertIn("The second ${fence} line CLOSES the Markdown fence", src)
        self.assertIn("FOOTER must be outside it", src)

    def test_missing_mission_composer_is_observable(self):
        src = (ROOT / "windows-relay" / "content.js").read_text(encoding="utf-8-sig")
        self.assertIn("consumer_mission_composer_not_found", src)

    def test_extension_forces_reinspection_and_has_bounded_stall_watchdog(self):
        src=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_WINDOWS_FORCED_RECOVERY_REINSPECTION_V1",src)
        self.assertIn("GPT_WINDOWS_FIVE_MINUTE_STALL_WATCHDOG_V1",src)
        self.assertIn("forceRecoveryPacketInspect()",src)
        self.assertIn("RELAY_STALL_PATIENCE_MS=300000",src)
        self.assertIn("location.reload()",src)

    def test_chatgpt_tool_approval_prompt_is_detected_and_observable(self):
        src=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_CHATGPT_TOOL_APPROVAL_PROMPT_DETECTOR_V1",src)
        self.assertIn("chatgpt_tool_approval_prompt_detected",src)
        self.assertIn("always allow",src.lower())
        self.assertIn("MutationObserver(scheduleToolApprovalPromptInspect)",src)
        self.assertIn("bindToolApprovalPromptDetector();",src)
        self.assertGreater(
            src.index("bindToolApprovalPromptDetector();"),
            src.index("connectBackgroundPort();"),
        )
        self.assertIn("for(let depth=0;depth<8 && node;depth++,node=node.parentElement)",src)
        self.assertIn("approval_detector_bound:!!approvalPromptObserver",src)
        self.assertIn("collapse-recovery-approval-v2",src)

    def test_discovered_packet_reacquires_if_chatgpt_remounts_during_settle(self):
        src=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_WINDOWS_DISCOVERY_SETTLE_REACQUIRE_V1",src)
        self.assertIn("relay_packet_settle_reacquire",src)
        self.assertIn("recoverDiscoveredPacket(p,'unit_disconnected')",src)
        self.assertIn("recoverDiscoveredPacket(p,'packet_changed_during_settle')",src)
        self.assertIn("setTimeout(()=>recoverLatestAssistant(),0)",src)

    def test_service_worker_rotates_firefox_chat_every_100_operations(self):
        src=(ROOT/"windows-relay"/"extension"/"service_worker.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_RELAY_CHAT_ROTATION_100_V1",src)
        self.assertIn("CHAT_ROTATION_EVERY=100",src)
        self.assertIn("noteDeliveredOperation",src)
        self.assertIn("https://chatgpt.com/",src)

    def test_recovery_advice_has_secondary_observer_contract(self):
        src=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_WINDOWS_RECOVERY_ADVICE_SECONDARY_OBSERVER_V1",src)
        self.assertIn("gpt_recovery_advice_observed",src)
        self.assertIn("gpt_recovery_advice_invalid",src)
        self.assertIn("RECOVERY_ADVICE_ALLOWED",src)


    def test_visible_chatgpt_error_is_observable_without_automatic_retry_click(self):
        src=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_CHATGPT_VISIBLE_ERROR_DETECTOR_V1",src)
        self.assertIn("error in input stream",src.lower())
        self.assertIn("chatgpt_ui_error_detected",src)
        self.assertIn("chatgpt_ui_error_cleared",src)
        self.assertIn("bindChatGPTUiErrorDetector();",src)
        self.assertIn("ui_error_detector_bound:!!uiErrorObserver",src)
        self.assertNotIn("retryButton.click()",src)

    def test_exact_result_confirmation_and_stale_owner_release_contract(self):
        for path in FILES:
            src = path.read_text(encoding="utf-8-sig")
            self.assertIn("GPT_WINDOWS_EXACT_RESULT_CONFIRMATION_V1", src, path)
            self.assertIn("GPT_WINDOWS_STALE_OWNER_RELEASE_V1", src, path)
            confirm = src.split("/* GPT_WINDOWS_EXACT_RESULT_CONFIRMATION_V1 */", 1)[1].split(
                "/* GPT_WINDOWS_STALE_OWNER_RELEASE_V1 */", 1
            )[0]
            self.assertIn("method:'user_result_turn'", confirm, path)
            self.assertIn("relay_result_send_progress", confirm, path)
            self.assertIn("relay_result_send_unconfirmed", confirm, path)
            self.assertEqual(confirm.count("return true;"), 1, path)
            recovery = src.split("/* GPT_WINDOWS_STALE_OWNER_RELEASE_V1 */", 1)[1].split(
                "// GPT_WINDOWS_CHATGPT_IMAGE_ATTACHMENT_V1", 1
            )[0]
            self.assertIn("attempted.has(draft.id)", recovery, path)
            self.assertIn("reason:'already_exactly_delivered'", recovery, path)
            self.assertIn("reason:'exact_user_result_visible_no_draft'", recovery, path)
            self.assertIn("if(activeRelayOperationId===draft.id)activeRelayOperationId=null", recovery, path)

    def test_recovery_obligation_survives_dom_virtualization_and_owner_is_bounded(self):
        src=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_WINDOWS_DURABLE_RECOVERY_OBLIGATION_V1",src)
        self.assertIn("GPT_WINDOWS_STALE_OWNER_LEASE_V1",src)
        self.assertIn("RECOVERY_WATCH_SESSION_KEY='gptWindowsRelayRecoveryWatchV1'",src)
        self.assertIn("hydrateRecoveryPacketWatch();",src)
        self.assertIn("persistRecoveryPacketWatch();",src)
        self.assertIn("relay_recovery_obligation_restored",src)
        self.assertIn("stale_owner_lease_expired_for_exact_replay",src)
        self.assertIn("source:'durable_recovery_obligation'",src)
        watchdog=src.split("function forceRecoveryPacketInspect(){",1)[1].split(
            "function scrollToNewestRelayCommandOnce(){",1
        )[0]
        no_unit=watchdog.split("if(!unit){",1)[1].split("\n  const p=extractUnit(unit);",1)[0]
        self.assertNotIn("resetRecoveryPacketWatch();",no_unit)
        self.assertIn("maybeScheduleRecoveryRefresh(recoveryPacketId,now)",no_unit)

    def test_content_runtime_reports_owner_generation(self):
        for path in FILES:
            src=path.read_text(encoding="utf-8-sig")
            self.assertIn("owner-v1",src,path)

    def test_late_packet_cursor_is_scoped_to_conversation_owner_and_explicit_op_token(self):
        workers=(
            ROOT/"windows-relay"/"extension"/"service_worker.js",
            ROOT/"windows-relay"/"extension-persistent"/"service_worker.js",
        )
        for path in workers:
            worker=path.read_text(encoding="utf-8-sig")
            self.assertIn("GPT_RELAY_LATE_PACKET_CURSOR_V2",worker,path)
            self.assertIn("GPT_RELAY_CONVERSATION_OWNER_V1",worker,path)
            self.assertIn("GPT_RELAY_OP_TOKEN_CURSOR_V1",worker,path)
            self.assertIn("OPERATION_CURSOR_KEY='gptRelayOperationCursorV2'",worker,path)
            self.assertIn("RELAY_OWNER_KEY='gptRelayConversationOwnerV1'",worker,path)
            self.assertIn("operationSeriesPosition",worker,path)
            self.assertIn("match(/(?:^|[-.])OP(\\d+)([a-z]*)(?=[-.]|$)/i)",worker,path)
            self.assertIn("cursor.owner_key===ownerKey",worker,path)
            self.assertIn("checkAndClaimRelayOwner",worker,path)
            self.assertIn("relay_cross_conversation_suppressed",worker,path)
            self.assertIn("relay_late_packet_suppressed",worker,path)
            self.assertIn("error:'late_packet_suppressed'",worker,path)
        for path in FILES:
            src=path.read_text(encoding="utf-8-sig")
            self.assertIn("conversation_key:relayConversationKey()",src,path)
            self.assertIn("r?.error==='late_packet_suppressed'",src,path)
            self.assertIn("reason:'newer_operation_cursor'",src,path)

if __name__ == "__main__":
    unittest.main()