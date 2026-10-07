#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import job_application_manifest_v2 as manifests
import job_application_runner_v2 as runner
import resume_profile


def profile():
    p = resume_profile.empty_profile()
    p["identity"]["first_name"] = "Jack"
    p["identity"]["last_name"] = "Monaghan"
    p["experience"] = [{
        "employer":"Employer A",
        "title":"Driver",
        "start":"2025-01",
        "end":None,
        "current":True,
        "may_contact":True,
        "phone":"",
        "responsibilities":"Delivered freight.",
        "salary":"",
        "supervisor":"",
        "supervisor_note":"",
    }]
    return p


def minimal_manifest():
    return {
        "schema_version": 1,
        "application_id": "example-employer-REQ123",
        "job": {
            "title": "Example Role",
            "employer": "Example Employer",
            "requisition_id": "REQ123",
        },
        "browser_target": {"tab_name": "Example Role"},
        "context": {
            "auto_bind_repeating_sections": True,
            "source_path": ["Website", "Employer Site"],
        },
    }


class ManifestV2Tests(unittest.TestCase):
    def test_minimal_manifest_validates(self):
        out = manifests.validate_manifest(minimal_manifest(), profile())
        self.assertEqual(out["application_id"], "example-employer-REQ123")
        self.assertEqual(out["browser_target"], {"tab_name": "Example Role"})
        self.assertTrue(out["context"]["auto_bind_repeating_sections"])

    def test_nested_persistent_authorization_is_rejected(self):
        m = minimal_manifest()
        m["context"]["record_overrides"] = {
            "experience": {
                "0": {
                    "reason_for_leaving": "Accepted another position.",
                    "certify_truthfulness": True,
                }
            }
        }
        with self.assertRaises(manifests.ManifestError) as cm:
            manifests.validate_manifest(m, profile())
        self.assertIn("forbidden persistent authorization", str(cm.exception))

    def test_top_level_policy_or_secret_state_is_rejected_recursively(self):
        for key, value in (
            ("allow_submit", True),
            ("allow_legal_certification", True),
            ("api_key", "secret"),
        ):
            m = minimal_manifest()
            m[key] = value
            with self.subTest(key=key):
                with self.assertRaises(manifests.ManifestError):
                    manifests.validate_manifest(m, profile())

    def test_repeating_goal_cannot_exceed_profile_records(self):
        m = minimal_manifest()
        m["context"]["repeating_section_goals"] = [
            {"source":"experience","desired_count":2}
        ]
        with self.assertRaises(manifests.ManifestError) as cm:
            manifests.validate_manifest(m, profile())
        self.assertIn("exceeds profile records", str(cm.exception))

    def test_record_override_must_target_existing_record_and_supported_fact(self):
        m = minimal_manifest()
        m["context"]["record_overrides"] = {
            "experience":{"1":{"reason_for_leaving":"Reason"}}
        }
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(m, profile())

        m = minimal_manifest()
        m["context"]["record_overrides"] = {
            "experience":{"0":{"made_up_fact":"x"}}
        }
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(m, profile())

    def test_attachment_preflight_requires_absolute_existing_matching_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "resume.pdf"
            path.write_bytes(b"%PDF-test")
            m = minimal_manifest()
            m["context"]["attachments"] = [{
                "path": str(path),
                "expected_filename": "resume.pdf",
                "target": {"name":"Select Files"},
                "success_text": "Successfully Uploaded!",
            }]
            out = manifests.validate_manifest(m, profile(), check_files=True)
            self.assertEqual(out["context"]["attachments"][0]["expected_filename"], "resume.pdf")

            bad = minimal_manifest()
            bad["context"]["attachments"] = [{
                "path": str(path),
                "expected_filename": "wrong.pdf",
                "target": {"name":"Select Files"},
            }]
            with self.assertRaises(manifests.ManifestError):
                manifests.validate_manifest(bad, profile(), check_files=True)

            missing = minimal_manifest()
            missing_path = Path(td) / "missing.pdf"
            missing["context"]["attachments"] = [{
                "path": str(missing_path),
                "expected_filename": "missing.pdf",
                "target": {"name":"Select Files"},
            }]
            with self.assertRaises(manifests.ManifestError):
                manifests.validate_manifest(missing, profile(), check_files=True)

    def test_application_id_is_stable_filename_safe_token(self):
        for bad in ("", "has spaces", "../escape", "slash/name", "x"*129):
            m = minimal_manifest()
            m["application_id"] = bad
            with self.subTest(bad=bad):
                with self.assertRaises(manifests.ManifestError):
                    manifests.validate_manifest(m, profile())

    def test_application_date_requires_real_iso_date(self):
        m = minimal_manifest()
        m["context"]["application_date"] = "2026-02-30"
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(m, profile())

    def test_entrypoint_requires_exact_button_and_disappearance_verifier(self):
        m=minimal_manifest()
        m["context"]["entrypoint"]={
            "target":{"control_type":"ControlType.Button","name":"Apply"},
            "verify":{"kind":"control_absent","name":"Apply"},
        }
        out=manifests.validate_manifest(m,profile())
        self.assertEqual(
            out["context"]["entrypoint"],
            {
                "target":{"control_type":"ControlType.Button","name":"Apply"},
                "verify":{"kind":"control_absent","name":"Apply"},
            },
        )

        wrong_type=minimal_manifest()
        wrong_type["context"]["entrypoint"]={
            "target":{"control_type":"ControlType.Edit","name":"Apply"},
            "verify":{"kind":"control_absent","name":"Apply"},
        }
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(wrong_type,profile())

        mismatched=minimal_manifest()
        mismatched["context"]["entrypoint"]={
            "target":{"name":"Apply"},
            "verify":{"kind":"control_absent","name":"Start Application"},
        }
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(mismatched,profile())

        missing_name=minimal_manifest()
        missing_name["context"]["entrypoint"]={
            "target":{"automation_id":"apply-button"},
            "verify":{"kind":"control_absent","name":"Apply"},
        }
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(missing_name,profile())

    def test_option_selection_requires_executable_combobox_target(self):
        m = minimal_manifest()
        m["context"]["option_selections"] = [{
            "target":{"control_type":"ControlType.ComboBox","name":"Schedule"},
            "value":"Night",
        }]
        out = manifests.validate_manifest(m, profile())
        self.assertEqual(
            out["context"]["option_selections"][0]["target"]["control_type"],
            "ControlType.ComboBox",
        )

        bad = minimal_manifest()
        bad["context"]["option_selections"] = [{
            "target":{"control_type":"ControlType.Edit","name":"Schedule"},
            "value":"Night",
        }]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(bad, profile())

        bad = minimal_manifest()
        bad["context"]["option_selections"] = [{
            "target":{"group_name":"Application Questions"},
            "value":"Night",
        }]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(bad, profile())

    def test_explicit_repeating_section_mapping_requires_existing_populated_typed_facts(self):
        p = profile()
        p["experience"][0]["current"] = True
        p["experience"][0]["phone"] = "555-0100"
        m = minimal_manifest()
        m["context"]["repeating_sections"] = [{
            "source":"experience",
            "record_index":0,
            "group_name":"Work Experience 1",
            "fields":{"Company":"employer","Phone":"phone"},
            "toggles":{"I currently work here":"current"},
            "options":{},
        }]
        out = manifests.validate_manifest(m, p)
        spec = out["context"]["repeating_sections"][0]
        self.assertEqual(spec["fields"]["Company"], "employer")
        self.assertEqual(spec["toggles"]["I currently work here"], "current")

        missing = minimal_manifest()
        missing["context"]["repeating_sections"] = [{
            "source":"experience",
            "record_index":0,
            "group_name":"Work Experience 1",
            "fields":{"Supervisor":"does_not_exist"},
        }]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(missing, p)

        empty = minimal_manifest()
        empty["context"]["repeating_sections"] = [{
            "source":"experience",
            "record_index":0,
            "group_name":"Work Experience 1",
            "fields":{"Supervisor":"supervisor"},
        }]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(empty, p)

        wrong_type = minimal_manifest()
        wrong_type["context"]["repeating_sections"] = [{
            "source":"experience",
            "record_index":0,
            "group_name":"Work Experience 1",
            "toggles":{"I currently work here":"employer"},
        }]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(wrong_type, p)

    def test_explicit_repeating_sections_reject_duplicate_scope_assignment(self):
        p = profile()
        m = minimal_manifest()
        m["context"]["repeating_sections"] = [
            {
                "source":"experience","record_index":0,"group_name":"Work Experience 1",
                "fields":{"Company":"employer"},
            },
            {
                "source":"experience","record_index":0,"group_name":"Work Experience 1",
                "fields":{"Job Title":"title"},
            },
        ]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(m, p)

    def test_review_expectations_are_limited_to_engine_supported_contract(self):
        m = minimal_manifest()
        m["context"]["review_expectations"] = [
            {"kind":"contains_text","value":"Spokane County"},
            {"kind":"not_contains_text","value":"Community Event"},
            {"kind":"review_field_value","field":"How Did You Hear About Us?","value":"Spokane County"},
        ]
        out = manifests.validate_manifest(m, profile())
        self.assertEqual(len(out["context"]["review_expectations"]), 3)

        bad = minimal_manifest()
        bad["context"]["review_expectations"] = [
            {"kind":"regex","value":".*"}
        ]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(bad, profile())

        bad = minimal_manifest()
        bad["context"]["review_expectations"] = [
            {"kind":"review_field_value","value":"Spokane County"}
        ]
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(bad, profile())

    def test_scoped_manual_review_expectation_validates_group_name(self):
        m=minimal_manifest()
        m["context"]["review_expectations"]=[{
            "kind":"review_field_value",
            "field":"Company",
            "value":"Employer A",
            "group_name":"Work Experience 1",
        }]
        out=manifests.validate_manifest(m,profile())
        self.assertEqual(
            out["context"]["review_expectations"][0]["group_name"],
            "Work Experience 1",
        )
        m["context"]["review_expectations"][0]["group_name"]=""
        with self.assertRaises(manifests.ManifestError):
            manifests.validate_manifest(m,profile())

    def test_shared_manifest_loader_accepts_utf8_bom(self):
        p=profile()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"application.json"
            path.write_text(
                json.dumps(minimal_manifest(),ensure_ascii=False),
                encoding="utf-8-sig",
            )
            out=manifests.load_manifest(path,p)
        self.assertEqual(out["application_id"],"example-employer-REQ123")
        self.assertEqual(out["browser_target"],{"tab_name":"Example Role"})

    def test_manifest_fingerprint_is_canonical_and_semantic(self):
        p=profile()
        first=manifests.validate_manifest(minimal_manifest(),p)
        reordered={
            "context":{
                "source_path":["Website","Employer Site"],
                "auto_bind_repeating_sections":True,
            },
            "browser_target":{"tab_name":"Example Role"},
            "job":{
                "requisition_id":"REQ123",
                "employer":"Example Employer",
                "title":"Example Role",
            },
            "application_id":"example-employer-REQ123",
            "schema_version":1,
        }
        second=manifests.validate_manifest(reordered,p)
        self.assertEqual(
            manifests.manifest_fingerprint(first),
            manifests.manifest_fingerprint(second),
        )
        changed=minimal_manifest()
        changed["context"]["source_path"]=["Website","Different Source"]
        changed=manifests.validate_manifest(changed,p)
        self.assertNotEqual(
            manifests.manifest_fingerprint(first),
            manifests.manifest_fingerprint(changed),
        )

    def test_runner_manifest_mode_rejects_mixed_legacy_application_inputs(self):
        p = profile()
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "application.json"
            manifest_path.write_text(json.dumps(minimal_manifest()), encoding="utf-8")
            with self.assertRaises(ValueError):
                runner._resolve_application_inputs(
                    p,
                    manifest_path=str(manifest_path),
                    context_path="legacy.json",
                    application_id=None,
                    tab_name=None,
                    tab_contains=None,
                )
            with self.assertRaises(ValueError):
                runner._resolve_application_inputs(
                    p,
                    manifest_path=str(manifest_path),
                    context_path=None,
                    application_id="legacy-app",
                    tab_name=None,
                    tab_contains=None,
                )

    def test_runner_resolves_valid_manifest_into_one_application_identity(self):
        p = profile()
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "application.json"
            manifest_path.write_text(json.dumps(minimal_manifest()), encoding="utf-8")
            context, app_id, browser, fingerprint = runner._resolve_application_inputs(
                p,
                manifest_path=str(manifest_path),
                context_path=None,
                application_id=None,
                tab_name=None,
                tab_contains=None,
            )
        self.assertEqual(app_id, "example-employer-REQ123")
        self.assertEqual(browser, {"tab_name":"Example Role"})
        self.assertEqual(context["source_path"], ["Website","Employer Site"])
        self.assertEqual(fingerprint, manifests.manifest_fingerprint(
            manifests.validate_manifest(minimal_manifest(), p)
        ))

    def test_invalid_manifest_preflight_does_not_touch_browser_or_provider(self):
        p = profile()
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "application.json"
            m = minimal_manifest()
            m["context"]["attachments"] = [{
                "path": str(Path(td) / "missing.pdf"),
                "expected_filename": "missing.pdf",
                "target": {"name":"Select Files"},
            }]
            manifest_path.write_text(json.dumps(m), encoding="utf-8")
            with patch.object(runner.firefox_adapter, "select_tab") as select_tab, \
                 patch.object(runner.provider, "snapshot") as snapshot:
                with self.assertRaises(manifests.ManifestError):
                    runner._resolve_application_inputs(
                        p,
                        manifest_path=str(manifest_path),
                        context_path=None,
                        application_id=None,
                        tab_name=None,
                        tab_contains=None,
                    )
        select_tab.assert_not_called()
        snapshot.assert_not_called()


if __name__ == "__main__":
    unittest.main()
