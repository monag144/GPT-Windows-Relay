#!/usr/bin/env python3
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import job_application_intake_v2 as intake
import job_application_manifest_v2 as manifests
import job_application_runner_v2 as runner
import resume_profile


def profile():
    p=resume_profile.empty_profile()
    p["identity"]["first_name"]="Jack"
    p["identity"]["last_name"]="Monaghan"
    p["experience"]=[
        {
            "employer":"Employer A",
            "title":"Driver A",
            "start":"2025-01",
            "end":None,
            "current":True,
            "may_contact":True,
            "phone":"",
            "responsibilities":"Delivered freight.",
            "salary":"",
            "supervisor":"",
            "supervisor_note":"",
        },
        {
            "employer":"Employer B",
            "title":"Driver B",
            "start":"2024-01",
            "end":"2024-12",
            "current":False,
            "may_contact":True,
            "phone":"555-0100",
            "responsibilities":"",
            "salary":"",
            "supervisor":"",
            "supervisor_note":"",
        },
    ]
    return p


def manifest(resume_path: str):
    return {
        "schema_version":1,
        "application_id":"example-REQ1",
        "job":{"title":"Road Role","employer":"Example Employer","requisition_id":"REQ1"},
        "browser_target":{"tab_name":"Road Role"},
        "context":{
            "source_path":["Website","Employer Site"],
            "auto_bind_repeating_sections":True,
            "repeating_section_goals":[{"source":"experience","desired_count":2}],
            "record_overrides":{
                "experience":{"0":{"reason_for_leaving":"Accepted another position."}}
            },
            "choice_answers":{"Are you willing to travel?":"Yes"},
            "option_selections":[{
                "target":{"control_type":"ControlType.ComboBox","name":"Schedule"},
                "value":"Night",
            }],
            "attachments":[{
                "path":resume_path,
                "expected_filename":Path(resume_path).name,
                "target":{"name":"Select Files"},
                "success_text":"Successfully Uploaded!",
            }],
            "review_expectations":[{
                "kind":"contains_text",
                "value":"Example Employer",
            }],
        },
    }


