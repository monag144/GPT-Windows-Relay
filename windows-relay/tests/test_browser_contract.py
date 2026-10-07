import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class BrowserContractTests(unittest.TestCase):
    def setUp(self):
        self.src=(ROOT/"content.js").read_text(encoding="utf-8")
        self.live_worker=(ROOT/"extension"/"service_worker.js").read_text(encoding="utf-8")
        self.persistent_worker=(ROOT/"extension-persistent"/"service_worker.js").read_text(encoding="utf-8")

    def test_v11_scanner_marker_present(self):
        self.assertIn("GPT_WINDOWS_EVENT_DRIVEN_SCANNER_V11",self.src)
        self.assertIn("GPT_WINDOWS_STABLE_MAIN_OBSERVER_V1",self.src)
        self.assertIn("GPT_WINDOWS_CODEBLOCK_PACKET_EXTRACTION_V1",self.src)
        self.assertIn("GPT_WINDOWS_CURRENT_CHATGPT_ROLE_SELECTORS_V1",self.src)

    def test_attempted_history_is_bounded(self):
        self.assertIn("MAX_ATTEMPTED=256",self.src)
        self.assertIn("attempted.delete(attemptedOrder.shift())",self.src)

    def test_observer_callback_does_not_rescan_conversation_root(self):
        self.assertNotIn("conversationRoot.querySelectorAll(ASSISTANT_SELECTOR)",self.src)
        self.assertIn("new MutationObserver(bindFromMutations)",self.src)

    def test_recovery_scan_is_low_frequency(self):
        self.assertIn("setInterval(recoverLatestAssistant,15000)",self.src)

    def test_no_document_wide_observer(self):
        self.assertNotIn("observe(document.documentElement",self.src)
        self.assertNotIn("observe(document.body",self.src)

    def test_recovery_scroll_is_one_shot(self):
        self.assertIn("GPT_WINDOWS_RECOVERY_SCROLL_V1",self.src)
        self.assertIn("recoveryScrollDone=true",self.src)
        self.assertEqual(self.src.count("scrollIntoView("),1)
        self.assertIn("scrollToNewestRelayCommandOnce();",self.src)

    def test_recovery_scroll_is_not_in_mutation_callback(self):
        start=self.src.index("function bindFromMutations")
        end=self.src.index("function bindConversationRoot")
        self.assertNotIn("scrollToNewestRelayCommandOnce",self.src[start:end])
        self.assertNotIn("querySelectorAll(ASSISTANT_SELECTOR)",self.src[start:end])

    def test_smart_scroll_is_throttled(self):
        self.assertIn("},1200);",self.src)
        self.assertIn("GPT_WINDOWS_SMART_AUTOSCROLL_V2",self.src)

    def test_action_retry_window_present_in_both_workers(self):
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("ACTION_RETRY_WINDOW_MS=45000",src)
            self.assertIn("DUPLICATE_INFLIGHT",src)
            self.assertIn("callAction(m.packet)",src)

    def test_persistent_worker_keeps_local_pairing_storage(self):
        self.assertIn("chrome.storage.local.get(['relayToken'])",self.persistent_worker)

    def test_packet_parser_is_line_anchored(self):
        self.assertIn("GPT_WINDOWS_LINE_ANCHORED_PACKET_PARSER_V1",self.src)
        self.assertIn("const blockRe=",self.src)
        self.assertNotIn("lastIndexOf(OPEN)",self.src)

    def test_nested_marker_text_cannot_shadow_outer_packet(self):
        self.assertIn("const blockRe=",self.src)
        self.assertIn("while((match=blockRe.exec(text))!==null)",self.src)
        self.assertIn("const parsed=validPacketBody(match[1])",self.src)
        self.assertNotIn("lastIndexOf(OPEN)",self.src)

    def test_persistent_background_port_contract(self):
        self.assertIn("GPT_WINDOWS_PERSISTENT_BACKGROUND_PORT_V1",self.src)
        self.assertIn("chrome.runtime.connect({name:'gpt-windows-relay-content'})",self.src)
        self.assertIn("backgroundAction(p.packet)",self.src)
        self.assertNotIn("chrome.runtime.sendMessage({type:'action',packet:p.packet})",self.src)
        self.assertIn("scheduleBackgroundReconnect()",self.src)

    def test_workers_accept_persistent_content_port(self):
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("chrome.runtime.onConnect.addListener",src)
            self.assertIn("gpt-windows-relay-content",src)
            self.assertIn("relay_action_result",src)
            self.assertIn("callAction(m.packet)",src)

    def test_stable_main_observer_replaces_computed_conversation_root(self):
        self.assertIn("const next=document.querySelector('main');",self.src)
        self.assertNotIn("lowestCommonAncestor(",self.src)
        self.assertIn("conversationObserver.observe(conversationRoot,{childList:true,subtree:true})",self.src)

    def test_packet_extraction_prefers_rendered_code_blocks(self):
        self.assertIn("function extractUnit(unit)",self.src)
        self.assertIn("querySelectorAll?.('pre code, code')",self.src)
        self.assertIn("return extract(unit.textContent||'');",self.src)
        body=self.src[self.src.index("function extractUnit(unit)"):self.src.index("function isAssistantUnit")]
        self.assertNotIn("return extractUnit(unit);",body)

    def test_workers_emit_local_bridge_telemetry(self):
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("async function browserEvent(",src)
            self.assertIn("content_port_connected",src)
            self.assertIn("action_received",src)
            self.assertIn("action_result",src)
            self.assertIn("/browser-event",src)

    def test_current_chatgpt_assistant_selectors_are_supported(self):
        self.assertIn('[data-message-author-role="assistant"]',self.src)
        self.assertIn('article[data-turn="assistant"]',self.src)
        self.assertIn('article[data-testid^="conversation-turn-"]',self.src)
        self.assertIn('section[data-testid^="conversation-turn-"]',self.src)

    def test_explicit_user_turns_fail_closed(self):
        self.assertIn('[data-message-author-role="user"]',self.src)
        self.assertIn("article[data-turn=\"user\"]",self.src)

    def test_content_start_and_scanner_snapshot_telemetry(self):
        self.assertIn("GPT_WINDOWS_TRUE_CONTENT_START_TELEMETRY_V1",self.src)
        self.assertIn("emitRelayEvent('content_script_started'",self.src)
        self.assertNotIn("event:'content_script_loaded'",self.src)
        self.assertIn("event:'scanner_snapshot'",self.src)
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("m?.type==='relay_event'",src)
            self.assertIn("browserEvent(m.event,m.detail??null)",src)

    def test_relay_handoff_scroll_window_is_bounded(self):
        self.assertIn("GPT_WINDOWS_RELAY_HANDOFF_SCROLL_V5",self.src)
        self.assertIn("relayHandoffScrollUntil=Date.now()+8000",self.src)
        self.assertIn("beginRelayHandoffScroll();",self.src)
        self.assertIn("setTimeout(tick,500)",self.src)

    def test_manual_scroll_authority_returns_after_handoff(self):
        self.assertIn("if(Date.now()<relayHandoffScrollUntil)",self.src)
        self.assertIn("followBottom=nearBottom(scrollRoot)",self.src)
        self.assertIn("Date.now()>=relayHandoffScrollUntil",self.src)

    def test_handoff_scroll_emits_viewport_telemetry(self):
        self.assertIn("GPT_WINDOWS_SCROLL_TELEMETRY_V5",self.src)
        self.assertIn("handoff_scroll_start",self.src)
        self.assertIn("handoff_scroll_end",self.src)
        self.assertIn("before_distance",self.src)
        self.assertIn("after_distance",self.src)
        self.assertIn("end_distance",self.src)
        self.assertIn("near_bottom",self.src)

    def test_inject_no_longer_owns_handoff_scroll_start(self):
        start=self.src.index("async function inject(text)")
        end=self.src.index("function scheduleBackgroundReconnect")
        body=self.src[start:end]
        self.assertNotIn("beginRelayHandoffScroll();",body)
        self.assertIn("await send();",body)

    def test_handoff_scroll_persists_across_content_reconnect(self):
        self.assertIn("HANDOFF_SESSION_KEY='gptWindowsRelayHandoffUntil'",self.src)
        self.assertIn("sessionStorage.setItem(HANDOFF_SESSION_KEY",self.src)
        self.assertIn("resumePersistedHandoff();",self.src)
        self.assertIn("handoff_scroll_resumed",self.src)

    def test_worker_drives_scroll_before_result_delivery(self):
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("type:'relay_handoff_scroll'",src)
            self.assertIn("type:'relay_action_result'",src)
            self.assertLess(src.index("type:'relay_handoff_scroll'"),src.index("type:'relay_action_result'"))

    def test_content_handles_worker_scroll_control(self):
        self.assertIn("GPT_WINDOWS_WORKER_DRIVEN_SCROLL_CONTROL_V1",self.src)
        self.assertIn("m?.type==='relay_handoff_scroll'",self.src)
        self.assertIn("beginRelayHandoffScroll();",self.src)

    def test_content_runtime_identity_is_emitted(self):
        self.assertIn("runtime:'v11-scroll-v5-delivery-v13-submit-once-result-wrapper-fallback-approval-v3-uierror-v1-owner-v1'",self.src)

    def test_content_start_event_occurs_outside_connect_function(self):
        connect_start=self.src.index("function connectBackgroundPort()")
        connect_end=self.src.index("function backgroundAction(packet)")
        connect_body=self.src[connect_start:connect_end]
        self.assertNotIn("content_script_started",connect_body)
        startup=self.src.index("connectBackgroundPort();")
        started=self.src.index("emitRelayEvent('content_script_started'")
        self.assertGreaterEqual(started,startup)

    def test_v5_handoff_reacquires_bottom_anchor_and_reinforces_scroll(self):
        self.assertIn("function newestConversationEdge()",self.src)
        self.assertIn("anchor?.scrollIntoView?.({block:'end'",self.src)
        self.assertIn("root?.scrollTo?.({top:root.scrollHeight",self.src)
        self.assertIn("root.scrollTop=root.scrollHeight",self.src)
        self.assertIn("emitRelayEvent('handoff_scroll_tick'",self.src)
        self.assertIn("runtime:'v11-scroll-v5-delivery-v13-submit-once-result-wrapper-fallback-approval-v3-uierror-v1-owner-v1'",self.src)

    def test_result_delivery_submits_once_then_waits_for_exact_turn(self):
        self.assertIn("GPT_WINDOWS_RESULT_DELIVERY_RECOVERY_V1",self.src)
        self.assertIn("GPT_WINDOWS_RESULT_SUBMIT_ONCE_V1",self.src)
        self.assertIn("RESULT_SUBMITTED_SESSION_KEY='gptWindowsRelaySubmittedIdsV1'",self.src)
        self.assertIn("RESULT_SUBMIT_WATCH_MS=120000",self.src)
        self.assertIn("function markResultSubmitted(packetId)",self.src)
        self.assertIn("function trackSubmittedResult(packetId)",self.src)
        self.assertIn("function reconcileSubmittedResults()",self.src)
        self.assertIn("relay_result_send_accepted",self.src)
        self.assertIn("relay_result_waiting_for_gpt_turn_end",self.src)
        self.assertIn("relay_result_turn_end_watchdog_expired",self.src)
        self.assertIn("resend:false",self.src)
        self.assertIn("reexecution:false",self.src)
        wait_start=self.src.index("async function waitForDeliveryConfirmation")
        wait_end=self.src.index("/* GPT_WINDOWS_STALE_OWNER_RELEASE_V1 */",wait_start)
        wait=self.src[wait_start:wait_end]
        self.assertIn("return 'confirmed';",wait)
        self.assertIn("return 'accepted';",wait)
        self.assertIn("method:'composer_cleared_stable'",wait)
        inject_start=self.src.index("async function injectConfirmed(text,packetId,attachments=[])")
        inject_end=self.src.index("async function inject(text)",inject_start)
        inject=self.src[inject_start:inject_end]
        accepted=inject.index("if(deliveryState==='accepted')")
        retry=inject.index("relay_result_send_retry")
        self.assertLess(accepted,retry)
        self.assertIn("markResultSubmitted(packetId);",inject)
        self.assertIn("return 'accepted';",inject)

    def test_delivery_retry_does_not_reexecute_windows_action(self):
        start=self.src.index("async function injectConfirmed(text,packetId,attachments=[])")
        end=self.src.index("async function inject(text)",start)
        block=self.src[start:end]
        self.assertNotIn("backgroundAction(",block)
        self.assertIn("userTurnContainsPacketId(packetId)",block)
        self.assertIn("composerContainsPacketId(packetId)",block)
        self.assertIn("await send(packetId,attempt);",block)

    def test_result_antispam_survives_reload_and_accepts_composer_clear(self):
        self.assertIn("GPT_WINDOWS_RESULT_ANTISPAM_V2",self.src)
        self.assertIn("ATTEMPTED_SESSION_KEY='gptWindowsRelayAttemptedIdsV2'",self.src)
        self.assertIn("function persistAttemptedHistory()",self.src)
        self.assertIn("function hydrateAttemptedHistory()",self.src)
        self.assertIn("function hydrateAttemptedFromConversation()",self.src)
        self.assertIn("sessionStorage.setItem(",self.src)
        self.assertIn("sessionStorage.getItem(ATTEMPTED_SESSION_KEY)",self.src)
        self.assertIn("method:'composer_cleared'",self.src)
        self.assertIn("DELIVERY_CLEAR_STABLE_MS=1500",self.src)
        self.assertIn("relay_result_replay_suppressed",self.src)
        self.assertIn("reason:'existing_user_result_turn'",self.src)

    def test_submitted_result_state_survives_content_reload_without_resend(self):
        self.assertIn("function persistSubmittedResults()",self.src)
        self.assertIn("function hydrateSubmittedResults()",self.src)
        self.assertIn("sessionStorage.getItem(RESULT_SUBMITTED_SESSION_KEY)",self.src)
        self.assertIn("hydrateSubmittedResults();",self.src)
        self.assertIn("for(const id of submittedResults.keys())trackSubmittedResult(id)",self.src)
        track_start=self.src.index("function trackSubmittedResult(packetId)")
        track_end=self.src.index("function reconcileSubmittedResults()",track_start)
        track=self.src[track_start:track_end]
        self.assertNotIn("send(",track)
        self.assertNotIn("backgroundAction(",track)

    def test_existing_user_result_prevents_backend_replay(self):
        run_start=self.src.index("async function run(p)")
        action_call=self.src.index("r=await backgroundAction(p.packet);",run_start)
        guard=self.src.index("if(userTurnContainsPacketId(p.id))",run_start)
        self.assertLess(guard,action_call)
        block=self.src[guard:action_call]
        self.assertIn("rememberAttempted(p.id);",block)
        self.assertIn("relay_result_replay_suppressed",block)

    def test_conversation_hydration_requires_windows_result_marker(self):
        start=self.src.index("function resultPacketIdFromUserUnit(unit)")
        end=self.src.index("function hydrateAttemptedFromConversation()",start)
        block=self.src[start:end]
        self.assertIn("[GPT_WINDOWS_RESULT]",block)
        self.assertIn('text.match(/"id"',block)

    def test_send_readiness_gate_does_not_burn_retry_attempts(self):
        self.assertIn("GPT_WINDOWS_SEND_READINESS_GATE_V1",self.src)
        self.assertIn("SEND_READY_TIMEOUT_MS=90000",self.src)
        self.assertIn("SEND_READY_POLL_MS=250",self.src)
        self.assertIn("function findReadySendButton()",self.src)
        self.assertIn("async function send(packetId=null,attempt=null)",self.src)
        self.assertIn("relay_result_send_waiting",self.src)
        self.assertIn("relay_result_send_ready",self.src)
        inject_start=self.src.index("async function injectConfirmed(text,packetId,attachments=[])")
        inject_end=self.src.index("async function inject(text)",inject_start)
        block=self.src[inject_start:inject_end]
        self.assertIn("await send(packetId,attempt);",block)
        self.assertIn("relay_result_send_retry",block)
        self.assertLess(block.index("await send(packetId,attempt);"),block.index("relay_result_send_retry"))

    def test_preinjection_idle_gate_precedes_set_text(self):
        self.assertIn("GPT_WINDOWS_PREINJECTION_IDLE_GATE_V1",self.src)
        self.assertIn("CHAT_IDLE_TIMEOUT_MS=120000",self.src)
        self.assertIn("CHAT_IDLE_POLL_MS=250",self.src)
        self.assertIn("function activeGenerationStopControl()",self.src)
        self.assertIn("function visibleInterruptedWaitState()",self.src)
        self.assertIn("async function waitForChatIdle(packetId,attempt)",self.src)
        self.assertIn("relay_result_idle_waiting",self.src)
        self.assertIn("relay_result_idle_ready",self.src)
        self.assertIn("relay_result_idle_timeout",self.src)
        start=self.src.index("async function injectConfirmed(text,packetId,attachments=[])")
        end=self.src.index("async function inject(text)",start)
        block=self.src[start:end]
        idle=block.index("await waitForChatIdle(packetId,attempt)")
        set_text=block.index("setText(text)")
        self.assertLess(idle,set_text)

    def test_busy_chat_state_checks_stop_and_interrupted_status(self):
        self.assertIn('[data-testid="stop-button"]',self.src)
        self.assertIn('button[aria-label="Stop generating"]',self.src)
        self.assertIn("connection interrupted",self.src)
        self.assertIn("waiting for the complete answer",self.src)

    def test_existing_relay_draft_blocks_new_backend_action(self):
        self.assertIn("GPT_WINDOWS_RELAY_DRAFT_RECOVERY_V1",self.src)
        run_start=self.src.index("async function run(p)")
        action_call=self.src.index("r=await backgroundAction(p.packet);",run_start)
        draft_guard=self.src.index("const draft=relayDraftFromComposer();",run_start)
        defer=self.src.index("relay_action_deferred_for_existing_draft",draft_guard)
        self.assertLess(draft_guard,action_call)
        self.assertLess(defer,action_call)

    def test_global_operation_owner_serializes_packet_ids(self):
        self.assertIn("let activeRelayOperationId=null;",self.src)
        run_start=self.src.index("async function run(p)")
        action_call=self.src.index("r=await backgroundAction(p.packet);",run_start)
        guard=self.src.index("if(activeRelayOperationId && activeRelayOperationId!==p.id)",run_start)
        claim=self.src.index("activeRelayOperationId=p.id;",guard)
        self.assertLess(guard,action_call)
        self.assertLess(claim,action_call)
        self.assertIn("relay_action_deferred_for_active_operation",self.src)

    def test_startup_recovers_existing_relay_result_draft(self):
        self.assertIn("function relayDraftFromComposer()",self.src)
        self.assertIn("function clearOwnedRelayDraft(packetId)",self.src)
        self.assertIn("async function recoverExistingRelayDraft()",self.src)
        self.assertIn("relay_result_draft_detected",self.src)
        self.assertIn("relay_result_draft_cleared",self.src)
        self.assertIn("relay_result_draft_recovered",self.src)
        self.assertIn("setTimeout(()=>{recoverExistingRelayDraft().catch(()=>{});},150);",self.src)

    def test_draft_recovery_defers_while_normal_delivery_is_inflight(self):
        start=self.src.index("async function recoverExistingRelayDraft()")
        end=self.src.index("async function injectConfirmed(text,packetId,attachments=[])",start)
        block=self.src[start:end]
        self.assertIn("GPT_WINDOWS_RELAY_DRAFT_SINGLE_OWNER_V2",block)
        self.assertIn("if(inflight.has(draft.id))",block)
        self.assertIn("reason:'normal_delivery_inflight'",block)
        self.assertLess(block.index("if(inflight.has(draft.id))"),block.index("draftRecoveryInFlight=true"))

    def test_draft_recovery_preserves_existing_payload_until_idle(self):
        start=self.src.index("async function recoverExistingRelayDraft()")
        end=self.src.index("async function injectConfirmed(text,packetId,attachments=[])",start)
        block=self.src[start:end]
        self.assertIn("await waitForChatIdle(draft.id,0)",block)
        self.assertIn("await send(draft.id,0)",block)
        self.assertIn("await waitForDeliveryConfirmation(draft.id,0)",block)
        self.assertNotIn("setText(",block)

    def test_delivery_v7_accepts_generation_start_as_positive_ack(self):
        self.assertIn("GPT_WINDOWS_GENERATION_START_ACK_V1",self.src)
        start=self.src.index("async function waitForDeliveryConfirmation")
        end=self.src.index("async function recoverExistingRelayDraft",start)
        block=self.src[start:end]
        self.assertIn("const composerHasPacket=composerContainsPacketId(packetId)",block)
        self.assertIn("!composerHasPacket && activeGenerationStopControl()",block)
        self.assertIn("method:'generation_started'",block)

    def test_delivery_v7_queues_deferred_actions_until_owner_releases(self):
        self.assertIn("GPT_WINDOWS_DEFERRED_ACTION_QUEUE_V1",self.src)
        self.assertIn("const MAX_DEFERRED_ACTIONS=16",self.src)
        self.assertIn("function queueDeferredAction(p,reason,ownerId=null)",self.src)
        self.assertIn("function drainDeferredActions()",self.src)
        run_start=self.src.index("async function run(p)")
        action_call=self.src.index("r=await backgroundAction(p.packet);",run_start)
        block=self.src[run_start:action_call]
        self.assertIn("queueDeferredAction(p,'existing_draft',draft.id)",block)
        self.assertIn("queueDeferredAction(p,'active_operation',activeRelayOperationId)",block)
        self.assertIn("relay_action_queued",self.src)
        self.assertIn("relay_action_dequeued",self.src)
        self.assertIn("scheduleDeferredDrain(100)",self.src)

    def test_p4_screenshot_attachment_transport_is_scoped(self):
        self.assertIn("GPT_WINDOWS_CHATGPT_IMAGE_ATTACHMENT_V1",self.src)
        self.assertIn("new DataTransfer()",self.src); self.assertIn("new File([decodeBase64",self.src)
        self.assertIn("await ensureRelayAttachments(attachments,packetId)",self.src)
        self.assertIn("cleanupRelayAttachments(r.attachments||[])",self.src)
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("GPT_WINDOWS_SCREENSHOT_ATTACHMENT_TRANSPORT_V1",src)
            self.assertIn("/managed-screenshot/",src); self.assertIn("relay_attachment_cleanup",src)


    def test_consumer_missions_route_to_active_chatgpt_tab(self):
        self.assertIn("GPT_ONE_CLICK_ACTIVE_TAB_TARGET_V1",self.live_worker)
        self.assertIn("const consumerMissionPorts=new Map()",self.live_worker)
        self.assertIn("chrome.tabs.query({active:true,lastFocusedWindow:true})",self.live_worker)
        self.assertIn("portOwnsConsumerMission(port)",self.live_worker)
        self.assertIn("consumer_mission_target_selected",self.live_worker)
        self.assertNotIn("let consumerMissionPort=null",self.live_worker)

    def test_consumer_active_tab_router_has_safe_single_tab_fallback(self):
        self.assertIn("if(consumerMissionPorts.size===1)return consumerMissionPorts.keys().next().value",self.live_worker)
        self.assertIn("consumerMissionPorts.get(consumerTabId)===port",self.live_worker)

    def test_consumer_worker_polls_only_its_browser_target(self):
        self.assertIn("GPT_ONE_CLICK_BROWSER_QUEUE_TARGET_V1",self.live_worker)
        self.assertIn("RELAY_BROWSER_ID",self.live_worker)
        self.assertIn("mission-next?browser_id=",self.live_worker)
        self.assertIn("browser_id:RELAY_BROWSER_ID",self.live_worker)

    def test_consumer_worker_reports_browser_integration_heartbeat(self):
        self.assertIn("GPT_ONE_CLICK_BROWSER_HEARTBEAT_V1",self.live_worker)
        self.assertIn("browserHeartbeat()",self.live_worker)
        self.assertIn("/browser-heartbeat?browser_id=",self.live_worker)
        self.assertIn("browser_integration_connected",self.live_worker)
        self.assertIn("browser_integration_disconnected",self.live_worker)


    def test_relay_actions_carry_conversation_identity(self):
        for path in (
            ROOT/"content.js",
            ROOT/"extension"/"content.js",
            ROOT/"extension-persistent"/"content.js",
        ):
            src=path.read_text(encoding="utf-8-sig")
            self.assertIn("GPT_RELAY_CONVERSATION_OWNER_V1",src,path)
            self.assertIn("function relayConversationKey()",src,path)
            self.assertIn("conversation_key:relayConversationKey()",src,path)
            self.assertIn("conversation_href:location.href",src,path)

    def test_workers_enforce_persisted_conversation_owner(self):
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("GPT_RELAY_CONVERSATION_OWNER_V1",src)
            self.assertIn("RELAY_OWNER_KEY='gptRelayConversationOwnerV1'",src)
            self.assertIn("checkAndClaimRelayOwner",src)
            self.assertIn("chrome.tabs.query({active:true,lastFocusedWindow:true})",src)
            self.assertIn("relay_owner_unclaimed_inactive_tab",src)
            self.assertIn("legacy_default_session_blocked",src)
            self.assertIn("relay_owner_same_session_different_conversation",src)
            self.assertIn("relay_owner_transfer_requires_claim",src)
            self.assertIn("relay_cross_conversation_suppressed",src)
            self.assertIn("relay_conversation_owner_transferred",src)

    def test_late_packet_cursor_uses_explicit_op_token_per_owner(self):
        for src in (self.live_worker,self.persistent_worker):
            self.assertIn("GPT_RELAY_LATE_PACKET_CURSOR_V2",src)
            self.assertIn("GPT_RELAY_OP_TOKEN_CURSOR_V1",src)
            self.assertIn("OPERATION_CURSOR_KEY='gptRelayOperationCursorV2'",src)
            self.assertIn("match(/(?:^|[-.])OP(\\d+)([a-z]*)(?=[-.]|$)/i)",src)
            self.assertIn("cursor.owner_key===ownerKey",src)
            self.assertIn("checkAndAdvanceOperationCursor(packetId,ownerDecision.owner)",src)
            self.assertNotIn("for(const key of ['generation','ordinal','suffix_rank'])",src)

    def test_default_session_cannot_take_over_existing_owner(self):
        for src in (self.live_worker,self.persistent_worker):
            owner=src[src.index("function checkAndClaimRelayOwner"):src.index("function checkAndAdvanceOperationCursor")]
            self.assertIn("if(session==='default')return {ok:false,error:'legacy_default_session_blocked',owner};",owner)
            self.assertLess(
                owner.index("if(session==='default')"),
                owner.index("const incomingVersion=relaySessionVersion(session)")
            )


if __name__=="__main__":
    unittest.main()
