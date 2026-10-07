#!/usr/bin/env python3
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import job_application_discovery_v2 as discovery
import job_application_engine_v2 as engine
import job_application_runner_v2 as runner
import resume_profile


def profile():
    p=resume_profile.empty_profile()
    p["identity"]["first_name"]="Jack"
    p["identity"]["last_name"]="Monaghan"
    p["experience"]=[{
        "employer":"Secret Employer",
        "title":"Secret Driver",
        "start":"2025-01",
        "end":None,
        "current":True,
        "may_contact":True,
        "phone":"555-0100",
        "responsibilities":"Private responsibilities.",
        "salary":"Private salary",
        "supervisor":"Private supervisor",
        "supervisor_note":"",
    }]
    return p


def manifest():
    return {
        "schema_version":1,
        "application_id":"discovery-REQ1",
        "job":{"title":"Target Job","employer":"Example Employer","requisition_id":"REQ1"},
        "browser_target":{"tab_name":"Target Job"},
        "context":{"auto_bind_repeating_sections":True},
    }


def state():
    return engine.PageState.from_obj({"controls":[
        {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
        {"type":"ControlType.Edit","name":"Company","value":"Secret Employer","required":True,
         "group_path":["Work Experience 1","My Experience"],"enabled":True,"offscreen":False},
        {"type":"ControlType.Edit","name":"Job Title","value":"Secret Driver",
         "group_path":["Work Experience 1","My Experience"],"enabled":True,"offscreen":False},
        {"type":"ControlType.ComboBox","name":"Schedule","value":"Night","required":True,
         "group_path":["Schedule Preference","Application Questions"],"enabled":True,"offscreen":False,
         "expand_collapse":"Collapsed"},
        {"type":"ControlType.RadioButton","name":"Yes","selected":True,"required":True,
         "group_path":["Are you willing to travel?","Application Questions"],"enabled":True,"offscreen":False},
        {"type":"ControlType.RadioButton","name":"No","selected":False,"required":True,
         "group_path":["Are you willing to travel?","Application Questions"],"enabled":True,"offscreen":False},
        {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
    ]})


def write_files(root: Path) -> tuple[Path,Path]:
    profile_path=root/"profile.json"
    profile_path.write_text(json.dumps(profile(),ensure_ascii=False),encoding="utf-8")
    manifest_path=root/"application.json"
    manifest_path.write_text(json.dumps(manifest(),ensure_ascii=False),encoding="utf-8")
    return profile_path,manifest_path


class DiscoveryV2Tests(unittest.TestCase):
    def test_compiled_discovery_is_structural_and_does_not_emit_field_values(self):
        import job_application_manifest_v2 as manifests
        normalized=manifests.validate_manifest(manifest(),profile())
        out=discovery.compile_discovery(state(),normalized,browser_restored=True)
        rendered=json.dumps(out,ensure_ascii=False)
        self.assertNotIn("Secret Employer",rendered)
        self.assertNotIn("Secret Driver",rendered)
        self.assertNotIn('"Night"',rendered)
        self.assertNotIn("555-0100",rendered)
        self.assertNotIn("Private responsibilities",rendered)
        self.assertEqual(out["page"]["current_step"]["number"],2)
        self.assertFalse(out["mutation_executed"])
        self.assertFalse(out["session_touched"])
        self.assertTrue(out["browser_restored"])
        self.assertEqual(out["required_controls"][0]["name"],"Company")
        self.assertTrue(out["required_controls"][0]["observed_populated"])
        choice=next(x for x in out["choice_groups"] if x["question"]=="Are you willing to travel?")
        self.assertEqual(choice["option_names"],["No","Yes"])
        self.assertTrue(choice["has_selection"])
        self.assertNotIn("selected_option",choice)

    def test_discovery_selects_target_then_restores_original_tab(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            tabs={"ok":True,"tabs":[
                {"name":"PC Engineering","runtime_id":"42.1","selected":True,"enabled":True},
                {"name":"Target Job","runtime_id":"42.2","selected":False,"enabled":True},
            ]}
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab",return_value={"ok":True}) as select_tab, \
                 patch.object(discovery.provider,"snapshot",return_value=state()) as snapshot:
                out=discovery.discover_from_files(str(profile_path),str(manifest_path))
        self.assertEqual(select_tab.call_count,2)
        self.assertEqual(select_tab.call_args_list[0].kwargs,{"tab_name":"Target Job"})
        self.assertEqual(select_tab.call_args_list[1].kwargs,{"runtime_id":"42.1"})
        snapshot.assert_called_once_with()
        self.assertTrue(out["browser_restored"])

    def test_discovery_restores_original_tab_when_snapshot_fails(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            tabs={"ok":True,"tabs":[
                {"name":"PC Engineering","runtime_id":"42.1","selected":True,"enabled":True},
                {"name":"Target Job","runtime_id":"42.2","selected":False,"enabled":True},
            ]}
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab",return_value={"ok":True}) as select_tab, \
                 patch.object(discovery.provider,"snapshot",side_effect=RuntimeError("snapshot failed")):
                with self.assertRaisesRegex(RuntimeError,"snapshot failed"):
                    discovery.discover_from_files(str(profile_path),str(manifest_path))
        self.assertEqual(select_tab.call_count,2)
        self.assertEqual(select_tab.call_args_list[-1].kwargs,{"runtime_id":"42.1"})

    def test_discovery_fails_closed_on_ambiguous_browser_target(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            raw=manifest()
            raw["browser_target"]={"contains":"Target"}
            manifest_path.write_text(json.dumps(raw,ensure_ascii=False),encoding="utf-8")
            tabs={"ok":True,"tabs":[
                {"name":"PC Engineering","selected":True,"enabled":True},
                {"name":"Target Job","selected":False,"enabled":True},
                {"name":"Target Job - Duplicate","selected":False,"enabled":True},
            ]}
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(discovery.provider,"snapshot") as snapshot:
                with self.assertRaisesRegex(discovery.DiscoveryError,"match count 2"):
                    discovery.discover_from_files(str(profile_path),str(manifest_path))
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_validate_runtime_target_is_read_only_and_manifest_scoped(self):
        tabs={"ok":True,"tabs":[
            {"name":"Target Job","runtime_id":"42.2","selected":False,"enabled":True},
            {"name":"Unrelated","runtime_id":"42.9","selected":True,"enabled":True},
        ]}
        with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs) as list_tabs, \
             patch.object(discovery.firefox_adapter,"select_tab") as select_tab, \
             patch.object(discovery.provider,"snapshot") as snapshot:
            out=discovery.validate_runtime_target({"tab_name":"Target Job"},"42.2")
        self.assertEqual(out,{"runtime_id":"42.2","name":"Target Job"})
        list_tabs.assert_called_once_with()
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_runtime_id_disambiguates_duplicate_manifest_target(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            tabs={"ok":True,"tabs":[
                {"name":"PC Engineering","runtime_id":"42.1","selected":True,"enabled":True},
                {"name":"Target Job","runtime_id":"42.2","selected":False,"enabled":True},
                {"name":"Target Job","runtime_id":"42.3","selected":False,"enabled":True},
            ]}
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab",return_value={"ok":True}) as select_tab, \
                 patch.object(discovery.provider,"snapshot",return_value=state()) as snapshot:
                out=discovery.discover_from_files(
                    str(profile_path),
                    str(manifest_path),
                    runtime_id="42.3",
                )
        self.assertEqual(select_tab.call_count,2)
        self.assertEqual(select_tab.call_args_list[0].kwargs,{"runtime_id":"42.3"})
        self.assertEqual(select_tab.call_args_list[1].kwargs,{"runtime_id":"42.1"})
        snapshot.assert_called_once_with()
        self.assertTrue(out["browser_restored"])

    def test_runtime_id_must_still_match_manifest_browser_target(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            tabs={"ok":True,"tabs":[
                {"name":"PC Engineering","runtime_id":"42.1","selected":True,"enabled":True},
                {"name":"Target Job","runtime_id":"42.2","selected":False,"enabled":True},
                {"name":"Unrelated Tab","runtime_id":"42.9","selected":False,"enabled":True},
            ]}
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(discovery.provider,"snapshot") as snapshot:
                with self.assertRaisesRegex(
                    discovery.DiscoveryError,
                    "does not satisfy manifest browser target",
                ):
                    discovery.discover_from_files(
                        str(profile_path),
                        str(manifest_path),
                        runtime_id="42.9",
                    )
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_discovery_restores_duplicate_named_original_by_runtime_id(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            tabs={"ok":True,"tabs":[
                {"name":"Duplicate","runtime_id":"42.10","selected":True,"enabled":True},
                {"name":"Duplicate","runtime_id":"42.11","selected":False,"enabled":True},
                {"name":"Target Job","runtime_id":"42.12","selected":False,"enabled":True},
            ]}
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab",return_value={"ok":True}) as select_tab, \
                 patch.object(discovery.provider,"snapshot",return_value=state()) as snapshot:
                out=discovery.discover_from_files(str(profile_path),str(manifest_path))
        self.assertEqual(select_tab.call_count,2)
        self.assertEqual(select_tab.call_args_list[0].kwargs,{"tab_name":"Target Job"})
        self.assertEqual(select_tab.call_args_list[1].kwargs,{"runtime_id":"42.10"})
        snapshot.assert_called_once_with()
        self.assertTrue(out["browser_restored"])

    def test_discovery_without_runtime_id_still_fails_if_original_name_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            tabs={"ok":True,"tabs":[
                {"name":"Duplicate","selected":True,"enabled":True},
                {"name":"Duplicate","selected":False,"enabled":True},
                {"name":"Target Job","selected":False,"enabled":True},
            ]}
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(discovery.provider,"snapshot") as snapshot:
                with self.assertRaises(discovery.DiscoveryError):
                    discovery.discover_from_files(str(profile_path),str(manifest_path))
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_runner_discover_cli_does_not_execute_mutations_or_touch_sessions(self):
        with tempfile.TemporaryDirectory() as td:
            profile_path,manifest_path=write_files(Path(td))
            tabs={"ok":True,"tabs":[
                {"name":"PC Engineering","selected":True,"enabled":True},
                {"name":"Target Job","selected":False,"enabled":True},
            ]}
            output=io.StringIO()
            with patch.object(discovery.firefox_adapter,"list_tabs",return_value=tabs), \
                 patch.object(discovery.firefox_adapter,"select_tab",return_value={"ok":True}), \
                 patch.object(discovery.provider,"snapshot",return_value=state()), \
                 patch.object(runner.provider,"execute") as execute, \
                 patch.object(runner.sessions,"load") as session_load, \
                 patch.object(runner.sessions,"save") as session_save, \
                 redirect_stdout(output):
                exit_code=runner.main([
                    "discover",
                    "--profile",str(profile_path),
                    "--manifest",str(manifest_path),
                ])
        self.assertEqual(exit_code,0)
        out=json.loads(output.getvalue())
        self.assertFalse(out["mutation_executed"])
        self.assertFalse(out["session_touched"])
        execute.assert_not_called()
        session_load.assert_not_called()
        session_save.assert_not_called()


if __name__=="__main__":
    unittest.main()