class IntakeV2Tests(unittest.TestCase):
    def test_readiness_reports_entrypoint_contract_without_authorization(self):
        p=profile()
        m=manifest(r"C:\\tmp\\resume.pdf")
        m["context"]["entrypoint"]={
            "target":{"control_type":"ControlType.Button","name":"Apply"},
            "verify":{"kind":"control_absent","name":"Apply"},
        }
        out=intake.compile_readiness(m,p,check_files=False)
        self.assertTrue(out["manifest_contracts"]["entrypoint_configured"])
        self.assertIn(
            "manifest-bound public-listing entrypoint transition",
            out["live_dependencies"],
        )
        self.assertFalse(out["persistent_authorization_present"])

    def test_valid_manifest_compiles_offline_readiness(self):
        with tempfile.TemporaryDirectory() as td:
            resume=Path(td)/"resume.pdf"
            resume.write_bytes(b"%PDF-test")
            raw=manifest(str(resume))
            out=intake.compile_readiness(raw,profile(),check_files=True)
        self.assertTrue(out["preflight_ready"])
        self.assertFalse(out["browser_touched"])
        self.assertTrue(out["live_discovery_required"])
        self.assertEqual(out["profile_inventory"]["experience_records"],2)
        self.assertEqual(out["planned_record_counts"]["experience"],2)
        self.assertEqual(out["manifest_contracts"]["choice_answers"],1)
        self.assertEqual(out["manifest_contracts"]["option_selections"],1)
        self.assertEqual(out["manifest_contracts"]["review_expectations"],1)
        self.assertEqual(out["manifest_contracts"]["attachments"][0]["expected_filename"],"resume.pdf")
        self.assertTrue(out["manifest_contracts"]["attachments"][0]["exists"])

    def test_potential_narrative_gaps_are_record_local_and_nonfatal_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            resume=Path(td)/"resume.pdf"
            resume.write_bytes(b"%PDF-test")
            out=intake.compile_readiness(manifest(str(resume)),profile())
        gaps={item["record_index"]:item["missing_if_requested_by_page"] for item in out["potential_record_requirements"]}
        self.assertNotIn(0,gaps)
        self.assertEqual(
            gaps[1],
            ["responsibilities","reason_for_leaving"],
        )
        self.assertTrue(out["preflight_ready"])

    def test_report_does_not_emit_profile_values_or_absolute_attachment_path(self):
        with tempfile.TemporaryDirectory() as td:
            resume=Path(td)/"private-resume.pdf"
            resume.write_bytes(b"%PDF-test")
            out=intake.compile_readiness(manifest(str(resume)),profile())
            rendered=json.dumps(out,ensure_ascii=False)
        self.assertNotIn("Employer A",rendered)
        self.assertNotIn("Employer B",rendered)
        self.assertNotIn("555-0100",rendered)
        self.assertNotIn(str(resume),rendered)
        self.assertIn("private-resume.pdf",rendered)

    def test_fingerprint_matches_normalized_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            resume=Path(td)/"resume.pdf"
            resume.write_bytes(b"%PDF-test")
            raw=manifest(str(resume))
            out=intake.compile_readiness(raw,profile())
            normalized=manifests.validate_manifest(raw,profile(),check_files=True)
        self.assertEqual(
            out["manifest_fingerprint"],
            manifests.manifest_fingerprint(normalized),
        )

    def test_persistent_authorization_is_never_reported_as_present(self):
        with tempfile.TemporaryDirectory() as td:
            resume=Path(td)/"resume.pdf"
            resume.write_bytes(b"%PDF-test")
            out=intake.compile_readiness(manifest(str(resume)),profile())
        self.assertFalse(out["persistent_authorization_present"])
        self.assertTrue(out["runtime_authorization_required_for_submit"])
        self.assertTrue(out["runtime_authorization_required_for_legal_certification"])

    def test_compile_from_files_accepts_utf8_bom_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            resume=root/"resume.pdf"
            resume.write_bytes(b"%PDF-test")
            profile_path=root/"profile.json"
            profile_path.write_text(json.dumps(profile(),ensure_ascii=False),encoding="utf-8")
            manifest_path=root/"application.json"
            manifest_path.write_text(
                json.dumps(manifest(str(resume)),ensure_ascii=False),
                encoding="utf-8-sig",
            )
            out=intake.compile_from_files(profile_path,manifest_path,check_files=True)
        self.assertTrue(out["preflight_ready"])
        self.assertFalse(out["browser_touched"])

    def test_runner_preflight_cli_is_zero_touch_and_returns_same_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            resume=root/"resume.pdf"
            resume.write_bytes(b"%PDF-test")
            profile_path=root/"profile.json"
            profile_path.write_text(json.dumps(profile(),ensure_ascii=False),encoding="utf-8")
            manifest_path=root/"application.json"
            raw=manifest(str(resume))
            manifest_path.write_text(json.dumps(raw,ensure_ascii=False),encoding="utf-8")
            expected=intake.compile_readiness(raw,profile(),check_files=True)
            output=io.StringIO()
            with patch.object(runner.provider,"snapshot_raw") as snapshot_raw, \
                 patch.object(runner.provider,"snapshot") as snapshot, \
                 patch.object(runner.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(runner.sessions,"load") as session_load, \
                 patch.object(runner.sessions,"save") as session_save, \
                 redirect_stdout(output):
                exit_code=runner.main([
                    "preflight",
                    "--profile",str(profile_path),
                    "--manifest",str(manifest_path),
                ])
        self.assertEqual(exit_code,0)
        out=json.loads(output.getvalue())
        self.assertTrue(out["preflight_ready"])
        self.assertFalse(out["browser_touched"])
        self.assertEqual(out["manifest_fingerprint"],expected["manifest_fingerprint"])
        snapshot_raw.assert_not_called()
        snapshot.assert_not_called()
        select_tab.assert_not_called()
        session_load.assert_not_called()
        session_save.assert_not_called()

    def test_runner_preflight_cli_rejects_missing_attachment_before_browser(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            profile_path=root/"profile.json"
            profile_path.write_text(json.dumps(profile(),ensure_ascii=False),encoding="utf-8")
            manifest_path=root/"application.json"
            raw=manifest(str(root/"missing.pdf"))
            manifest_path.write_text(json.dumps(raw,ensure_ascii=False),encoding="utf-8")
            with patch.object(runner.provider,"snapshot_raw") as snapshot_raw, \
                 patch.object(runner.provider,"snapshot") as snapshot, \
                 patch.object(runner.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(runner.sessions,"load") as session_load, \
                 self.assertRaises(manifests.ManifestError):
                runner.main([
                    "preflight",
                    "--profile",str(profile_path),
                    "--manifest",str(manifest_path),
                ])
        snapshot_raw.assert_not_called()
        snapshot.assert_not_called()
        select_tab.assert_not_called()
        session_load.assert_not_called()

    def test_invalid_manifest_fails_during_offline_compile(self):
        with tempfile.TemporaryDirectory() as td:
            missing=Path(td)/"missing.pdf"
            raw=manifest(str(missing))
            with self.assertRaises(manifests.ManifestError):
                intake.compile_readiness(raw,profile(),check_files=True)


if __name__=="__main__":
    unittest.main()
