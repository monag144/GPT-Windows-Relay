#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

import job_application_engine_v2 as eng
import job_application_runner_v2 as runner


def state(*controls):
    return eng.PageState.from_obj({"controls": list(controls)})


class RunnerVerifierTests(unittest.TestCase):
    def test_value_verifier(self):
        s = state({"type":"ControlType.Edit","id":"email","name":"Email","value":"a@example.com"})
        action={"op":"set_text","target":{"automation_id":"email","name":"Email"},"verify":{"kind":"value_equals","value":"a@example.com"}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_value_verifier_honors_group_scope(self):
        s=state(
            {"type":"ControlType.Edit","name":"Company","value":"First","group_path":["Work Experience 1"]},
            {"type":"ControlType.Edit","name":"Company","value":"Second","group_path":["Work Experience 2"]},
        )
        action={"op":"set_text","target":{"name":"Company","group_name":"Work Experience 2"},"verify":{"kind":"value_equals","value":"Second"}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_toggle_verifier(self):
        s = state({"type":"ControlType.CheckBox","id":"terms","name":"I agree","toggle":"On"})
        action={"op":"set_toggle","target":{"automation_id":"terms","name":"I agree"},"verify":{"kind":"toggle_equals","value":"On"}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_terminal_pill_verifier(self):
        s = state({"type":"ControlType.ListItem","name":"Spokane County, press delete to clear value."})
        action={"op":"select_hierarchy","target":{"automation_id":"source--source"},"verify":{"kind":"selected_pill_equals","value":"Spokane County"}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_step_change_verifier(self):
        s = state({"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"})
        action={"op":"invoke","target":{"name":"Save and Continue"},"verify":{"kind":"step_changes","from":{"number":1,"total":6,"label":"My Information"}}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_runner_resolves_reasoning_then_executes_verified_action(self):
        p = __import__("resume_profile").empty_profile()
        p["identity"]["first_name"] = "Jack"
        p["identity"]["last_name"] = "Monaghan"
        empty = state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.Edit","id":"q-interest","name":"Why are you interested?","value":""},
        )
        filled = state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.Edit","id":"q-interest","name":"Why are you interested?","value":"Grounded answer"},
        )
        config={"provider":"static","answers":{"q-interest":"Grounded answer"}}
        with patch.object(runner.provider, "snapshot", side_effect=[empty, empty]), \
             patch.object(runner.provider, "execute", return_value={"ok":True}), \
             patch.object(runner, "wait_for_verification", return_value=(filled, {"ok":True,"attempt":1,"reason":"value readback"})):
            out=runner.run(p, eng.EnginePolicy(), {}, max_iterations=2, reasoning_config=config)
        self.assertEqual(out["status"], "iteration_limit")
        self.assertEqual(out["history"][0]["status"], "needs_reasoning")
        self.assertEqual(out["history"][0]["reasoning_resolved"][0]["key"], "q-interest")
        self.assertEqual(out["history"][1]["actions"][0]["action"]["source"], "reasoning_broker")

    def test_option_verifier_falls_back_after_automation_id_rerender(self):
        s=state(
            {"type":"ControlType.ComboBox","id":"dynamic-C","name":"Schedule","selection":["Night"],"group_path":["Availability"]},
        )
        action={
            "op":"select_option",
            "target":{"control_type":"ControlType.ComboBox","automation_id":"dynamic-A","name":"Schedule","group_name":"Availability"},
            "verify":{"kind":"option_selected","value":"Night"},
        }
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_semantic_fallback_still_fails_on_ambiguous_duplicates(self):
        s=state(
            {"type":"ControlType.Edit","id":"new-A","name":"Company","value":"Employer","group_path":["Work Experience"]},
            {"type":"ControlType.Edit","id":"new-B","name":"Company","value":"Employer","group_path":["Work Experience"]},
        )
        action={
            "op":"set_text",
            "target":{"automation_id":"old-id","name":"Company","group_name":"Work Experience"},
            "verify":{"kind":"value_equals","value":"Employer"},
        }
        ok,reason=runner.verify_action(s,action)
        self.assertFalse(ok)
        self.assertIn("match count 2",reason)

    def test_option_selected_verifier(self):
        s=state({"type":"ControlType.ComboBox","name":"Degree","selection":["High School Diploma"],"group_path":["Education 1"]})
        action={"op":"select_option","target":{"control_type":"ControlType.ComboBox","name":"Degree","group_name":"Education 1"},"verify":{"kind":"option_selected","value":"High School Diploma"}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_section_count_increases_verifier(self):
        s=state(
            {"type":"ControlType.Edit","name":"Company","group_path":["Work Experience 1"]},
            {"type":"ControlType.Edit","name":"Job Title","group_path":["Work Experience 1"]},
            {"type":"ControlType.Edit","name":"Company","group_path":["Work Experience 2"]},
            {"type":"ControlType.Edit","name":"Job Title","group_path":["Work Experience 2"]},
        )
        action={"op":"invoke","target":{"name":"Add Another"},"verify":{"kind":"section_count_increases","family":"Work Experience","before_count":1}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_runner_adds_section_then_binds_new_record_from_fresh_page(self):
        p=__import__("resume_profile").empty_profile()
        p["experience"]=[
            {"employer":"Employer A","title":"Driver A","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
            {"employer":"Employer B","title":"Driver B","start":"2024-01","end":"2024-12","current":False,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
        ]
        first=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Button","id":"add-A","name":"Add Another","enabled":True,"offscreen":False,"top":200,"group_path":["Work Experience","My Experience"]},
        )
        second=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","id":"company-B","name":"Company","value":"","top":300,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","id":"title-B","name":"Job Title","value":"","top":320,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Button","id":"add-B","name":"Add Another","enabled":True,"offscreen":False,"top":400,"group_path":["Work Experience","My Experience"]},
        )
        after_company=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","id":"company-C","name":"Company","value":"Employer B","top":300,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","id":"title-C","name":"Job Title","value":"","top":320,"group_path":["Work Experience 2","My Experience"]},
        )
        context={"auto_bind_repeating_sections":True,"repeating_section_goals":[{"source":"experience","desired_count":2}]}
        executed=[]
        def execute(action):
            executed.append(action)
            return {"ok":True}
        with patch.object(runner.provider,"snapshot",side_effect=[first,second]), \
             patch.object(runner.provider,"execute",side_effect=execute), \
             patch.object(runner,"wait_for_verification",side_effect=[
                 (second,{"ok":True,"attempt":1,"reason":"section family count 2 > 1"}),
                 (after_company,{"ok":True,"attempt":1,"reason":"value readback"}),
             ]):
            out=runner.run(p,eng.EnginePolicy(),context,max_iterations=2)
        self.assertEqual(out["status"],"iteration_limit")
        self.assertEqual(executed[0]["op"],"invoke")
        self.assertEqual(executed[0]["target"]["name"],"Add Another")
        self.assertEqual(out["history"][0]["trusted_new_repeating_group"],"Work Experience 2")
        self.assertEqual(executed[1]["op"],"set_text")
        self.assertEqual(executed[1]["target"]["automation_id"],"company-B")
        self.assertEqual(executed[1]["value"],"Employer B")

    def test_choice_selected_verifier(self):
        question="Are you authorized?"
        s=state({"type":"ControlType.RadioButton","name":"Yes","selected":True,"group_path":["Yes",question]})
        action={"op":"select_choice","target":{"group_name":question,"name":"Yes"},"verify":{"kind":"choice_selected","group_name":question,"option":"Yes"}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_upload_verified_verifier(self):
        s=state(
            {"type":"ControlType.Text","name":"resume.docx"},
            {"type":"ControlType.Text","name":"Successfully Uploaded!"},
        )
        action={"op":"upload_file","verify":{"kind":"upload_verified","expected_filename":"resume.docx","success_text":"Successfully Uploaded!"}}
        self.assertTrue(runner.verify_action(s,action)[0])

    def test_runner_persists_reasoning_without_authorization(self):
        p = __import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        p["identity"]["last_name"]="Monaghan"
        empty=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.Edit","id":"q-interest","name":"Why are you interested?","value":""},
        )
        filled=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.Edit","id":"q-interest","name":"Why are you interested?","value":"Grounded answer"},
        )
        config={"provider":"static","answers":{"q-interest":"Grounded answer"}}
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}), \
             patch.object(runner.provider,"snapshot",side_effect=[empty,empty]), \
             patch.object(runner.provider,"execute",return_value={"ok":True}), \
             patch.object(runner,"wait_for_verification",return_value=(filled,{"ok":True,"attempt":1,"reason":"value readback"})):
            runner.run(p,eng.EnginePolicy(),{},max_iterations=2,reasoning_config=config,application_id="app-session-test")
            persisted=runner.sessions.load("app-session-test")
        self.assertEqual(persisted["reasoned_answers"]["q-interest"],"Grounded answer")
        self.assertNotIn("allow_submit",persisted)
        self.assertNotIn("allow_legal_certification",persisted)
        self.assertNotIn("certify_truthfulness",persisted)

    def test_runner_restores_downstream_revalidation_requirement(self):
        p=__import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        p["identity"]["last_name"]="Monaghan"
        current=state({"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"})
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("app-revalidation-test")
            runner.sessions.observe_step(s,5)
            runner.sessions.save(s)
            with patch.object(runner.provider,"snapshot",return_value=current):
                out=runner.run(p,eng.EnginePolicy(),{},max_iterations=1,application_id="app-revalidation-test")
            persisted=runner.sessions.load("app-revalidation-test")
        self.assertEqual(persisted["downstream_revalidation_required_from"],3)
        self.assertEqual(out["history"][0]["downstream_revalidation_required_from"],3)

    def test_runner_replans_after_each_mutation_and_uses_fresh_target(self):
        p=__import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        p["identity"]["last_name"]="Monaghan"
        first=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-old","name":"First Name","value":""},
            {"type":"ControlType.Edit","id":"last-old","name":"Last Name","value":""},
        )
        after_first=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-new","name":"First Name","value":"Jack"},
            {"type":"ControlType.Edit","id":"last-new","name":"Last Name","value":""},
        )
        after_second=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-newer","name":"First Name","value":"Jack"},
            {"type":"ControlType.Edit","id":"last-newer","name":"Last Name","value":"Monaghan"},
        )
        executed=[]
        def execute(action):
            executed.append(action)
            return {"ok":True}
        with patch.object(runner.provider,"snapshot",side_effect=[first,after_first]), \
             patch.object(runner.provider,"execute",side_effect=execute), \
             patch.object(runner,"wait_for_verification",side_effect=[
                 (after_first,{"ok":True,"attempt":1,"reason":"value readback"}),
                 (after_second,{"ok":True,"attempt":1,"reason":"value readback"}),
             ]):
            out=runner.run(p,eng.EnginePolicy(),{},max_iterations=2)
        self.assertEqual(out["status"],"iteration_limit")
        self.assertEqual(len(executed),2)
        self.assertEqual(executed[0]["target"]["automation_id"],"first-old")
        self.assertEqual(executed[1]["target"]["automation_id"],"last-new")
        self.assertEqual(out["history"][0]["planned_action_count"],2)
        self.assertEqual(len(out["history"][0]["actions"]),1)

    def test_iteration_budget_supports_long_one_mutation_cycles(self):
        p=__import__("resume_profile").empty_profile()
        with patch.object(runner.provider,"snapshot",return_value=state()):
            out=runner.run(p,eng.EnginePolicy(),{},max_iterations=101)
        self.assertIn(out["status"],{"blocked","done","ready_to_submit","needs_reasoning","iteration_limit"})

    def test_runner_probes_selector_then_reasons_then_selects(self):
        p=__import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        p["identity"]["last_name"]="Monaghan"
        blank=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule-A","name":"Schedule","value":"","group_path":["Availability","Application Questions"]},
        )
        selected=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule-C","name":"Schedule","selection":["Night"],"group_path":["Availability","Application Questions"]},
        )
        executed=[]
        def execute(action):
            executed.append(action)
            if action["op"]=="inspect_options":
                return {"ok":True,"op":"inspect_options","options":["Day","Night"],"selection_unchanged":True}
            return {"ok":True,"op":"select_option","option":"Night","selected":True}
        config={"provider":"static","answers":{"Availability::Schedule":"Night"}}
        with patch.object(runner.provider,"snapshot",side_effect=[blank,blank,blank]), \
             patch.object(runner.provider,"execute",side_effect=execute), \
             patch.object(runner,"wait_for_verification",return_value=(selected,{"ok":True,"attempt":1,"reason":"option selected"})):
            out=runner.run(p,eng.EnginePolicy(),{},max_iterations=3,reasoning_config=config)
        self.assertEqual(out["status"],"iteration_limit")
        self.assertEqual([x["op"] for x in executed],["inspect_options","select_option"])
        self.assertEqual(out["history"][0]["actions"][0]["provider"]["option_count"],2)
        self.assertEqual(out["history"][1]["status"],"needs_reasoning")
        self.assertEqual(out["history"][1]["reasoning_resolved"][0]["key"],"Availability::Schedule")
        self.assertEqual(out["history"][2]["actions"][0]["action"]["value"],"Night")

    def test_runner_review_uses_persisted_verified_assertion(self):
        p=__import__("resume_profile").empty_profile()
        review=state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"How Did You Hear About Us?"},
            {"type":"ControlType.Text","name":"Community Event"},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("review-ledger-app")
            runner.sessions.record_verified_action(
                s,
                {"op":"select_hierarchy","target":{"name":"How Did You Hear About Us?"},"verify":{"kind":"selected_pill_equals","value":"Spokane County"}},
                1,
            )
            runner.sessions.save(s)
            with patch.object(runner.provider,"snapshot",return_value=review):
                out=runner.run(p,eng.EnginePolicy(),{},max_iterations=1,application_id="review-ledger-app")
        self.assertEqual(out["status"],"blocked")
        self.assertIn("Spokane County",out["decision"]["review_mismatches"][0])

    def test_runner_review_scopes_persisted_assertion_to_repeated_record(self):
        p=__import__("resume_profile").empty_profile()
        review=state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"Company","group_path":["Work Experience 1","Review"]},
            {"type":"ControlType.Text","name":"Employer A","group_path":["Work Experience 1","Review"]},
            {"type":"ControlType.Text","name":"Company","group_path":["Work Experience 2","Review"]},
            {"type":"ControlType.Text","name":"Employer B","group_path":["Work Experience 2","Review"]},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("review-scope-ledger-app")
            runner.sessions.record_verified_action(
                s,
                {
                    "op":"set_text",
                    "target":{"name":"Company","group_name":"Work Experience 1"},
                    "value":"Employer B",
                },
                2,
            )
            runner.sessions.save(s)
            with patch.object(runner.provider,"snapshot",return_value=review):
                out=runner.run(
                    p,
                    eng.EnginePolicy(allow_submit=True),
                    {},
                    max_iterations=1,
                    application_id="review-scope-ledger-app",
                )
        self.assertEqual(out["status"],"blocked")
        self.assertTrue(
            any("Work Experience 1" in x for x in out["decision"]["review_mismatches"])
        )

    def test_history_action_redacts_local_upload_path(self):
        raw={
            "op":"upload_file",
            "target":{"name":"Select files"},
            "path":r"C:\\Users\\Example\\Private\\resume.docx",
            "expected_filename":"resume.docx",
        }
        safe=runner._history_action(raw)
        self.assertEqual(safe["path"],"[local file path omitted]")
        self.assertEqual(safe["expected_filename"],"resume.docx")
        self.assertIn("Private",raw["path"])
        self.assertNotIn("Private",safe["path"])

    def test_runner_pins_tab_before_perception_and_verification(self):
        p=__import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        first=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-A","name":"First Name","value":""},
        )
        filled=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-B","name":"First Name","value":"Jack"},
        )
        with patch.object(runner.firefox_adapter,"select_tab",return_value={"ok":True,"selected_name":"Road Maintenance Specialist"}) as select_tab, \
             patch.object(runner.provider,"snapshot",side_effect=[first,filled]), \
             patch.object(runner.provider,"execute",return_value={"ok":True}):
            out=runner.run(
                p,eng.EnginePolicy(),{},max_iterations=1,
                browser_target={"tab_name":"Road Maintenance Specialist"},
            )
        self.assertEqual(out["status"],"iteration_limit")
        self.assertGreaterEqual(select_tab.call_count,2)
        for call in select_tab.call_args_list:
            self.assertEqual(call.kwargs,{"tab_name":"Road Maintenance Specialist"})

    def test_runner_reuses_runtime_id_after_initial_title_pin(self):
        p=__import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        first=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-A","name":"First Name","value":""},
        )
        filled=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-B","name":"First Name","value":"Jack"},
        )
        with patch.object(
            runner.firefox_adapter,
            "select_tab",
            side_effect=[
                {"ok":True,"selected_name":"Road Maintenance Specialist","runtime_id":"42.7.9"},
                {"ok":True,"selected_name":"Candidate Home","runtime_id":"42.7.9"},
            ],
        ) as select_tab, \
             patch.object(runner.provider,"snapshot",side_effect=[first,filled]), \
             patch.object(runner.provider,"execute",return_value={"ok":True}):
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                browser_target={"tab_name":"Road Maintenance Specialist"},
            )
        self.assertEqual(out["status"],"iteration_limit")
        self.assertEqual(select_tab.call_count,2)
        self.assertEqual(
            select_tab.call_args_list[0].kwargs,
            {"tab_name":"Road Maintenance Specialist"},
        )
        self.assertEqual(
            select_tab.call_args_list[1].kwargs,
            {"runtime_id":"42.7.9"},
        )

    def test_runner_persists_and_reuses_browser_tab(self):
        p=__import__("resume_profile").empty_profile()
        done=state({"type":"ControlType.Text","name":"Application Submitted"})
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}), \
             patch.object(runner.firefox_adapter,"select_tab",return_value={"ok":True,"selected_name":"Road Maintenance Specialist"}) as select_tab, \
             patch.object(runner.provider,"snapshot",return_value=done):
            first=runner.run(
                p,eng.EnginePolicy(),{},max_iterations=1,
                application_id="tab-session",
                browser_target={"tab_name":"Road Maintenance Specialist"},
            )
            saved=runner.sessions.load("tab-session")
            second=runner.run(
                p,eng.EnginePolicy(),{},max_iterations=1,
                application_id="tab-session",
            )
        self.assertEqual(first["status"],"done")
        self.assertEqual(second["status"],"done")
        self.assertEqual(second["iterations"],0)
        self.assertEqual(saved["browser_tab"],{"tab_name":"Road Maintenance Specialist"})
        # First run pins the tab and observes exact submission evidence.
        # Second run is terminal local state and must not touch Firefox.
        self.assertEqual(select_tab.call_count,1)

    def test_runner_fails_closed_when_browser_target_cannot_be_selected(self):
        p=__import__("resume_profile").empty_profile()
        with patch.object(runner.firefox_adapter,"select_tab",side_effect=RuntimeError("FIREFOX_TAB_MATCH_COUNT_0")), \
             patch.object(runner.provider,"snapshot") as snapshot:
            out=runner.run(
                p,eng.EnginePolicy(),{},max_iterations=1,
                browser_target={"contains":"missing-job"},
            )
        self.assertEqual(out["status"],"browser_target_failed")
        self.assertFalse(out["ok"])
        snapshot.assert_not_called()

    def test_runner_persists_exact_submission_completion(self):
        p=__import__("resume_profile").empty_profile()
        done=state({"type":"ControlType.Text","name":"Application Submitted"})
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}), \
             patch.object(runner.provider,"snapshot",return_value=done):
            out=runner.run(p,eng.EnginePolicy(),{},max_iterations=1,application_id="completed-app")
            saved=runner.sessions.load("completed-app")
        self.assertEqual(out["status"],"done")
        self.assertTrue(runner.sessions.is_completed(saved))
        self.assertEqual(saved["completion"]["evidence"],"Application Submitted")

    def test_runner_completed_session_short_circuits_without_browser_or_provider(self):
        p=__import__("resume_profile").empty_profile()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("completed-app")
            runner.sessions.mark_completed(s)
            runner.sessions.set_browser_tab(s,{"tab_name":"Old Workday Tab"})
            runner.sessions.save(s)
            with patch.object(runner.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(runner.provider,"snapshot") as snapshot:
                out=runner.run(p,eng.EnginePolicy(),{},max_iterations=1,application_id="completed-app")
        self.assertEqual(out["status"],"done")
        self.assertEqual(out["iterations"],0)
        self.assertIn("local session records verified application submission",out["decision"]["reason"])
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_manifest_fingerprint_mismatch_blocks_before_completed_short_circuit(self):
        p=__import__("resume_profile").empty_profile()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("manifest-completed-app")
            runner.sessions.bind_manifest_fingerprint(s,"a"*64)
            runner.sessions.mark_completed(s)
            runner.sessions.set_browser_tab(s,{"tab_name":"Old Workday Tab"})
            runner.sessions.save(s)
            with patch.object(runner.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(runner.provider,"snapshot") as snapshot:
                out=runner.run(
                    p,
                    eng.EnginePolicy(),
                    {},
                    max_iterations=1,
                    application_id="manifest-completed-app",
                    browser_target={"tab_name":"New Workday Tab"},
                    manifest_fingerprint="b"*64,
                )
        self.assertEqual(out["status"],"manifest_session_mismatch")
        self.assertFalse(out["ok"])
        self.assertEqual(out["iterations"],0)
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_matching_manifest_fingerprint_allows_completed_zero_touch_restart(self):
        p=__import__("resume_profile").empty_profile()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("manifest-completed-app")
            runner.sessions.bind_manifest_fingerprint(s,"a"*64)
            runner.sessions.mark_completed(s)
            runner.sessions.set_browser_tab(s,{"tab_name":"Old Workday Tab"})
            runner.sessions.save(s)
            with patch.object(runner.firefox_adapter,"select_tab") as select_tab, \
                 patch.object(runner.provider,"snapshot") as snapshot:
                out=runner.run(
                    p,
                    eng.EnginePolicy(),
                    {},
                    max_iterations=1,
                    application_id="manifest-completed-app",
                    manifest_fingerprint="a"*64,
                )
        self.assertEqual(out["status"],"done")
        self.assertEqual(out["iterations"],0)
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_manifest_fingerprint_binds_before_browser_target_is_persisted(self):
        p=__import__("resume_profile").empty_profile()
        blocked=state()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}), \
             patch.object(runner.firefox_adapter,"select_tab",return_value={"ok":True}) as select_tab, \
             patch.object(runner.provider,"snapshot",return_value=blocked):
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                application_id="manifest-new-app",
                browser_target={"tab_name":"New Workday Tab"},
                manifest_fingerprint="c"*64,
            )
            saved=runner.sessions.load("manifest-new-app")
        self.assertEqual(saved["manifest_fingerprint"],"c"*64)
        self.assertEqual(saved["browser_tab"],{"tab_name":"New Workday Tab"})
        self.assertEqual(select_tab.call_count,1)
        self.assertIn(out["status"],{"blocked","done","ready_to_submit","needs_reasoning","iteration_limit"})

    def test_live_binding_fingerprint_mismatch_fails_before_session_or_browser(self):
        p=__import__("resume_profile").empty_profile()
        with patch.object(runner.discovery,"validate_runtime_target") as validate_runtime, \
             patch.object(runner.sessions,"load") as session_load, \
             patch.object(runner.firefox_adapter,"select_tab") as select_tab, \
             patch.object(runner.provider,"snapshot") as snapshot:
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                application_id="bound-app",
                browser_target={"tab_name":"Target Job"},
                manifest_fingerprint="a"*64,
                browser_runtime_id="42.2",
                expected_manifest_fingerprint="b"*64,
            )
        self.assertEqual(out["status"],"live_binding_failed")
        self.assertEqual(out["iterations"],0)
        validate_runtime.assert_not_called()
        session_load.assert_not_called()
        select_tab.assert_not_called()
        snapshot.assert_not_called()

    def test_live_binding_wrong_runtime_tab_fails_before_session_or_provider(self):
        p=__import__("resume_profile").empty_profile()
        with patch.object(
            runner.discovery,
            "validate_runtime_target",
            side_effect=runner.discovery.DiscoveryError(
                "Firefox runtime-id target does not satisfy manifest browser target"
            ),
        ) as validate_runtime, \
             patch.object(runner.sessions,"load") as session_load, \
             patch.object(runner.provider,"snapshot") as snapshot:
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                application_id="bound-app",
                browser_target={"tab_name":"Target Job"},
                manifest_fingerprint="a"*64,
                browser_runtime_id="42.9",
                expected_manifest_fingerprint="a"*64,
            )
        self.assertEqual(out["status"],"live_binding_failed")
        validate_runtime.assert_called_once_with({"tab_name":"Target Job"},"42.9")
        session_load.assert_not_called()
        snapshot.assert_not_called()

    def test_valid_live_binding_pins_runtime_id_but_persists_semantic_target(self):
        p=__import__("resume_profile").empty_profile()
        blocked=state()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}), \
             patch.object(
                 runner.discovery,
                 "validate_runtime_target",
                 return_value={"runtime_id":"42.2","name":"Target Job"},
             ) as validate_runtime, \
             patch.object(
                 runner.firefox_adapter,
                 "select_tab",
                 return_value={"ok":True,"selected_name":"Target Job","runtime_id":"42.2"},
             ) as select_tab, \
             patch.object(runner.provider,"snapshot",return_value=blocked):
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                application_id="bound-app",
                browser_target={"tab_name":"Target Job"},
                manifest_fingerprint="a"*64,
                browser_runtime_id="42.2",
                expected_manifest_fingerprint="a"*64,
            )
            saved=runner.sessions.load("bound-app")
        self.assertEqual(out["status"],"blocked")
        validate_runtime.assert_called_once_with({"tab_name":"Target Job"},"42.2")
        select_tab.assert_called_once_with(runtime_id="42.2")
        self.assertEqual(saved["browser_tab"],{"tab_name":"Target Job"})
        self.assertNotIn("runtime_id",saved["browser_tab"])

    def test_noncompleted_session_reuses_persisted_browser_target(self):
        p=__import__("resume_profile").empty_profile()
        blocked=state()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("persisted-target-app")
            runner.sessions.set_browser_tab(s,{"tab_name":"Target Job"})
            runner.sessions.save(s)
            with patch.object(
                runner.firefox_adapter,
                "select_tab",
                return_value={"ok":True,"selected_name":"Target Job","runtime_id":"42.2"},
            ) as select_tab, \
                 patch.object(runner.provider,"snapshot",return_value=blocked):
                out=runner.run(
                    p,
                    eng.EnginePolicy(),
                    {},
                    max_iterations=1,
                    application_id="persisted-target-app",
                )
        self.assertEqual(out["status"],"blocked")
        select_tab.assert_called_once_with(tab_name="Target Job")

    def test_runner_does_not_checkpoint_generic_done_without_submission_text(self):
        p=__import__("resume_profile").empty_profile()
        review=state({"type":"ControlType.ListItem","name":"current step 6 of 6 Review"})
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}), \
             patch.object(runner.provider,"snapshot",return_value=review):
            out=runner.run(p,eng.EnginePolicy(),{},max_iterations=1,application_id="review-no-submit")
            saved=runner.sessions.load("review-no-submit")
        self.assertEqual(out["status"],"done")
        self.assertFalse(runner.sessions.is_completed(saved))
        self.assertIsNone(saved["completion"])

    def test_force_live_bypasses_completed_session_short_circuit(self):
        p=__import__("resume_profile").empty_profile()
        listing=state({"type":"ControlType.Button","name":"Apply","enabled":True,"offscreen":False})
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=runner.sessions.empty_session("completed-app")
            runner.sessions.mark_completed(s)
            runner.sessions.save(s)
            with patch.object(runner.provider,"snapshot",return_value=listing) as snapshot:
                out=runner.run(p,eng.EnginePolicy(),{},max_iterations=1,application_id="completed-app",force_live=True)
        self.assertEqual(out["status"],"blocked")
        snapshot.assert_called_once()

    def test_matching_rehearsal_fingerprint_allows_first_mutation(self):
        p=__import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        empty=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-A","name":"First Name","value":""},
        )
        filled=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-B","name":"First Name","value":"Jack"},
        )
        action=eng.plan(p,empty,eng.EnginePolicy(),{})["actions"][0]
        fingerprint=runner.rehearsal.action_fingerprint(action)
        with patch.object(
            runner.discovery,"validate_runtime_target",
            return_value={"runtime_id":"42.2","name":"Target Job"},
        ), patch.object(
            runner.firefox_adapter,"select_tab",
            return_value={"ok":True,"runtime_id":"42.2","selected_name":"Target Job"},
        ), patch.object(
            runner.provider,"snapshot",return_value=empty
        ), patch.object(
            runner.provider,"execute",return_value={"ok":True}
        ) as execute, patch.object(
            runner,"wait_for_verification",
            return_value=(filled,{"ok":True,"attempt":1,"reason":"value readback"}),
        ):
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                browser_target={"tab_name":"Target Job"},
                manifest_fingerprint="a"*64,
                browser_runtime_id="42.2",
                expected_manifest_fingerprint="a"*64,
                expected_first_mutation_fingerprint=fingerprint,
            )
        self.assertEqual(out["status"],"iteration_limit")
        self.assertEqual(out["history"][0]["rehearsal_gate"]["status"],"matched")
        execute.assert_called_once()

    def test_rehearsal_fingerprint_mismatch_blocks_before_provider_execute(self):
        p=__import__("resume_profile").empty_profile()
        p["identity"]["first_name"]="Jack"
        empty=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"first-A","name":"First Name","value":""},
        )
        with patch.object(
            runner.discovery,"validate_runtime_target",
            return_value={"runtime_id":"42.2","name":"Target Job"},
        ), patch.object(
            runner.firefox_adapter,"select_tab",
            return_value={"ok":True,"runtime_id":"42.2","selected_name":"Target Job"},
        ), patch.object(
            runner.provider,"snapshot",return_value=empty
        ), patch.object(runner.provider,"execute") as execute:
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                browser_target={"tab_name":"Target Job"},
                manifest_fingerprint="a"*64,
                browser_runtime_id="42.2",
                expected_manifest_fingerprint="a"*64,
                expected_first_mutation_fingerprint="0"*64,
            )
        self.assertEqual(out["status"],"rehearsal_mismatch")
        self.assertEqual(out["iterations"],1)
        self.assertEqual(out["history"][0]["rehearsal_gate"]["status"],"mismatch")
        execute.assert_not_called()

    def test_read_only_selector_probe_does_not_consume_rehearsal_gate(self):
        p=__import__("resume_profile").empty_profile()
        blank=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule-A","name":"Schedule","value":"",
             "group_path":["Availability","Application Questions"]},
        )
        context_for_fingerprint={
            "selector_options":{"Availability::Schedule":["Day","Night"]},
            "reasoned_answers":{"Availability::Schedule":"Night"},
        }
        mutation=eng.plan(p,blank,eng.EnginePolicy(),context_for_fingerprint)["actions"][0]
        fingerprint=runner.rehearsal.action_fingerprint(mutation)
        selected=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule-B","name":"Schedule","value":"Night",
             "selection":["Night"],"group_path":["Availability","Application Questions"]},
        )
        calls=[]
        def execute(action):
            calls.append(action["op"])
            if action["op"]=="inspect_options":
                return {
                    "ok":True,
                    "options":["Day","Night"],
                    "selection_unchanged":True,
                }
            return {"ok":True}
        config={"provider":"static","answers":{"Availability::Schedule":"Night"}}
        with patch.object(
            runner.discovery,"validate_runtime_target",
            return_value={"runtime_id":"42.2","name":"Target Job"},
        ), patch.object(
            runner.firefox_adapter,"select_tab",
            return_value={"ok":True,"runtime_id":"42.2","selected_name":"Target Job"},
        ), patch.object(
            runner.provider,"snapshot",side_effect=[blank,blank,blank]
        ), patch.object(
            runner.provider,"execute",side_effect=execute
        ), patch.object(
            runner,"wait_for_verification",
            return_value=(selected,{"ok":True,"attempt":1,"reason":"option selected"}),
        ):
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=3,
                reasoning_config=config,
                browser_target={"tab_name":"Target Job"},
                manifest_fingerprint="a"*64,
                browser_runtime_id="42.2",
                expected_manifest_fingerprint="a"*64,
                expected_first_mutation_fingerprint=fingerprint,
            )
        self.assertEqual(calls,["inspect_options","select_option"])
        self.assertEqual(
            out["history"][0]["rehearsal_gate"]["status"],
            "deferred_for_read_only_action",
        )
        self.assertEqual(out["history"][2]["rehearsal_gate"]["status"],"matched")

    def test_rehearsal_binding_requires_runtime_live_binding(self):
        p=__import__("resume_profile").empty_profile()
        with patch.object(runner.sessions,"load") as session_load, \
             patch.object(runner.provider,"snapshot") as snapshot:
            out=runner.run(
                p,
                eng.EnginePolicy(),
                {},
                max_iterations=1,
                expected_first_mutation_fingerprint="a"*64,
            )
        self.assertEqual(out["status"],"rehearsal_binding_failed")
        session_load.assert_not_called()
        snapshot.assert_not_called()

    def test_control_absent_verifier(self):
        s = state({"type":"ControlType.Text","name":"Application Submitted"})
        action={"op":"invoke","target":{"name":"Submit"},"verify":{"kind":"control_absent","name":"Submit"}}
        self.assertTrue(runner.verify_action(s,action)[0])


if __name__ == "__main__":
    unittest.main()
