"""Regressions for PCE10.018/.021/.025 false result suppression and stalled recovery."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COPIES=(ROOT/'content.js',ROOT/'extension'/'content.js',
        ROOT/'extension-persistent'/'content.js')
WORKERS=(ROOT/'extension'/'service_worker.js',
         ROOT/'extension-persistent'/'service_worker.js')

def body_between(text,first,next_):
    start=text.index(first)
    return text[start:text.index(next_,start)]

class ReplaySuppressionGuards(unittest.TestCase):
    def test_source_content_is_identical_in_all_three_active_variants(self):
        self.assertEqual(len({p.read_bytes() for p in COPIES}),1)

    def test_only_exact_standalone_user_result_envelope_counts_as_receipt(self):
        for path in COPIES:
            s=path.read_text(encoding='utf-8')
            b=body_between(s,'function userTurnContainsPacketId(packetId){',
                              'function composerContainsPacketId(')
            self.assertIn('resultPacketIdFromUserUnit(nodes[i])===packetId',b)
            self.assertNotIn('elementText(nodes[i]).includes(packetId)',b)
            self.assertIn('const RESULT_TURN_SELECTOR=USER_SELECTOR;',s)
            self.assertIn('if(!unit?.matches?.(USER_SELECTOR))return null;',s)
            self.assertIn('const match=text.match(/^\\[GPT_WINDOWS_RESULT\\]',s)

    def test_deferred_actions_never_mutate_attempted_ledger_from_ui_text(self):
        for path in COPIES:
            s=path.read_text(encoding='utf-8')
            queued=body_between(s,'function queueDeferredAction(p,','function scheduleDeferredDrain(')
            drained=body_between(s,'function drainDeferredActions()','function forgetAttempted(')
            self.assertNotIn('rememberAttempted(p.id)',queued)
            self.assertNotIn('userTurnContainsPacketId(',queued)
            self.assertNotIn('rememberAttempted(id)',drained)
            self.assertNotIn('userTurnContainsPacketId(',drained)
            self.assertIn('run(p).catch(()=>{})',drained)

    def test_attempted_reconciliation_requires_authenticated_no_execution(self):
        for path in COPIES:
            s=path.read_text(encoding='utf-8')
            run=body_between(s,'async function run(p){','function recoverDiscoveredPacket(') if 'function recoverDiscoveredPacket(' in s[s.index('async function run(p){'):] else s[s.index('async function run(p){'):]
            self.assertIn('if(durable?.state!==\'NO_EXECUTION\')',run)
            self.assertIn('if(durable?.state!==\'NO_EXECUTION\')',s)
            self.assertIn("reason:'packet_status_unavailable'",s)
            self.assertIn('function reconcileAttemptedDiscovery(p,unit)',s)
            inspect=body_between(s,'function inspectUnit(unit){','function latestAssistantPair()')
            self.assertIn('reconcileAttemptedDiscovery(p,unit);',inspect)
            recover=body_between(s,'function recoverScannerForPacket(request){','function reconcileAttemptedDiscovery(')
            self.assertNotIn('if(!target || attempted.has(packetId)',recover)
            self.assertIn('reconcileAttemptedDiscovery(target.parsed,target.unit)',recover)

    def test_worker_keeps_watchdog_until_backend_terminal_state(self):
        for path in WORKERS:
            s=path.read_text(encoding='utf-8')
            terminals=body_between(s,'function terminalScannerEvent(event){','async function clearDiscoveryForEvent(')
            self.assertNotIn('relay_result_replay_suppressed',terminals)
            clear=body_between(s,'async function clearDiscoveryForEvent(','async function recoverStalledScanner(')
            self.assertIn("await call('/packet-status?id='+encodeURIComponent(packetId)",clear)
            self.assertIn("durable?.state!=='EXECUTING'",clear)
            self.assertIn("durable?.state!=='EXECUTION_CONFIRMED'",clear)
            self.assertIn('firstSeen+SCANNER_STALE_MS',s)
            self.assertIn('Number(control.stop_generation)!==Number(record.stop_generation)',s)
            self.assertIn("durable?.state!=='NO_EXECUTION'",s)

if __name__=='__main__':
    unittest.main()
