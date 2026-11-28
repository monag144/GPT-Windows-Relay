"""Universal Courier: explicit output intake, raw text, and zero transcript scan.

These tests never control the GUI, invoke PowerShell, execute a packet, or
modify the operator's real state. All journal files are in a temporary tree.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import desktop_native_relay as native
import windows_relay as wr


class UniversalCourierTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)
        mappings={
            "HOME":self.root,
            "STATE":self.root/"state.json",
            "CONFIG":self.root/"desktop-control.json",
            "STATUS":self.root/"runtime-status.json",
            "OUTBOX":self.root/"outbox",
            "OUTPUT_REQUESTS":self.root/"explicit-output-requests",
            "OUTPUT_RECEIPTS":self.root/"explicit-output-receipts",
            "DELIVERY_HOLDS":self.root/"delivery-holds",
        }
        for name,value in mappings.items():
            patch=mock.patch.object(native,name,value)
            patch.start()
            self.addCleanup(patch.stop)
        native.configuration()
        self.state=wr.State(native.STATE)
        self.state.set_armed(True)
        self.state.data["outbound_owner"]="windows"
        self.state.save()
        self.aid="COURIER-UNIVERSAL-001"
        self.body="Universal field delivery without application routing"

    def request(self,**overrides):
        row={"version":1,"kind":"EXPLICIT_OUTPUT","id":self.aid,
             "source":"explicit-file","text":self.body,
             "text_sha256":hashlib.sha256(self.body.encode()).hexdigest()}
        row.update(overrides)
        native.OUTPUT_REQUESTS.mkdir(parents=True,exist_ok=True)
        path=native.OUTPUT_REQUESTS/wr.safe_result_filename(self.aid)
        path.write_text(json.dumps(row),encoding="utf-8")
        return path

    def test_queue_explicit_text_does_not_execute_or_scan(self):
        with mock.patch.object(native,"execute_with_stop") as execute, \
             mock.patch.object(native,"process_packet") as process, \
             mock.patch.object(native.subprocess,"run") as subprocess_run:
            native.queue_explicit_output(self.body,aid=self.aid)
            self.assertEqual(native.reconcile_explicit_output_requests(self.state),1)
        execute.assert_not_called()
        process.assert_not_called()
        subprocess_run.assert_not_called()
        delivery=self.state.outbound_lookup(self.aid)
        self.assertEqual(delivery["phase"],"READY")
        self.assertEqual(delivery["wire_format"],"plain_text")
        self.assertEqual(wr.read_outbound_wire_result(self.state,self.aid),self.body)
        self.assertEqual(self.state.lookup(self.aid)["status"],"OUTPUT_READY")
        self.assertEqual(native.reconcile_explicit_output_requests(self.state),0)

    def test_plain_text_outbox_has_independent_receipt_not_in_content(self):
        self.request()
        native.reconcile_explicit_output_requests(self.state)
        path,nonce=native.outbox_result(self.state,self.aid)
        self.assertEqual(path.read_text(encoding="utf-8"),self.body)
        self.assertNotIn(nonce,path.read_text(encoding="utf-8"))
        meta=json.loads(path.with_suffix(".receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["receipt"],nonce)
        self.assertEqual(meta["text_sha256"],hashlib.sha256(self.body.encode()).hexdigest())
        self.assertEqual(native.outbox_result(self.state,self.aid),(path,nonce))
        native._verify_saved_receipt_binding(self.aid,nonce)
        with self.assertRaisesRegex(RuntimeError,"MARKER_INVALID|PLAINTEXT_MISMATCH"):
            native._verify_saved_receipt_binding(self.aid,"NATIVE-RECEIPT-"+"0"*32)

    def test_same_action_id_never_overwrites_different_content(self):
        self.request()
        native.reconcile_explicit_output_requests(self.state)
        with self.assertRaisesRegex(wr.RelayError,"collision"):
            self.state.enqueue_text_output(self.aid,"Different content",source="explicit-file")
        self.assertFalse(self.state.enqueue_text_output(self.aid,self.body,source="explicit-file"))
        self.assertEqual(wr.read_outbound_wire_result(self.state,self.aid),self.body)

    def test_mismatched_hash_is_rejected_before_journal_write(self):
        self.request(text_sha256="0"*64)
        self.assertEqual(native.reconcile_explicit_output_requests(self.state),0)
        self.assertIsNone(self.state.outbound_lookup(self.aid))
        receipt=json.loads((native.OUTPUT_RECEIPTS/wr.safe_result_filename(self.aid)).read_text())
        self.assertEqual(receipt["result"],"REJECTED")

    def test_file_source_requires_explicit_local_text_file(self):
        p=self.root/"user-output.txt"
        p.write_text(self.body,encoding="utf-8")
        native.queue_output_file(str(p),aid=self.aid)
        self.assertEqual(native.reconcile_explicit_output_requests(self.state),1)
        self.assertEqual(wr.read_outbound_wire_result(self.state,self.aid),self.body)
        other=self.root/"unsafe.command"
        other.write_text(self.body,encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"LOCAL_TXT"):
            native.queue_output_file(str(other),aid="COURIER-OTHER")

    def test_unsafe_existing_outbox_without_sidecar_never_recreated(self):
        self.request()
        native.reconcile_explicit_output_requests(self.state)
        native.OUTBOX.mkdir(parents=True,exist_ok=True)
        (native.OUTBOX/(self.aid+".txt")).write_text(self.body,encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError,"ORPHANED_OUTBOX"):
            native.outbox_result(self.state,self.aid)

    def test_previously_queued_request_is_not_double_added(self):
        self.request()
        self.assertEqual(native.reconcile_explicit_output_requests(self.state),1)
        self.request()
        self.assertEqual(native.reconcile_explicit_output_requests(self.state),1)
        self.assertEqual(len(self.state.data["outbound_deliveries"]),1)

    def test_native_runner_has_no_live_third_party_transcript_reader(self):
        native_source=(ROOT/"desktop_native_relay.py").read_text(encoding="utf-8")
        running=native_source.split("def runner():",1)[1].split("HUD_MODE =",1)[0]
        self.assertNotIn("read_scan(",native_source)
        self.assertNotIn("Watch-ChatGPT-ActionCandidates.ps1",native_source)
        self.assertNotIn("SCANNING_CHATGPT_APP",running)
        self.assertNotIn("process_packet(",running)
        self.assertIn("reconcile_explicit_output_requests(state)",running)
        self.assertIn("state.list_claimable_outbound_ids()",running)

    def test_all_apps_have_fail_closed_empty_check_before_unicode_input(self):
        source=(ROOT/"tools"/"Send-Foreground-TextResult.ps1").read_text(encoding="utf-8")
        self.assertIn("function Test-EditorIsCertainlyEmpty(",source)
        self.assertIn("$allowSubmit=Test-EditorIsCertainlyEmpty $target",source)
        self.assertIn("FOREGROUND_EDITOR_NOT_VERIFIABLY_EMPTY",source)
        gate=source.index("$allowSubmit=Test-EditorIsCertainlyEmpty $target")
        injection=source.index("[CourierForegroundInput]::TypeUnicode($chunk)")
        self.assertLess(gate,injection)
        check=source.split("function Test-EditorIsCertainlyEmpty(",1)[1].split(
            "function Assert-CurrentTarget(",1)[0]
        self.assertIn("IsNullOrWhiteSpace",check)
        self.assertIn("return $false",check)
        self.assertNotIn("Test-MessagingComposerTarget",check)
        self.assertIn("[switch]$PlainText",source)
        self.assertIn("FOREIGN_PLAINTEXT_RECEIPT_OR_CONTENT_MISMATCH",source)
        self.assertNotIn("TypeEnter()",source)


if __name__=="__main__":
    unittest.main()
