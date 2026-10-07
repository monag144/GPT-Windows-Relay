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
import job_application_preview_v2 as preview
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
        "phone":"555-0199",
        "responsibilities":"Secret responsibilities.",
        "salary":"Secret salary",
        "supervisor":"Secret supervisor",
        "supervisor_note":"",
    }]
    return p


def base_manifest():
    return {
        "schema_version":1,
        "application_id":"preview-REQ1",
        "job":{"title":"Target Job","employer":"Example Employer","requisition_id":"REQ1"},
        "browser_target":{"tab_name":"Target Job"},
        "context":{"auto_bind_repeating_sections":True},
    }


def repeating_state():
    return engine.PageState.from_obj({"controls":[
        {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
        {"type":"ControlType.Edit","name":"Company","value":"","required":True,
         "group_path":["Work Experience 1","My Experience"],"enabled":True,"offscreen":False},
        {"type":"ControlType.Edit","name":"Job Title","value":"","required":True,
         "group_path":["Work Experience 1","My Experience"],"enabled":True,"offscreen":False},
        {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
    ]})


class PreviewV2Tests(unittest.TestCase):
    def test_preview_redacts_profile_backed_action_values(self):
        normalized=manifests.validate_manifest(base_manifest(),profile())
        out=preview.compile_preview(profile(),repeating_state(),normalized,browser_restored=True)
        rendered=json.dumps(out,ensure_ascii=False)
        self.assertEqual(out["plan"]["status"],"act")
        self.assertGreaterEqual(out["plan"]["action_count"],2)
        self.assertTrue(out["plan"]["first_action"]["configured_value_omitted"])
        self.assertNotIn("Secret Employer",rendered)
        self.assertNotIn("Secret Driver",rendered)
        self.assertNotIn("555-0199",rendered)
        self.assertNotIn("Secret responsibilities",rendered)
        self.assertIn("profile.experience[0].employer",rendered)

    def test_preview_redacts_configured_choice_answer(self):
        raw=base_manifest()
        raw["context"]["choice_answers"]={"Are you willing to travel?":"Yes"}
        state=engine.PageState.from_obj({"controls":[
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.RadioButton","name":"Yes","selected":False,
             "group_path":["Are you willing to travel?","Application Questions"],"enabled":True,"offscreen":False},
            {"type":"ControlType.RadioButton","name":"No","selected":False,
             "group_path":["Are you willing to travel?","Application Questions"],"enabled":True,"offscreen":False},
        ]})
        normalized=manifests.validate_manifest(raw,profile())
        out=preview.compile_preview(profile(),state,normalized,browser_restored=True)
        action=out["plan"]["first_action"]
        self.assertEqual(action["op"],"select_choice")
        self.assertEqual(action["target"]["group_name"],"Are you willing to travel?")
        self.assertEqual(action["target"]["name"],"[configured option omitted]")
        self.assertNotIn('"Yes"',json.dumps(out,ensure_ascii=False))

    def test_preview_redacts_upload_path_and_filename_from_action(self):
        with tempfile.TemporaryDirectory() as td:
            secret=Path(td)/"PrivateFirst_PrivateLast_resume.pdf"
            secret.write_bytes(b"%PDF-test")
            raw=base_manifest()
            raw["context"]["attachments"]=[{
                "path":str(secret),
                "expected_filename":secret.name,
                "target":{"name":"Select Files"},
                "success_text":"Successfully Uploaded!",
            }]
            state=engine.PageState.from_obj({"controls":[
                {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
                {"type":"ControlType.Button","name":"Select Files","enabled":True,"offscreen":False},
            ]})
            normalized=manifests.validate_manifest(raw,profile(),check_files=True)
            out=preview.compile_preview(profile(),state,normalized,browser_restored=True)
            rendered=json.dumps(out,ensure_ascii=False)
        self.assertEqual(out["plan"]["first_action"]["op"],"upload_file")
        self.assertNotIn(str(secret),rendered)
        self.assertNotIn(secret.name,rendered)

    def test_preview_review_mismatch_reports_count_not_expected_value(self):
        raw=base_manifest()
        raw["context"]["review_expectations"]=[{
            "kind":"contains_text",
            "value":"Secret Employer",
        }]
        state=engine.PageState.from_obj({"controls":[
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        ]})
        normalized=manifests.validate_manifest(raw,profile())
        out=preview.compile_preview(profile(),state,normalized,browser_restored=True)
        rendered=json.dumps(out,ensure_ascii=False)
        self.assertEqual(out["plan"]["status"],"blocked")
        self.assertEqual(out["plan"]["blockers"]["review_mismatch_count"],1)
        self.assertNotIn("Secret Employer",rendered)

    def test_preview_public_listing_surfaces_entrypoint_without_inventing_action(self):
        normalized=manifests.validate_manifest(base_manifest(),profile())
        state=engine.PageState.from_obj({"controls":[
            {"type":"ControlType.Button","name":"Apply","enabled":True,"offscreen":False},
            {"type":"ControlType.Text","name":"Target Job"},
        ]})
        out=preview.compile_preview(profile(),state,normalized,browser_restored=True)
        self.assertEqual(out["page"]["entrypoint_buttons"],["Apply"])
        self.assertEqual(out["plan"]["status"],"blocked")
        self.assertEqual(out["plan"]["action_count"],0)
        self.assertEqual(out["plan"]["reason"],"no safe action identified")

    def test_preview_emits_validated_live_run_binding(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=profile()
            profile_path=root/"profile.json"
            profile_path.write_text(json.dumps(p,ensure_ascii=False),encoding="utf-8")
            manifest_path=root/"application.json"
            manifest_path.write_text(json.dumps(base_manifest(),ensure_ascii=False),encoding="utf-8")
            normalized=manifests.validate_manifest(base_manifest(),p,check_files=True)
            expected=manifests.manifest_fingerprint(normalized)
            with patch.object(
                preview.discovery,
                "capture_live_state",
                return_value=repeating_state(),
            ) as capture:
                out=preview.preview_from_files(
                    str(profile_path),
                    str(manifest_path),
                    runtime_id="42.77",
                )
        self.assertEqual(
            out["live_run_binding"],
            {
                "runtime_id":"42.77",
                "expected_manifest_fingerprint":expected,
            },
        )
        capture.assert_called_once_with(normalized,runtime_id="42.77")

    def test_runner_preview_cli_is_read_only_and_session_free(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=profile()
            profile_path=root/"profile.json"
            profile_path.write_text(json.dumps(p,ensure_ascii=False),encoding="utf-8")
            manifest_path=root/"application.json"
            manifest_path.write_text(json.dumps(base_manifest(),ensure_ascii=False),encoding="utf-8")
            output=io.StringIO()
            with patch.object(preview.discovery,"capture_live_state",return_value=repeating_state()) as capture, \
                 patch.object(runner.provider,"execute") as execute, \
                 patch.object(runner.sessions,"load") as session_load, \
                 patch.object(runner.sessions,"save") as session_save, \
                 redirect_stdout(output):
                exit_code=runner.main([
                    "preview",
                    "--profile",str(profile_path),
                    "--manifest",str(manifest_path),
                    "--runtime-id","42.77",
                ])
        self.assertEqual(exit_code,0)
        out=json.loads(output.getvalue())
        self.assertFalse(out["mutation_executed"])
        self.assertFalse(out["session_touched"])
        capture.assert_called_once_with(
            manifests.validate_manifest(base_manifest(),p,check_files=True),
            runtime_id="42.77",
        )
        execute.assert_not_called()
        session_load.assert_not_called()
        session_save.assert_not_called()


if __name__=="__main__":
    unittest.main()
