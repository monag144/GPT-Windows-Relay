"""PCE14 executable benchmark contracts: measurable sequences, not source-string checks."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import relay_behavioral as rb  # noqa: E402

SHA = "a" * 64
GIT = "b" * 40


def metadata(mode="fixture"):
    return {
        "schema": "pce14-relay-run-v1",
        "run_id": "fixture-test-001" if mode == "fixture" else "live-test-001",
        "mode": mode,
        "source_sha": GIT,
        "loaded_runtime_sha256": SHA if mode == "live" else None,
        "catalog_sha256": rb.digest(rb.CATALOG),
        "observer_id": "independent-observer-01",
        "observer_independent": mode == "live",
        "isolated_profile": mode == "live",
    }


def event(case_id, trial_id, marker, index, mode="fixture"):
    source, name = marker.split(":", 1)
    item = {
        "case_id": case_id,
        "trial_id": trial_id,
        "operation_id": "OP-" + trial_id,
        "tab_id": "tab-87",
        "payload_sha256": SHA,
        "source": source,
        "event": name,
        "at_ms": index * 100,
    }
    if source == "observer":
        item["observer_id"] = "independent-observer-01"
    if marker == "observer:user_turn_verified":
        item["role"] = "user"
        item["conversation_id"] = "conversation-209"
    if marker == "observer:loaded_runtime_attested":
        item["runtime_sha256"] = SHA
    return item


def trial(case, number=0, mode="fixture"):
    trial_id = case["id"] + "-" + str(number)
    markers = ["relay:trial_started"] + case["required"][:]
    if case["effects"] and "relay:effect_committed" not in markers:
        markers.insert(1, "relay:effect_committed")
    if case["sends"] and "relay:send_invoked" not in markers:
        markers.insert(1, "relay:send_invoked")
    markers.append("observer:trial_complete")
    return [event(case["id"], trial_id, marker, i, mode) for i, marker in enumerate(markers)]


class BehavioralBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = rb.load_catalog()
        cls.cases = {c["id"]: c for c in cls.catalog["cases"]}

    def test_complete_fixture_matrix_is_not_misrepresented_as_live(self):
        events = [e for c in self.cases.values() for j in range(3) for e in trial(c, j)]
        result = rb.score(metadata(), self.catalog, events)
        self.assertEqual(result["counts"]["passing"], 20)
        self.assertEqual(result["counts"]["failed"], 0)
        self.assertEqual(result["counts"]["blocked"], 0)
        self.assertFalse(result["full_behavioral_gate"])
        self.assertFalse(result["release_qualified"])
        self.assertTrue(all(v["status"] == "FIXTURE_PASS" for v in result["capabilities"].values()))

    def test_unexecuted_cases_not_marked_pass(self):
        result = rb.score(metadata(), self.catalog, [])
        self.assertEqual(result["counts"]["not_run"], 20)
        self.assertFalse(result["full_behavioral_gate"])

    def test_single_trial_does_not_qualify(self):
        case = self.cases["R06"]
        outcome = rb.score(metadata(), self.catalog, trial(case))
        self.assertEqual(outcome["capabilities"]["R06"]["status"], "BLOCKED")

    def test_fake_assistant_quote_is_not_user_turn(self):
        seq = trial(self.cases["R07"])
        next(e for e in seq if e["event"] == "user_turn_verified")["role"] = "assistant"
        outcome = rb.check_trial(self.cases["R07"], seq, metadata(), self.catalog["forbidden_global"])
        self.assertEqual(outcome["status"], "FAIL")
        self.assertIn("user-role", outcome["reason"])

    def test_stale_or_wrong_payload_is_refused(self):
        seq = trial(self.cases["R06"])
        next(e for e in seq if e["event"] == "user_turn_verified")["payload_sha256"] = "d" * 64
        outcome = rb.check_trial(self.cases["R06"], seq, metadata(), self.catalog["forbidden_global"])
        self.assertEqual(outcome["status"], "FAIL")

    def test_duplicate_send_is_refused(self):
        seq = trial(self.cases["R06"])
        duplicate = event("R06", "R06-0", "relay:send_invoked", len(seq) - 1)
        duplicate["at_ms"] = seq[-2]["at_ms"] + 1
        seq.insert(-1, duplicate)
        self.assertEqual(rb.check_trial(self.cases["R06"], seq, metadata(), self.catalog["forbidden_global"])["status"], "FAIL")

    def test_replayed_backend_effect_is_refused(self):
        seq = trial(self.cases["R12"])
        dup = event("R12", "R12-0", "relay:effect_replayed", len(seq) - 1)
        dup["at_ms"] = seq[-2]["at_ms"] + 1
        seq.insert(-1, dup)
        self.assertEqual(rb.check_trial(self.cases["R12"], seq, metadata(), self.catalog["forbidden_global"])["status"], "FAIL")

    def test_stop_case_refuses_send_even_with_completion(self):
        seq = trial(self.cases["R11"])
        surprise = event("R11", "R11-0", "relay:send_invoked", len(seq) - 1)
        surprise["at_ms"] = seq[-2]["at_ms"] + 1
        seq.insert(-1, surprise)
        outcome = rb.check_trial(self.cases["R11"], seq, metadata(), self.catalog["forbidden_global"])
        self.assertEqual(outcome["status"], "FAIL")

    def test_incomplete_trial_is_blocked_not_success(self):
        seq = trial(self.cases["R03"])[:-1]
        self.assertEqual(rb.check_trial(self.cases["R03"], seq, metadata(), self.catalog["forbidden_global"])["status"], "BLOCKED")

    def test_missing_step_is_failure_not_skipped_success(self):
        seq = [e for e in trial(self.cases["R04"]) if e["event"] != "composer_exact"]
        self.assertEqual(rb.check_trial(self.cases["R04"], seq, metadata(), self.catalog["forbidden_global"])["status"], "FAIL")

    def test_wrong_tab_is_failure_even_if_sender_claims_success(self):
        seq = trial(self.cases["R03"])
        seq[2]["tab_id"] = "other-tab"
        self.assertEqual(rb.check_trial(self.cases["R03"], seq, metadata(), self.catalog["forbidden_global"])["status"], "FAIL")

    def test_deadline_is_checked(self):
        seq = trial(self.cases["R04"])
        seq[-1]["at_ms"] = 20000
        result = rb.check_trial(self.cases["R04"], seq, metadata(), self.catalog["forbidden_global"])
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("latency", result["reason"])

    def test_runtime_hash_disagreement_blocks_provenance(self):
        seq = trial(self.cases["R17"], mode="live")
        next(e for e in seq if e["event"] == "loaded_runtime_attested")["runtime_sha256"] = "e" * 64
        self.assertEqual(rb.check_trial(self.cases["R17"], seq, metadata("live"), self.catalog["forbidden_global"])["status"], "FAIL")

    def test_live_requires_positive_runtime_evidence(self):
        events = [e for c in self.cases.values() if c["id"] != "R17" for e in trial(c, mode="live")]
        with self.assertRaisesRegex(ValueError, "loaded-runtime"):
            rb.score(metadata("live"), self.catalog, events)

    def test_live_not_valid_without_isolated_independent_observer(self):
        info = metadata("live")
        info["observer_independent"] = False
        with self.assertRaisesRegex(ValueError, "independent observer"):
            rb.validate_manifest(info)
        info = metadata("live")
        info["isolated_profile"] = False
        with self.assertRaisesRegex(ValueError, "isolated"):
            rb.validate_manifest(info)

    def test_trace_rejects_raw_clipboard_or_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "trace.jsonl"
            leaked = trial(self.cases["R04"])[0]
            leaked["clipboard_text"] = "should never enter benchmark logs"
            p.write_text(json.dumps(leaked) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "raw-content"):
                rb.load_events(p)

    def test_evidence_cannot_mix_two_trial_ids_for_same_case(self):
        seq = trial(self.cases["R02"])
        seq[2]["operation_id"] = "another-operation"
        self.assertEqual(rb.check_trial(self.cases["R02"], seq, metadata(), self.catalog["forbidden_global"])["status"], "FAIL")

    def test_three_successful_live_traces_do_not_certify_release(self):
        traces = [e for c in self.cases.values() for i in range(3) for e in trial(c, i, "live")]
        result = rb.score(metadata("live"), self.catalog, traces)
        self.assertEqual(result["counts"]["passing"], 20)
        self.assertTrue(result["full_behavioral_gate"])
        self.assertFalse(result["release_qualified"])

    def test_output_is_write_once_and_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            rb.write_once(path, {"ok": True})
            self.assertTrue(path.is_file())
            with self.assertRaises(FileExistsError):
                rb.write_once(path, {"ok": False})
            self.assertEqual(rb.load_json(path), {"ok": True})

    def test_report_is_machine_readable_and_cli_fails_on_missing_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            m, t, out = (root / f for f in ("manifest.json", "trace.jsonl", "out.json"))
            m.write_text(json.dumps(metadata()), encoding="utf-8")
            t.write_text("", encoding="utf-8")
            rc = rb.main(["--manifest", str(m), "--trace", str(t), "--output", str(out)])
            self.assertEqual(rc, 2)
            self.assertEqual(rb.load_json(out)["counts"]["not_run"], 20)


if __name__ == "__main__":
    unittest.main()
