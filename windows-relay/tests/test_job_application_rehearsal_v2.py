#!/usr/bin/env python3
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import job_application_engine_v2 as engine
import job_application_manifest_v2 as manifests
import job_application_rehearsal_v2 as rehearsal
import job_application_runner_v2 as runner
import resume_profile


def profile():
    p=resume_profile.empty_profile()
    p["identity"]["first_name"]="PrivateFirst"
    p["identity"]["last_name"]="PrivateLast"
    p["experience"]=[{
        "employer":"Secret Employer",
        "title":"Secret Driver",
        "start":"2025-01",
        "end":None,
        "current":True,
        "may_contact":True,
        "phone":"",
        "responsibilities":"",
        "salary":"",
        "supervisor":"",
        "supervisor_note":"",
    }]
    return p


def manifest():
    return {
        "schema_version":1,
        "application_id":"rehearsal-REQ1",
        "job":{"title":"Target Job","employer":"Example Employer","requisition_id":"REQ1"},
        "browser_target":{"tab_name":"Target Job"},
        "context":{"auto_bind_repeating_sections":True},
    }


def repeating_state():
    return engine.PageState.from_obj({"controls":[
        {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
        {"type":"ControlType.Edit","id":"company-A","name":"Company","value":"","required":True,
         "group_path":["Work Experience 1","My Experience"],"enabled":True,"offscreen":False},
        {"type":"ControlType.Edit","id":"title-A","name":"Job Title","value":"","required":True,
         "group_path":["Work Experience 1","My Experience"],"enabled":True,"offscreen":False},
        {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
    ]})


class RehearsalV2Tests(unittest.TestCase):
    def test_action_fingerprint_is_canonical_and_value_sensitive(self):
        a={
            "op":"set_text",
            "target":{"name":"Company","automation_id":"company-A"},
            "value":"Secret Employer",
            "verify":{"kind":"value_equals","value":"Secret Employer"},
        }
        b={
            "value":"Secret Employer",
            "verify":{"value":"Secret Employer","kind":"value_equals"},
            "target":{"automation_id":"company-A","name":"Company"},
            "op":"set_text",
        }
        changed={**a,"value":"Different"}
        self.assertEqual(rehearsal.action_fingerprint(a),rehearsal.action_fingerprint(b))
        self.assertNotEqual(rehearsal.action_fingerprint(a),rehearsal.action_fingerprint(changed))

    def test_compile_rehearsal_redacts_value_and_fingerprints_exact_first_mutation(self):
        normalized=manifests.validate_manifest(manifest(),profile())
        out=rehearsal.compile_rehearsal(
            profile(),repeating_state(),normalized,browser_restored=True
        )
        rendered=json.dumps(out,ensure_ascii=False)
        self.assertTrue(out["ready_for_first_mutation"])
        self.assertEqual(out["rehearsal_status"],"ready")
        self.assertEqual(out["first_mutation"]["action"]["op"],"set_text")
        self.assertEqual(out["first_mutation"]["target_match_count"],1)
        self.assertTrue(out["first_mutation"]["verifier_present"])
        self.assertEqual(len(out["first_mutation"]["fingerprint"]),64)
        self.assertNotIn("Secret Employer",rendered)
        self.assertNotIn("Secret Driver",rendered)

    def test_public_listing_entrypoint_is_fingerprint_bound_first_mutation(self):
        raw=manifest()
        raw["context"]={
            "entrypoint":{
                "target":{"control_type":"ControlType.Button","name":"Apply"},
                "verify":{"kind":"control_absent","name":"Apply"},
            }
        }
        normalized=manifests.validate_manifest(raw,profile())
        state=engine.PageState.from_obj({"controls":[
            {"type":"ControlType.Button","name":"Apply","enabled":True,"offscreen":False},
            {"type":"ControlType.Button","name":"Sign In","enabled":True,"offscreen":False},
        ]})
        out=rehearsal.compile_rehearsal(
            profile(),state,normalized,browser_restored=True
        )
        self.assertTrue(out["ready_for_first_mutation"])
        self.assertEqual(out["first_mutation"]["action"]["op"],"invoke")
        self.assertEqual(out["first_mutation"]["action"]["target"]["name"],"Apply")
        self.assertEqual(len(out["first_mutation"]["fingerprint"]),64)
        expected=engine.plan(profile(),state,engine.EnginePolicy(),normalized["context"])["actions"][0]
        self.assertEqual(
            out["first_mutation"]["fingerprint"],
            rehearsal.action_fingerprint(expected),
        )

    def test_selector_probe_is_not_mislabeled_as_mutation_ready(self):
        raw=manifest()
        raw["context"]={}
        normalized=manifests.validate_manifest(raw,profile())
        state=engine.PageState.from_obj({"controls":[
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule-A","name":"Schedule","value":"",
             "group_path":["Availability","Application Questions"],"enabled":True,"offscreen":False},
        ]})
        out=rehearsal.compile_rehearsal(profile(),state,normalized,browser_restored=True)
        self.assertFalse(out["ready_for_first_mutation"])
        self.assertEqual(out["rehearsal_status"],"read_only_probe_required")
        self.assertIsNone(out["first_mutation"])
        self.assertEqual(out["read_only_action"]["op"],"inspect_options")

    def test_rehearse_from_files_emits_three_part_live_run_binding(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=profile()
            profile_path=root/"profile.json"
            profile_path.write_text(json.dumps(p),encoding="utf-8")
            manifest_path=root/"manifest.json"
            manifest_path.write_text(json.dumps(manifest()),encoding="utf-8")
            normalized=manifests.validate_manifest(manifest(),p,check_files=True)
            expected_manifest=manifests.manifest_fingerprint(normalized)
            with patch.object(
                rehearsal.discovery,"validate_runtime_target",
                return_value={"runtime_id":"42.77","name":"Target Job"},
            ) as validate, patch.object(
                rehearsal.discovery,"capture_live_state",
                return_value=repeating_state(),
            ) as capture:
                out=rehearsal.rehearse_from_files(
                    str(profile_path),str(manifest_path),runtime_id="42.77"
                )
        self.assertTrue(out["ready_for_first_mutation"])
        self.assertEqual(out["live_run_binding"]["runtime_id"],"42.77")
        self.assertEqual(
            out["live_run_binding"]["expected_manifest_fingerprint"],
            expected_manifest,
        )
        self.assertEqual(
            out["live_run_binding"]["expected_first_mutation_fingerprint"],
            out["first_mutation"]["fingerprint"],
        )
        validate.assert_called_once_with({"tab_name":"Target Job"},"42.77")
        capture.assert_called_once_with(normalized,runtime_id="42.77")

    def test_runner_rehearse_cli_is_session_free_and_does_not_execute_provider_action(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=profile()
            profile_path=root/"profile.json"
            profile_path.write_text(json.dumps(p),encoding="utf-8")
            manifest_path=root/"manifest.json"
            manifest_path.write_text(json.dumps(manifest()),encoding="utf-8")
            output=io.StringIO()
            with patch.object(
                rehearsal.discovery,"validate_runtime_target",
                return_value={"runtime_id":"42.77","name":"Target Job"},
            ), patch.object(
                rehearsal.discovery,"capture_live_state",
                return_value=repeating_state(),
            ), patch.object(runner.provider,"execute") as execute, \
                 patch.object(runner.sessions,"load") as session_load, \
                 patch.object(runner.sessions,"save") as session_save, \
                 redirect_stdout(output):
                exit_code=runner.main([
                    "rehearse",
                    "--profile",str(profile_path),
                    "--manifest",str(manifest_path),
                    "--runtime-id","42.77",
                ])
        self.assertEqual(exit_code,0)
        out=json.loads(output.getvalue())
        self.assertTrue(out["ready_for_first_mutation"])
        self.assertFalse(out["mutation_executed"])
        self.assertFalse(out["session_touched"])
        execute.assert_not_called()
        session_load.assert_not_called()
        session_save.assert_not_called()


if __name__=="__main__":
    unittest.main()
