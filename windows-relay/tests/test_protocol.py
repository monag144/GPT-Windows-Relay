import base64, json, tempfile, unittest
from unittest import mock
from pathlib import Path
import windows_relay as wr

def pkt(id="t1",command="Write-Output hi",**extra):
    p={"version":1,"platform":"windows","action":"EXEC","id":id,"session":"default","shell":"powershell","command":command,"timeout":10};p.update(extra)
    return f"{wr.OPEN}\n{json.dumps(p)}\n{wr.CLOSE}"

class Tests(unittest.TestCase):
    def test_parse(self): self.assertEqual(wr.extract(pkt()).id,"t1")
    def test_default_result_mode_is_compact(self): self.assertEqual(wr.extract(pkt()).result_mode,"compact")
    def test_full_result_mode_accepted(self): self.assertEqual(wr.extract(pkt(result_mode="full")).result_mode,"full")
    def test_invalid_result_mode_rejected(self):
        with self.assertRaises(wr.PacketError): wr.extract(pkt(result_mode="huge"))
    def test_platform(self):
        with self.assertRaises(wr.PacketError): wr.extract(pkt(platform="linux"))
    def test_bridge_owner_metadata_is_accepted_and_hashed(self):
        a=wr.extract(pkt(id="owner-meta",session="pce8.1",owner_claim=True))
        self.assertEqual(a.session,"pce8.1")
        b=wr.extract(pkt(id="owner-meta",session="pce8.1",owner_claim=False))
        self.assertNotEqual(a.hash,b.hash)

    def test_b64(self):
        x=base64.b64encode(b"Write-Output encoded").decode(); self.assertEqual(wr.extract(pkt(command=None,command_b64=x)).command,"Write-Output encoded")
    def test_command_lines(self):
        a=wr.extract(pkt(command=None,command_lines=["line1","line2","","line4"])); self.assertEqual(a.command,"line1\nline2\n\nline4")
    def test_exactly_one_command_source(self):
        with self.assertRaises(wr.PacketError): wr.extract(pkt(command="a",command_lines=["b"]))
    def test_invalid_command_lines(self):
        with self.assertRaises(wr.PacketError): wr.extract(pkt(command=None,command_lines=["ok",7]))
    def test_python_shell(self):
        a=wr.extract(pkt(shell="python",command="print(123)")); argv=wr.shell_argv(a); self.assertEqual(argv[1:4],["-X","utf8","-c"]); self.assertEqual(argv[4],"print(123)")
    def test_python_execute(self):
        a=wr.extract(pkt(shell="python",command="print(\"PYTHON_NATIVE_GREEN\")")); r=wr.execute(a); self.assertEqual(r["status"],"OK"); self.assertIn("PYTHON_NATIVE_GREEN",r["stdout"])
    def test_pwsh_accepted(self): self.assertEqual(wr.extract(pkt(shell="pwsh")).shell,"pwsh")
    def test_unknown_shell_rejected(self):
        with self.assertRaises(wr.PacketError): wr.extract(pkt(shell="bash"))
    def test_outside_text_rejected(self):
        with self.assertRaises(wr.PacketError): wr.extract("junk\n"+pkt())
    def test_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            s=wr.State(Path(d)/"s.json"); a=wr.extract(pkt()); s.reserve(a); self.assertEqual(s.lookup("t1")["status"],"INFLIGHT")
    def test_collision_hash(self):
        a=wr.extract(pkt(command="a")); b=wr.extract(pkt(command="b")); self.assertNotEqual(a.hash,b.hash)
    def test_compact_result_preserves_full_output_on_disk(self):
        with tempfile.TemporaryDirectory() as d:
            s=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt())
            raw={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","shell":a.shell,"status":"OK","exit_code":0,"cwd":str(Path(d)),"started_at":"x","finished_at":"y","duration_ms":1,"stdout":"A"*(wr.PREVIEW_OUT+50),"stderr":"B"*(wr.PREVIEW_ERR+50)}
            path=wr.save_full_result(s,raw)
            shown=wr.present_result(a,raw,path)
            self.assertTrue(shown["stdout_truncated"])
            self.assertTrue(shown["stderr_truncated"])
            self.assertEqual(shown["stdout_chars"],wr.PREVIEW_OUT+50)
            saved=json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(len(saved["stdout"]),wr.PREVIEW_OUT+50)
            self.assertEqual(len(saved["stderr"]),wr.PREVIEW_ERR+50)
    def test_full_mode_uses_legacy_network_cap(self):
        a=wr.extract(pkt(result_mode="full"))
        raw={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","shell":a.shell,"status":"OK","exit_code":0,"cwd":".","started_at":"x","finished_at":"y","duration_ms":1,"stdout":"A"*(wr.MAX_OUT+5),"stderr":""}
        shown=wr.present_result(a,raw,"C:\\full.json")
        self.assertTrue(shown["stdout_truncated"])
        self.assertEqual(shown["result_mode"],"full")
        self.assertIn("relay truncated",shown["stdout"])
    def test_duplicate_completed_action_replays_saved_result(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="replay1"))
            state.reserve(a)
            raw={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","shell":a.shell,"status":"OK","exit_code":0,"cwd":str(Path(d)),"started_at":"x","finished_at":"y","duration_ms":1,"stdout":"RECOVER_ME","stderr":""}
            saved=wr.save_full_result(state,raw)
            shown=wr.present_result(a,raw,saved)
            state.mark(a,shown)
            replay=json.loads(wr.process(pkt(id="replay1"),state).split(wr.RO+"\n",1)[1].rsplit("\n"+wr.RC,1)[0])
            self.assertEqual(replay["status"],"OK")
            self.assertTrue(replay["stdout"].endswith(wr.SANDWICH_REMINDER))
            self.assertIn("RECOVER_ME",replay["stdout"])
            self.assertTrue(replay["replayed"])

    def test_duplicate_inflight_is_retryable_without_reexecution(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="busy1"))
            state.reserve(a)
            body=json.loads(wr.process(pkt(id="busy1"),state).split(wr.RO+"\n",1)[1].rsplit("\n"+wr.RC,1)[0])
            self.assertEqual(body["status"],"DUPLICATE_INFLIGHT")

    def test_stale_inflight_becomes_interrupted_on_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            state=wr.State(path)
            a=wr.extract(pkt(id="stale1"))
            state.reserve(a)
            restarted=wr.State(path)
            self.assertEqual(restarted.lookup("stale1")["status"],"INTERRUPTED_RESTART")

    def test_result_filename_sanitizes_windows_invalid_colon(self):
        self.assertEqual(wr.safe_result_filename("job:123"),"job_123.json")

    def test_atomic_json_retries_transient_permission_error(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"atomic.json"
            real_replace=wr.os.replace
            calls={"n":0}
            def flaky(src,dst):
                calls["n"]+=1
                if calls["n"]<3: raise PermissionError("simulated transient sharing lock")
                return real_replace(src,dst)
            with mock.patch.object(wr.os,"replace",side_effect=flaky):
                wr.atomic_json(path,{"ok":True})
            self.assertEqual(calls["n"],3)
            self.assertTrue(json.loads(path.read_text(encoding="utf-8"))["ok"])

    def test_state_reserve_rolls_back_memory_when_persistence_fails(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="rollback-reserve"))
            with mock.patch.object(state,"save",side_effect=PermissionError("locked")):
                with self.assertRaises(PermissionError): state.reserve(a)
            self.assertIsNone(state.lookup(a.id))

    def test_state_mark_rolls_back_memory_when_persistence_fails(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="rollback-mark")); state.reserve(a)
            before=dict(state.lookup(a.id))
            result={"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"x.json"}
            with mock.patch.object(state,"save",side_effect=PermissionError("locked")):
                with self.assertRaises(PermissionError): state.mark(a,result)
            self.assertEqual(state.lookup(a.id),before)


    def test_every_serialized_result_stdout_ends_with_sandwich_reminder(self):
        body=json.loads(wr.result({"status":"OK","stdout":"hello"}).split(wr.RO+"\n",1)[1].rsplit("\n"+wr.RC,1)[0])
        self.assertEqual(body["stdout"],"hello\n"+wr.SANDWICH_REMINDER)
        empty=json.loads(wr.result({"status":"COMMAND_FAILED","stdout":""}).split(wr.RO+"\n",1)[1].rsplit("\n"+wr.RC,1)[0])
        self.assertEqual(empty["stdout"],wr.SANDWICH_REMINDER)
        already=json.loads(wr.result({"status":"OK","stdout":wr.SANDWICH_REMINDER}).split(wr.RO+"\n",1)[1].rsplit("\n"+wr.RC,1)[0])
        self.assertEqual(already["stdout"],wr.SANDWICH_REMINDER)

    def test_result_attachment_descriptor_is_extracted(self):
        out=json.dumps({"ok":True,"chatgpt_attachment":{"kind":"image","name":"screenshot-20261003T091921-123456789.png","mime":"image/png"}})
        self.assertEqual(wr.result_attachments(out)[0]["name"],"screenshot-20261003T091921-123456789.png")

    def test_managed_screenshot_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            with self.assertRaises(wr.RelayError): wr.managed_screenshot_path(state,"../secret.png",False)


    def test_mark_atomically_creates_passive_outbound_ready_entry(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="outbound-ready",result_mode="full")); state.reserve(a)
            raw={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","shell":a.shell,"status":"OK","exit_code":0,"cwd":str(Path(d)),"started_at":"x","finished_at":"y","duration_ms":1,"stdout":"READY","stderr":""}
            saved=wr.save_full_result(state,raw)
            state.mark(a,wr.present_result(a,raw,saved))
            entry=state.outbound_lookup(a.id)
            self.assertEqual(entry["id"],a.id)
            self.assertEqual(entry["payload_hash"],a.hash)
            self.assertEqual(entry["saved_result_path"],saved)
            self.assertEqual(entry["result_mode"],"full")
            self.assertEqual(entry["phase"],"READY")
            self.assertEqual(entry["created_at"],entry["updated_at"])

    def test_outbound_ready_survives_restart_and_inflight_does_not_gain_ready(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"; state=wr.State(path)
            ready=wr.extract(pkt(id="ready-restart")); state.reserve(ready)
            raw={"version":1,"platform":"windows","id":ready.id,"session":ready.session,"action":"EXEC","shell":ready.shell,"status":"OK","exit_code":0,"cwd":str(Path(d)),"started_at":"x","finished_at":"y","duration_ms":1,"stdout":"READY","stderr":""}
            saved=wr.save_full_result(state,raw)
            state.mark(ready,wr.present_result(ready,raw,saved))
            stale=wr.extract(pkt(id="stale-no-ready")); state.reserve(stale)
            before=state.outbound_lookup(ready.id)
            restarted=wr.State(path)
            self.assertEqual(restarted.outbound_lookup(ready.id),before)
            self.assertIsNone(restarted.outbound_lookup(stale.id))
            self.assertEqual(restarted.lookup(stale.id)["status"],"INTERRUPTED_RESTART")

    def test_completed_replay_does_not_duplicate_or_reset_outbound_ready(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="ready-replay")); state.reserve(a)
            raw={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","shell":a.shell,"status":"OK","exit_code":0,"cwd":str(Path(d)),"started_at":"x","finished_at":"y","duration_ms":1,"stdout":"ONCE","stderr":""}
            saved=wr.save_full_result(state,raw)
            state.mark(a,wr.present_result(a,raw,saved))
            before=state.outbound_lookup(a.id)
            replay=wr.process(pkt(id="ready-replay"),state)
            self.assertIn('"replayed": true',replay)
            self.assertEqual(state.outbound_lookup(a.id),before)

    def test_mark_rollback_removes_outbound_ready_when_persistence_fails(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="rollback-outbound")); state.reserve(a)
            before=dict(state.lookup(a.id))
            result={"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"x.json"}
            with mock.patch.object(state,"save",side_effect=PermissionError("locked")):
                with self.assertRaises(PermissionError): state.mark(a,result)
            self.assertEqual(state.lookup(a.id),before)
            self.assertIsNone(state.outbound_lookup(a.id))

    def test_nonterminal_outbound_delivery_protects_processed_record_from_pruning(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            state.data["processed"]={"protected":{"payload_hash":"h","session":"default","status":"OK"}}
            for i in range(499): state.data["processed"][f"old-{i}"]={"payload_hash":str(i),"session":"default","status":"OK"}
            state.data["outbound_deliveries"]={"protected":{"id":"protected","payload_hash":"h","phase":"READY"}}
            state.save()
            a=wr.extract(pkt(id="new-ready")); state.reserve(a)
            state.mark(a,{"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"new.json"})
            self.assertIn("protected",state.data["processed"])
            self.assertEqual(state.outbound_lookup("protected")["phase"],"READY")
            self.assertLessEqual(len(state.data["processed"]),500)


    def test_outbound_owner_defaults_browser_and_persists_valid_windows_value(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            state=wr.State(path)
            self.assertEqual(state.outbound_owner,"browser")
            state.data["outbound_owner"]="windows"
            state.save()
            restarted=wr.State(path)
            self.assertEqual(restarted.outbound_owner,"windows")

    def test_invalid_outbound_owner_fails_closed_on_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            state=wr.State(path)
            state.data["outbound_owner"]="invalid-owner"
            state.save()
            with self.assertRaises(wr.RelayError):
                wr.State(path)


    def test_materialized_outbound_wire_matches_normal_result_exactly(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="wire-materialize",result_mode="full")); state.reserve(a)
            raw={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","shell":a.shell,"status":"OK","exit_code":0,"cwd":str(Path(d)),"started_at":"x","finished_at":"y","duration_ms":1,"stdout":"HELLO","stderr":""}
            saved=wr.save_full_result(state,raw)
            presented=wr.present_result(a,raw,saved)
            state.mark(a,presented)
            info=wr.materialize_outbound_result_file(state,a.id)
            actual=Path(info["result_file"]).read_text(encoding="utf-8")
            self.assertEqual(actual,wr.result(presented))
            self.assertEqual(info["text_chars"],len(actual))
            self.assertEqual(info["attachments"],[])

    def test_claim_requires_windows_owner_armed_and_attachment_safe(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="claim-guards")); state.reserve(a)
            state.mark(a,{"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"x.json"})
            with self.assertRaises(wr.RelayError): state.claim_outbound_delivery(a.id)
            state.data["outbound_owner"]="windows"; state.save()
            state.set_armed(False)
            with self.assertRaises(wr.RelayError): state.claim_outbound_delivery(a.id)
            state.set_armed(True)
            state.data["outbound_deliveries"][a.id]["has_attachments"]=True; state.save()
            with self.assertRaises(wr.RelayError): state.claim_outbound_delivery(a.id)
            state.data["outbound_deliveries"][a.id].pop("has_attachments",None); state.save()
            with self.assertRaises(wr.RelayError): state.claim_outbound_delivery(a.id)

    def test_claim_and_retry_transition_through_durable_submitting(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json"); state.data["outbound_owner"]="windows"; state.save()
            a=wr.extract(pkt(id="claim-retry")); state.reserve(a)
            state.mark(a,{"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"x.json"})
            first=state.claim_outbound_delivery(a.id)
            self.assertEqual(first["phase"],"SUBMITTING"); self.assertEqual(first["attempt_count"],1)
            failed=state.finish_outbound_delivery(a.id,"PRE_SUBMIT_FAILED")
            self.assertEqual(failed["phase"],"PRE_SUBMIT_FAILED")
            second=state.claim_outbound_delivery(a.id)
            self.assertEqual(second["phase"],"SUBMITTING"); self.assertEqual(second["attempt_count"],2)
            done=state.finish_outbound_delivery(a.id,"SUBMITTED")
            self.assertEqual(done["phase"],"SUBMITTED")
            with self.assertRaises(wr.RelayError): state.claim_outbound_delivery(a.id)

    def test_submitting_restart_becomes_terminal_submit_uncertain(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"; state=wr.State(path)
            state.data["outbound_owner"]="windows"; state.save()
            a=wr.extract(pkt(id="restart-uncertain")); state.reserve(a)
            state.mark(a,{"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"x.json"})
            state.claim_outbound_delivery(a.id)
            restarted=wr.State(path)
            delivery=restarted.outbound_lookup(a.id)
            self.assertEqual(delivery["phase"],"SUBMIT_UNCERTAIN")
            self.assertEqual(delivery["restart_recovery"],"interrupted_while_submitting")
            with self.assertRaises(wr.RelayError): restarted.claim_outbound_delivery(a.id)

    def test_claim_and_finish_persistence_failures_roll_back_phase(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json"); state.data["outbound_owner"]="windows"; state.save()
            a=wr.extract(pkt(id="sender-rollback")); state.reserve(a)
            state.mark(a,{"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"x.json"})
            with mock.patch.object(state,"save",side_effect=PermissionError("locked")):
                with self.assertRaises(PermissionError): state.claim_outbound_delivery(a.id)
            self.assertEqual(state.outbound_lookup(a.id)["phase"],"READY")
            state.claim_outbound_delivery(a.id)
            with mock.patch.object(state,"save",side_effect=PermissionError("locked")):
                with self.assertRaises(PermissionError): state.finish_outbound_delivery(a.id,"SUBMIT_UNCERTAIN")
            self.assertEqual(state.outbound_lookup(a.id)["phase"],"SUBMITTING")

    def test_mark_records_attachment_safety_for_windows_claiming(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="attachment-flag")); state.reserve(a)
            state.mark(a,{"status":"OK","exit_code":0,"finished_at":"x","saved_result_path":"x.json","attachments":[{"kind":"image","name":"example.png","mime":"image/png"}]})
            self.assertTrue(state.outbound_lookup(a.id)["has_attachments"])


    def test_process_returns_exact_persisted_wire_file(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            packet=pkt(id="wire-process-exact",result_mode="full")
            a=wr.extract(packet)
            raw={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","shell":a.shell,"status":"OK","exit_code":0,"cwd":str(Path(d)),"started_at":"x","finished_at":"y","duration_ms":1,"stdout":"ORDERED","stderr":""}
            with mock.patch.object(wr,"execute",return_value=raw):
                returned=wr.process(packet,state)
            delivery=state.outbound_lookup(a.id)
            wire_path=Path(delivery["wire_result_path"])
            self.assertEqual(delivery["phase"],"READY")
            self.assertFalse(delivery["has_attachments"])
            self.assertEqual(returned,wire_path.read_text(encoding="utf-8"))
            self.assertEqual(wr.outbound_result_file(state,a.id),str(wire_path.resolve()))
            self.assertEqual(returned,wr.read_outbound_wire_result(state,a.id))

    def test_wire_persistence_failure_prevents_ready_completion(self):
        with tempfile.TemporaryDirectory() as d:
            state=wr.State(Path(d)/"state.json")
            a=wr.extract(pkt(id="wire-before-ready")); state.reserve(a)
            presented={"version":1,"platform":"windows","id":a.id,"session":a.session,"action":"EXEC","status":"OK","exit_code":0,"finished_at":"x","stdout":"X","stderr":"","saved_result_path":"x.json"}
            with mock.patch.object(wr,"save_outbound_wire_result",side_effect=PermissionError("locked")):
                with self.assertRaises(PermissionError): state.mark(a,presented)
            self.assertIsNone(state.outbound_lookup(a.id))
            self.assertEqual(state.lookup(a.id)["status"],"INFLIGHT")

if __name__=="__main__": unittest.main()
