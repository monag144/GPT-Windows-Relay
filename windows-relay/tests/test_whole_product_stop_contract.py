import unittest
import tempfile
import windows_relay as relay
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class WholeProductStopContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content=(ROOT/'content.js').read_text(encoding='utf-8')
        cls.ext=(ROOT/'extension'/'content.js').read_text(encoding='utf-8')
        cls.persist=(ROOT/'extension-persistent'/'content.js').read_text(encoding='utf-8')
        cls.sw=(ROOT/'extension'/'service_worker.js').read_text(encoding='utf-8')
        cls.control=(ROOT/'relay-control.ps1').read_text(encoding='utf-8')

    def test_content_copies_are_identical(self):
        self.assertEqual(self.content,self.ext)
        self.assertEqual(self.content,self.persist)

    def test_paused_by_default_and_positive_resume(self):
        s=self.content
        self.assertIn('let operatorPaused=true;',s)
        self.assertIn("if(m.armed===true && operatorPaused)resumeBrowserRelay('backend_armed');",s)
        resume=s[s.index('function resumeBrowserRelay('):s.index('function applyOperatorControlState(')]
        self.assertIn('resumePersistedHandoff();',resume)
        self.assertIn("stop_contract:'whole-stop-v1'",s)
        self.assertIn("runtime:'v11-scroll-v5-delivery-v17-whole-stop-v1",s)

    def test_active_delivery_has_abort_barriers(self):
        s=self.content
        for token in [
            'async function send(packetId=null,attempt=null){\n  assertOperatorActive();',
            'async function waitForChatIdle(packetId,attempt){\n  assertOperatorActive();',
            'async function waitForDeliveryConfirmation(packetId,attempt){\n  assertOperatorActive();',
            'async function injectConfirmed(text,packetId,attachments=[]){\n  assertOperatorActive();',
            "if(operatorPaused)throw e;",
            "function backgroundAction(packet){\n  if(operatorPaused)return Promise.reject(new Error('operator_paused'));"
        ]: self.assertIn(token,s)

    def test_autonomous_schedulers_are_pause_guarded(self):
        s=self.content
        for token in [
            'function scheduleDraftRecovery(delay=1000){\n  if(operatorPaused)return;',
            'function scheduleDeferredDrain(delay=100){\n  if(operatorPaused)return;',
            'function drainDeferredActions(){\n  if(operatorPaused)return;',
            'function maybeScheduleRecoveryRefresh(packetId,now=Date.now()){\n  if(operatorPaused)return;',
            'function forceRecoveryPacketInspect(){\n  if(operatorPaused)return;',
            'function scheduleWatchedInspect(){\n  if(operatorPaused)return;',
            'function scheduleAutoScroll(){\n  if(operatorPaused)return;',
            'function recoverLatestAssistant(){\n  if(operatorPaused)return;',
            'function scheduleChatGPTUiErrorInspect(){\n  if(operatorPaused)return;',
            'function scheduleToolApprovalPromptInspect(){\n  if(operatorPaused)return;'
        ]: self.assertIn(token,s)

    def test_quiesce_cancels_long_lived_work(self):
        s=self.content
        for token in [
            'clearInterval(recoveryTimer)',
            'clearInterval(consumerMissionPollTimer)',
            'clearInterval(approvalInspectInterval)',
            'clearInterval(uiErrorInspectInterval)',
            'submittedWatchTimers.clear();',
            "pendingRequest.reject(new Error('operator_paused'))",
            'watchedObserver?.disconnect()',
            'conversationObserver?.disconnect()',
            'approvalPromptObserver?.disconnect()',
            'uiErrorObserver?.disconnect()'
        ]: self.assertIn(token,s)

    def test_control_poll_survives_pause_but_runtime_reload_does_not(self):
        s=self.content
        self.assertIn('operatorControlPollTimer=setInterval(pollOperatorControlState,2000)',s)
        block=s[s.index('function scheduleBackgroundReconnect()'):s.index('function connectBackgroundPort()')]
        self.assertNotIn('if(operatorPaused)return;',block)
        self.assertIn('!operatorPaused &&',block)
        quiesce=s[s.index('function quiesceBrowserRelay('):s.index('function resumeBrowserRelay(')]
        self.assertNotIn('backgroundPortReconnectTimer,draftRecoveryTimer',quiesce)

    def test_service_worker_bridges_backend_state(self):
        self.assertIn("m?.type==='operator_control_poll'",self.sw)
        self.assertIn("function controlStateMessage(st,online=true)",self.sw)
        self.assertIn("type:'operator_control_state',online,armed:!!st?.armed",self.sw)
        self.assertIn("broadcastControlState(controlStateMessage(",self.sw)
        self.assertIn("type:'operator_control_state',online:false",self.sw)

    def test_stop_waits_for_exact_generation_before_listener_kill(self):
        block=self.control[self.control.index("if($Action -in @('stop','pause'))"):self.control.index("if($Action -eq 'restart')")]
        self.assertLess(block.index('SetBackendArm $false'),block.index('WaitBrowserQuiesced'))
        self.assertLess(block.index('WaitBrowserQuiesced'),block.index('taskkill /PID'))
        self.assertIn('BROWSER_QUIESCENCE=',block)
        self.assertIn("'VERIFIED'",block)
        self.assertIn("'UNVERIFIED'",block)
        self.assertNotIn('Start-Sleep -Milliseconds 700',block)
        self.assertIn("New-Item -ItemType File -Force -Path $pause",block)

    def test_autoapproval_yields_to_stop(self):
        self.assertIn('if(operatorPaused)return;\n          alwaysAllow.click();',self.content)


    def test_stop_uses_credentials_matching_listener_port(self):
        s=self.control
        self.assertIn('GPTWindowsRelay',s)
        self.assertIn('GPTWindowsRelayConsumer',s)
        self.assertIn('$listenerPort',s)
        self.assertIn('[int]$candidate.port -eq $listenerPort',s)
        self.assertIn('SetBackendArm $false ([int]$l.LocalPort)',s)


    def test_content_quiesces_before_exact_generation_ack(self):
        src=self.content
        block=src[src.index('function applyOperatorControlState('):src.index('function pollOperatorControlState(')]
        self.assertLess(block.index("quiesceBrowserRelay('backend_disarmed')"),block.index('acknowledgeOperatorQuiescedGeneration(m.stop_generation)'))
        ack=src[src.index('function acknowledgeOperatorQuiescedGeneration('):src.index('function applyOperatorControlState(')]
        self.assertIn("type:'operator_quiesced_ack',stop_generation:g",ack)
        self.assertLess(ack.index('port.postMessage('),ack.index('lastOperatorQuiescedGeneration=g;'))

    def test_workers_require_all_ports_from_frozen_generation_snapshot(self):
        for sw in (self.sw,(ROOT/'extension-persistent'/'service_worker.js').read_text(encoding='utf-8')):
            self.assertIn('const relayContentPorts=new Set();',sw)
            self.assertIn('operatorStopAckExpected=new Set(relayContentPorts);',sw)
            self.assertIn('operatorStopAckExpected.has(port)',sw)
            self.assertIn('operatorStopAckReceived.add(port);',sw)
            self.assertIn("browserEvent('browser_operator_quiesced_all'",sw)
            self.assertIn('expected_ports:operatorStopAckExpected.size',sw)
            self.assertIn('acked_ports:operatorStopAckReceived.size',sw)
            self.assertNotIn('operatorStopAckExpected.delete(',sw)
            # Quiescence reports the frozen numeric generation after verifying
            # all ports, not the previous un-normalized variable name.
            self.assertIn("stop_generation:g,",sw)
            self.assertIn("g===operatorStopAckGeneration",sw)

    def test_backend_rejects_stale_stop_generation_ack(self):
        with tempfile.TemporaryDirectory() as d:
            state=relay.State(Path(d)/'state.json')
            state.load()
            g1=state.set_armed(False)
            self.assertGreater(g1,0)
            self.assertFalse(state.ack_browser_quiesced(g1-1))
            self.assertTrue(state.ack_browser_quiesced(g1))
            self.assertEqual(state.operator_stop_status()['browser_quiesced_generation'],g1)
            state.set_armed(True)
            g2=state.set_armed(False)
            self.assertEqual(g2,g1+1)
            self.assertFalse(state.ack_browser_quiesced(g1))
            self.assertTrue(state.ack_browser_quiesced(g2))

    def test_backend_and_controller_expose_correlated_stop_generation(self):
        backend=(ROOT/'windows_relay.py').read_text(encoding='utf-8')
        self.assertIn("'stop_generation'",backend)
        self.assertIn("'browser_quiesced_generation'",backend)
        self.assertIn("event=='browser_operator_quiesced_all'",backend)
        self.assertIn('ack_browser_quiesced',backend)
        self.assertIn('function WaitBrowserQuiesced',self.control)
        self.assertIn('stop_generation -eq $generation',self.control)
        self.assertIn('browser_quiesced_generation -eq $generation',self.control)
        self.assertIn('5000',self.control)


    def test_outbound_owner_uses_existing_authenticated_status_control_plane(self):
        root=__import__('pathlib').Path(__file__).resolve().parents[1]
        backend=(root/'windows_relay.py').read_text(encoding='utf-8-sig')
        self.assertIn("'outbound_owner':self.server.state.outbound_owner",backend)
        for rel in ('extension/service_worker.js','extension-persistent/service_worker.js'):
            src=(root/rel).read_text(encoding='utf-8-sig')
            self.assertIn("call('/status'",src)
            self.assertIn("outbound_owner:st?.outbound_owner==='windows'?'windows':'browser'",src)
        for rel in ('content.js','extension/content.js','extension-persistent/content.js'):
            src=(root/rel).read_text(encoding='utf-8-sig')
            self.assertIn("let outboundOwner='browser';",src)
            self.assertIn("if(outboundOwner==='windows')",src)
            self.assertIn("relay_result_delivery_delegated_windows",src)

if __name__=='__main__':
    unittest.main()
