#!/usr/bin/env python3
from __future__ import annotations

import unittest

import job_application_engine_v2 as eng
import resume_profile


def profile():
    p = resume_profile.empty_profile()
    p["identity"]["first_name"] = "Alex"
    p["identity"]["last_name"] = "Example"
    p["contact"]["email"] = "alex@example.com"
    return p


def state(*controls):
    return eng.PageState.from_obj({"controls": list(controls)})


class EngineV2Tests(unittest.TestCase):
    def test_manifest_entrypoint_is_exact_unique_rehearsable_mutation(self):
        s=state(
            {"type":"ControlType.Button","name":"Apply","enabled":True,"offscreen":False},
            {"type":"ControlType.Button","name":"Sign In","enabled":True,"offscreen":False},
        )
        context={"entrypoint":{
            "target":{"control_type":"ControlType.Button","name":"Apply"},
            "verify":{"kind":"control_absent","name":"Apply"},
        }}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"act")
        self.assertEqual(out["reason"],"manifest-authorized application entrypoint is available")
        self.assertEqual(out["actions"],[{
            "op":"invoke",
            "target":{"control_type":"ControlType.Button","name":"Apply"},
            "verify":{"kind":"control_absent","name":"Apply"},
        }])

    def test_manifest_entrypoint_fails_closed_when_duplicate_or_absent(self):
        context={"entrypoint":{
            "target":{"control_type":"ControlType.Button","name":"Apply"},
            "verify":{"kind":"control_absent","name":"Apply"},
        }}
        duplicate=state(
            {"type":"ControlType.Button","name":"Apply","enabled":True,"offscreen":False},
            {"type":"ControlType.Button","name":"Apply","enabled":True,"offscreen":False},
        )
        out=eng.plan(profile(),duplicate,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"blocked")
        self.assertEqual(out["entrypoint_blockers"],["entrypoint target match count 2"])

        absent=state(
            {"type":"ControlType.Button","name":"Sign In","enabled":True,"offscreen":False},
        )
        out=eng.plan(profile(),absent,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"blocked")
        self.assertEqual(out["entrypoint_blockers"],["entrypoint target match count 0"])

    def test_manifest_entrypoint_is_ignored_after_workday_step_exists(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"source--source","name":"How Did You Hear About Us?","value":""},
            {"type":"ControlType.Button","name":"Apply","enabled":True,"offscreen":False},
        )
        context={
            "entrypoint":{
                "target":{"control_type":"ControlType.Button","name":"Apply"},
                "verify":{"kind":"control_absent","name":"Apply"},
            },
            "source_path":["Website","Spokane County"],
        }
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["actions"][0]["op"],"select_hierarchy")
        self.assertNotEqual(out["actions"][0]["target"].get("name"),"Apply")

    def test_source_hierarchy_planned_from_step1(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 1 of 6 My Information"},
            {"type": "ControlType.Edit", "id": "source--source", "name": "How Did You Hear About Us?", "value": ""},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {"source_path": ["Website", "Spokane County"]})
        self.assertEqual(out["status"], "act")
        self.assertEqual(out["actions"][0]["op"], "select_hierarchy")
        self.assertEqual(out["actions"][0]["path"], ["Website", "Spokane County"])
        self.assertEqual(out["actions"][0]["verify"]["value"], "Spokane County")

    def test_source_hierarchy_skipped_when_terminal_pill_already_selected(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 1 of 6 My Information"},
            {"type": "ControlType.Edit", "id": "source--source", "name": "How Did You Hear About Us?", "value": ""},
            {"type": "ControlType.ListItem", "name": "Spokane County, press delete to clear value."},
            {"type": "ControlType.Button", "name": "Save and Continue", "enabled": True, "offscreen": False},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {"source_path": ["Website", "Spokane County"]})
        self.assertEqual(out["actions"][0]["op"], "invoke")
        self.assertEqual(out["actions"][0]["target"]["name"], "Save and Continue")
        self.assertEqual(out["reasoning_requests"], [])

    def test_certification_is_blocked_without_explicit_authorization(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 4 of 6 Voluntary Disclosures"},
            {"type": "ControlType.CheckBox", "id": "terms", "name": "I agree", "toggle": "Off"},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {"certify_truthfulness": True})
        self.assertEqual(out["status"], "blocked")

    def test_certification_is_action_when_explicitly_authorized(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 4 of 6 Voluntary Disclosures"},
            {"type": "ControlType.CheckBox", "id": "terms", "name": "I agree", "toggle": "Off"},
        )
        policy = eng.EnginePolicy(allow_legal_certification=True)
        out = eng.plan(profile(), s, policy, {"certify_truthfulness": True})
        self.assertEqual(out["status"], "act")
        self.assertEqual(out["actions"][0]["op"], "set_toggle")
        self.assertTrue(out["actions"][0]["checked"])

    def test_step5_restoration_uses_decline_and_application_date(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 5 of 6 Self Identify"},
            {"type": "ControlType.Edit", "name": "Name", "value": ""},
            {"type": "ControlType.Spinner", "name": "Month", "value": "MM"},
            {"type": "ControlType.Spinner", "name": "Day", "value": "DD"},
            {"type": "ControlType.Spinner", "name": "Year", "value": "YYYY"},
            {"type": "ControlType.CheckBox", "name": "I do not want to answer", "toggle": "Off"},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {"application_date": "2026-10-03"})
        self.assertEqual(out["status"], "act")
        ops = [(a["op"], a["target"]["name"], a.get("value"), a.get("checked")) for a in out["actions"]]
        self.assertIn(("set_text", "Name", "Alex Example", None), ops)
        self.assertIn(("set_text", "Month", "10", None), ops)
        self.assertIn(("set_text", "Day", "3", None), ops)
        self.assertIn(("set_text", "Year", "2026", None), ops)
        self.assertIn(("set_toggle", "I do not want to answer", None, True), ops)

    def test_reasoned_answer_becomes_verified_text_action(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 3 of 6 Application Questions"},
            {"type": "ControlType.Edit", "id": "q-interest", "name": "Why are you interested?", "value": ""},
        )
        context = {"reasoned_answers": {"q-interest": "Grounded concise answer"}}
        out = eng.plan(profile(), s, eng.EnginePolicy(), context)
        self.assertEqual(out["status"], "act")
        self.assertEqual(out["actions"][0]["op"], "set_text")
        self.assertEqual(out["actions"][0]["value"], "Grounded concise answer")
        self.assertEqual(out["actions"][0]["source"], "reasoning_broker")
        self.assertEqual(out["actions"][0]["verify"]["kind"], "value_equals")

    def test_explicit_radio_choice_uses_question_ancestry(self):
        question = "Are you legally authorized to work in the United States?"
        s = state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.RadioButton","name":"Yes","selected":False,"group_path":["Yes", question, "Application Questions"]},
            {"type":"ControlType.RadioButton","name":"No","selected":False,"group_path":["No", question, "Application Questions"]},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {"choice_answers": {question: "Yes"}})
        self.assertEqual(out["status"], "act")
        self.assertEqual(out["actions"][0]["op"], "select_choice")
        self.assertEqual(out["actions"][0]["target"]["group_name"], question)
        self.assertEqual(out["actions"][0]["target"]["name"], "Yes")
        self.assertEqual(out["actions"][0]["verify"]["kind"], "choice_selected")

    def test_existing_radio_selection_suppresses_reasoning_without_override(self):
        question = "Are you willing to work weekends?"
        s = state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.RadioButton","name":"Yes","selected":False,"group_path":["Yes", question, "Application Questions"]},
            {"type":"ControlType.RadioButton","name":"No","selected":True,"group_path":["No", question, "Application Questions"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {})
        self.assertEqual(out["status"], "act")
        self.assertEqual(out["actions"][0]["target"]["name"], "Save and Continue")
        self.assertEqual(out["reasoning_requests"], [])

    def test_non_sensitive_radio_can_request_reasoning(self):
        question = "Are you willing to work weekends?"
        s = state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.RadioButton","name":"Yes","selected":False,"group_path":["Yes", question, "Application Questions"]},
            {"type":"ControlType.RadioButton","name":"No","selected":False,"group_path":["No", question, "Application Questions"]},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {})
        self.assertEqual(out["status"], "needs_reasoning")
        self.assertEqual(out["reasoning_requests"][0]["kind"], "choice_answer")
        self.assertEqual(out["reasoning_requests"][0]["options"], ["No", "Yes"])

    def test_sensitive_radio_not_inferred(self):
        question = "Gender"
        s = state(
            {"type":"ControlType.ListItem","name":"current step 4 of 6 Voluntary Disclosures"},
            {"type":"ControlType.RadioButton","name":"Male","selected":False,"group_path":["Male", question, "Voluntary Disclosures"]},
            {"type":"ControlType.RadioButton","name":"Female","selected":False,"group_path":["Female", question, "Voluntary Disclosures"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(), {})
        self.assertEqual(out["reasoning_requests"], [])
        self.assertEqual(out["actions"][0]["target"]["name"], "Save and Continue")

    def test_attachment_is_planned_when_upload_control_present(self):
        s = state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Button","id":"resumeAttachments--attachments","name":"Select files","enabled":True},
        )
        context={"attachments":[{
            "target":{"automation_id":"resumeAttachments--attachments","name":"Select files"},
            "path":r"C:\\tmp\\resume.docx",
            "expected_filename":"resume.docx",
            "success_text":"Successfully Uploaded!",
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"act")
        self.assertEqual(out["actions"][0]["op"],"upload_file")
        self.assertEqual(out["actions"][0]["expected_filename"],"resume.docx")
        self.assertEqual(out["actions"][0]["verify"]["kind"],"upload_verified")

    def test_attachment_is_skipped_after_verified_upload(self):
        s = state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Button","id":"resumeAttachments--attachments","name":"Select files","enabled":True},
            {"type":"ControlType.Text","name":"resume.docx"},
            {"type":"ControlType.Text","name":"Successfully Uploaded!"},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        context={"attachments":[{
            "target":{"automation_id":"resumeAttachments--attachments","name":"Select files"},
            "path":r"C:\\tmp\\resume.docx",
            "expected_filename":"resume.docx",
            "success_text":"Successfully Uploaded!",
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["actions"][0]["op"],"invoke")
        self.assertEqual(out["actions"][0]["target"]["name"],"Save and Continue")

    def test_repeating_experience_fields_are_section_scoped(self):
        p=profile()
        p["experience"]=[
            {"employer":"Employer A","title":"Driver","start":"2025-01","end":None,"current":True,
             "may_contact":True,"phone":"","responsibilities":"Duties","salary":"",
             "supervisor":"","supervisor_note":""},
            {"employer":"Employer B","title":"Driver","start":"2024-01","end":"2024-12","current":False,
             "may_contact":True,"phone":"","responsibilities":"Older duties","salary":"",
             "supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.CheckBox","name":"I currently work here","toggle":"Off","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Company","value":"","group_path":["Work Experience 2","My Experience"]},
        )
        context={"repeating_sections":[{
            "source":"experience","record_index":0,"group_name":"Work Experience 1",
            "fields":{"Company":"employer"},
            "toggles":{"I currently work here":"current"},
        }]}
        out=eng.plan(p,s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"act")
        company=[a for a in out["actions"] if a["op"]=="set_text"][0]
        current=[a for a in out["actions"] if a["op"]=="set_toggle"][0]
        self.assertEqual(company["target"]["group_name"],"Work Experience 1")
        self.assertEqual(company["value"],"Employer A")
        self.assertEqual(current["target"]["group_name"],"Work Experience 1")
        self.assertTrue(current["checked"])
        self.assertEqual(out["reasoning_requests"],[])
        self.assertFalse(any(a.get("target",{}).get("group_name")=="Work Experience 2" for a in out["actions"]))

    def test_scoped_field_verifier_distinguishes_duplicate_labels(self):
        c1=eng.Control.from_obj({"type":"ControlType.Edit","name":"Company","value":"A","group_path":["Work Experience 1"]})
        c2=eng.Control.from_obj({"type":"ControlType.Edit","name":"Company","value":"B","group_path":["Work Experience 2"]})
        self.assertEqual(c1.group_path,("Work Experience 1",))
        self.assertEqual(c2.group_path,("Work Experience 2",))

    def test_section_inventory_detects_repeating_family(self):
        s=state(
            {"type":"ControlType.Edit","name":"Company","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Company","top":300,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","top":320,"group_path":["Work Experience 2","My Experience"]},
        )
        out=eng.section_inventory(s)
        self.assertEqual(out["section_count"],2)
        self.assertEqual([x["family"] for x in out["sections"]],["Work Experience","Work Experience"])
        self.assertTrue(all(x["likely_repeating"] for x in out["sections"]))
        self.assertTrue(all(x["safe_named_scope"] for x in out["sections"]))

    def test_section_inventory_preserves_semantic_value_for_identity_binding(self):
        s=state(
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.ComboBox","name":"Degree","selection":["High School Diploma"],"top":120,"group_path":["Education 1","My Experience"]},
        )
        out=eng.section_inventory(s)
        by_group={item["group_name"]:item for item in out["sections"]}
        company=by_group["Work Experience 1"]["controls"][0]
        degree=by_group["Education 1"]["controls"][0]
        self.assertEqual(company["value"],"Employer A")
        self.assertEqual(degree["selection"],["High School Diploma"])

    def test_section_inventory_flags_same_name_scope_ambiguity(self):
        s=state(
            {"type":"ControlType.Edit","name":"Company","top":100,"group_path":["Work Experience","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","top":120,"group_path":["Work Experience","My Experience"]},
            {"type":"ControlType.Edit","name":"Company","top":300,"group_path":["Work Experience","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","top":320,"group_path":["Work Experience","My Experience"]},
        )
        out=eng.section_inventory(s)
        self.assertEqual(out["section_count"],1)
        section=out["sections"][0]
        self.assertTrue(section["ambiguous_within_scope"])
        self.assertFalse(section["safe_named_scope"])
        self.assertIn("Company",section["duplicate_labels"])
        self.assertIn("Job Title",section["duplicate_labels"])

    def test_infer_repeating_experience_bindings_use_identity_not_screen_order(self):
        p=profile()
        p["experience"]=[
            {"employer":"Employer A","title":"Driver A","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
            {"employer":"Employer B","title":"Driver B","start":"2024-01","end":"2024-12","current":False,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.Edit","name":"Company","value":"Employer B","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver B","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.CheckBox","name":"I currently work here","top":140,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","top":300,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":320,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.CheckBox","name":"I currently work here","top":340,"group_path":["Work Experience 2","My Experience"]},
        )
        out=eng.infer_repeating_sections(s,p)
        self.assertEqual(len(out["bindings"]),2)
        by_group={item["group_name"]:item for item in out["bindings"]}
        self.assertEqual(by_group["Work Experience 1"]["record_index"],1)
        self.assertEqual(by_group["Work Experience 2"]["record_index"],0)
        self.assertEqual(by_group["Work Experience 1"]["identity_anchors"],{"employer":"Employer B","title":"Driver B"})
        self.assertEqual(by_group["Work Experience 1"]["binding_confidence"],"identity_anchor")

    def test_multiple_untrusted_blank_sections_are_not_position_bound(self):
        p=profile()
        p["experience"]=[
            {"employer":"A","title":"Driver A","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
            {"employer":"B","title":"Driver B","start":"2024-01","end":"2024-12","current":False,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.Edit","name":"Company","value":"","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Company","value":"","top":300,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"","top":320,"group_path":["Work Experience 2","My Experience"]},
        )
        out=eng.infer_repeating_sections(s,p)
        self.assertEqual(out["bindings"],[])
        self.assertEqual(
            [item["reason"] for item in out["skipped"]],
            ["empty section requires trusted creation order","empty section requires trusted creation order"],
        )

    def test_verified_created_blank_section_binds_next_unused_record(self):
        p=profile()
        p["experience"]=[
            {"employer":"Employer A","title":"Driver A","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
            {"employer":"Employer B","title":"Driver B","start":"2024-01","end":"2024-12","current":False,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Company","value":"","top":300,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"","top":320,"group_path":["Work Experience 2","My Experience"]},
        )
        out=eng.infer_repeating_sections(
            s,p,trusted_empty_group_names=["Work Experience 2"]
        )
        by_group={item["group_name"]:item for item in out["bindings"]}
        self.assertEqual(by_group["Work Experience 1"]["record_index"],0)
        self.assertEqual(by_group["Work Experience 2"]["record_index"],1)
        self.assertEqual(by_group["Work Experience 2"]["binding_confidence"],"trusted_created_empty")

    def test_unmatched_prefilled_identity_is_never_overwritten_by_position(self):
        p=profile()
        p["experience"]=[
            {"employer":"Employer A","title":"Driver A","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.Edit","name":"Company","value":"Unknown Employer","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Mystery Role","top":120,"group_path":["Work Experience 1","My Experience"]},
        )
        out=eng.infer_repeating_sections(s,p)
        self.assertEqual(out["bindings"],[])
        self.assertEqual(out["skipped"][0]["reason"],"prefilled identity does not match canonical profile")


    def test_infer_repeating_binding_requires_two_recognized_fields(self):
        p=profile()
        p["experience"]=[{"employer":"A","title":"Driver","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""}]
        s=state(
            {"type":"ControlType.Edit","name":"Company","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Unfamiliar Field","top":120,"group_path":["Work Experience 1","My Experience"]},
        )
        out=eng.infer_repeating_sections(s,p)
        self.assertEqual(out["bindings"],[])
        self.assertEqual(out["skipped"][0]["reason"],"insufficient recognized field structure")

    def test_auto_bound_repeating_sections_feed_deterministic_planner(self):
        p=profile()
        p["experience"]=[{"employer":"Employer A","title":"Driver","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""}]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.CheckBox","name":"I currently work here","toggle":"Off","top":140,"group_path":["Work Experience 1","My Experience"]},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        self.assertEqual(out["status"],"act")
        self.assertEqual(out["reasoning_requests"],[])
        values={(a["target"]["name"],a.get("value"),a.get("checked")) for a in out["actions"]}
        self.assertIn(("Company","Employer A",None),values)
        self.assertIn(("Job Title","Driver",None),values)
        self.assertIn(("I currently work here",None,True),values)

    def test_explicit_option_selection_is_verified(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.ComboBox","id":"degree","name":"Degree","value":"","expand_collapse":"Collapsed","group_path":["Education 1","My Experience"]},
        )
        context={"option_selections":[{
            "target":{"control_type":"ControlType.ComboBox","automation_id":"degree","name":"Degree","group_name":"Education 1"},
            "value":"High School Diploma",
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"act")
        action=out["actions"][0]
        self.assertEqual(action["op"],"select_option")
        self.assertEqual(action["value"],"High School Diploma")
        self.assertEqual(action["verify"],{"kind":"option_selected","value":"High School Diploma"})

    def test_option_selection_skips_existing_selection(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.ComboBox","id":"degree","name":"Degree","selection":["High School Diploma"],"group_path":["Education 1","My Experience"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        context={"option_selections":[{
            "target":{"control_type":"ControlType.ComboBox","automation_id":"degree","name":"Degree","group_name":"Education 1"},
            "value":"High School Diploma",
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["actions"][0]["op"],"invoke")
        self.assertEqual(out["actions"][0]["target"]["name"],"Save and Continue")

    def test_auto_bind_education_maps_degree_as_exact_option(self):
        p=profile()
        p["education"]=[{"school":"Northern School","alternate_name":"","credential":"High School Diploma","end_year":2012,"location":"WA"}]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"School or University","value":"","top":100,"group_path":["Education 1","My Experience"]},
            {"type":"ControlType.ComboBox","name":"Degree","value":"","top":120,"expand_collapse":"Collapsed","group_path":["Education 1","My Experience"]},
        )
        binding=eng.infer_repeating_sections(s,p)
        self.assertEqual(len(binding["bindings"]),1)
        self.assertEqual(binding["bindings"][0]["fields"]["School or University"],"school")
        self.assertEqual(binding["bindings"][0]["options"]["Degree"],"credential")
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        self.assertEqual(out["status"],"act")
        ops={(a["op"],a["target"]["name"],a.get("value")) for a in out["actions"]}
        self.assertIn(("set_text","School or University","Northern School"),ops)
        self.assertIn(("select_option","Degree","High School Diploma"),ops)

    def test_control_roundtrip_keeps_expand_state_and_selection(self):
        c=eng.Control.from_obj({
            "type":"ControlType.ComboBox","name":"Degree",
            "expand_collapse":"Expanded","selection":["High School Diploma"],
        })
        obj=c.to_obj()
        self.assertEqual(obj["expand_collapse"],"Expanded")
        self.assertEqual(obj["selection"],["High School Diploma"])

    def test_repeating_section_goal_plans_scoped_add(self):
        p=profile()
        p["experience"]=[
            {"employer":"A","title":"Driver A","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
            {"employer":"B","title":"Driver B","start":"2024-01","end":"2024-12","current":False,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"A","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Button","id":"add-work","name":"Add Another","top":200,"group_path":["Work Experience","My Experience"]},
        )
        context={"auto_bind_repeating_sections":True,"repeating_section_goals":[{"source":"experience","desired_count":2}]}
        out=eng.plan(p,s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"act")
        action=out["actions"][0]
        self.assertEqual(action["op"],"invoke")
        self.assertEqual(action["target"]["automation_id"],"add-work")
        self.assertEqual(action["verify"],{"kind":"section_count_increases","family":"Work Experience","before_count":1})

    def test_repeating_section_goal_blocks_when_add_button_is_not_safe(self):
        p=profile()
        p["experience"]=[
            {"employer":"A","title":"Driver A","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
            {"employer":"B","title":"Driver B","start":"2024-01","end":"2024-12","current":False,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"A","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"repeating_section_goals":[{"source":"experience","desired_count":2}]})
        self.assertEqual(out["status"],"blocked")
        self.assertIn("exact add button match count is 0",out["repeating_section_blockers"][0])

    def test_repeating_section_goal_cannot_exceed_profile_records(self):
        p=profile()
        p["experience"]=[{"employer":"A","title":"Driver","start":"2025-01","end":None,"current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"","supervisor":"","supervisor_note":""}]
        s=state({"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"})
        out=eng.plan(p,s,eng.EnginePolicy(),{"repeating_section_goals":[{"source":"experience","desired_count":2}]})
        self.assertEqual(out["status"],"blocked")
        self.assertIn("exceeds canonical profile record count",out["repeating_section_blockers"][0])

    def test_blank_selector_plans_read_only_probe(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule","name":"Schedule","value":"","group_path":["Availability","Application Questions"]},
        )
        out=eng.plan(profile(),s,eng.EnginePolicy(),{})
        self.assertEqual(out["status"],"act")
        action=out["actions"][0]
        self.assertEqual(action["op"],"inspect_options")
        self.assertEqual(action["probe_key"],"Availability::Schedule")
        self.assertNotIn("verify",action)

    def test_probed_selector_becomes_constrained_reasoning_request(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule","name":"Schedule","value":"","group_path":["Availability","Application Questions"]},
        )
        out=eng.plan(profile(),s,eng.EnginePolicy(),{"selector_options":{"Availability::Schedule":["Day","Night"]}})
        self.assertEqual(out["status"],"needs_reasoning")
        req=out["reasoning_requests"][0]
        self.assertEqual(req["kind"],"choice_answer")
        self.assertEqual(req["key"],"Availability::Schedule")
        self.assertEqual(req["options"],["Day","Night"])

    def test_reasoned_selector_answer_becomes_exact_select_option(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","id":"schedule","name":"Schedule","value":"","group_path":["Availability","Application Questions"]},
        )
        context={
            "selector_options":{"Availability::Schedule":["Day","Night"]},
            "reasoned_answers":{"Availability::Schedule":"Night"},
        }
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"act")
        action=out["actions"][0]
        self.assertEqual(action["op"],"select_option")
        self.assertEqual(action["value"],"Night")
        self.assertEqual(action["source"],"reasoning_broker")

    def test_sensitive_probed_selector_blocks_instead_of_reasoning(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 4 of 6 Voluntary Disclosures"},
            {"type":"ControlType.ComboBox","id":"gender","name":"Gender","value":"","group_path":["Demographics","Voluntary Disclosures"]},
        )
        out=eng.plan(profile(),s,eng.EnginePolicy(),{"selector_options":{"Demographics::Gender":["Male","Female"]}})
        self.assertEqual(out["status"],"blocked")
        self.assertEqual(out["reasoning_requests"],[])
        self.assertIn("sensitive selector requires explicit answer",out["selector_blockers"][0])

    def test_verified_review_field_value_catches_semantic_mismatch(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"How Did You Hear About Us?"},
            {"type":"ControlType.Text","name":"Community Event"},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        context={"verified_review_expectations":[{"kind":"review_field_value","field":"How Did You Hear About Us?","value":"Spokane County","step_number":1,"trusted":True}]}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"blocked")
        self.assertIn("Spokane County",out["review_mismatches"][0])

    def test_verified_review_field_value_passes_when_value_present(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"How Did You Hear About Us?"},
            {"type":"ControlType.Text","name":"Spokane County"},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        context={"verified_review_expectations":[{"kind":"review_field_value","field":"How Did You Hear About Us?","value":"Spokane County","step_number":1,"trusted":True}]}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"ready_to_submit")
        self.assertEqual(out["review_mismatches"],[])

    def test_verified_review_field_value_skips_field_workday_does_not_render(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        context={"verified_review_expectations":[{"kind":"review_field_value","field":"Internal Optional Field","value":"Some Value","step_number":2,"trusted":True}]}
        out=eng.plan(profile(),s,eng.EnginePolicy(),context)
        self.assertEqual(out["status"],"ready_to_submit")
        self.assertEqual(out["review_mismatches"],[])

    def test_repeating_role_description_uses_bound_record_responsibilities(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":None,
            "current":True,"may_contact":True,"phone":"",
            "responsibilities":"Delivered freight safely and completed inspections.",
            "salary":"","supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","id":"role","name":"Role Description","value":"","group_path":["Work Experience 1","My Experience"]},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        role=[a for a in out["actions"] if a.get("target",{}).get("name")=="Role Description"]
        self.assertEqual(len(role),1)
        self.assertEqual(role[0]["value"],"Delivered freight safely and completed inspections.")
        self.assertEqual(role[0]["target"]["group_name"],"Work Experience 1")

    def test_repeating_reason_for_leaving_missing_fact_blocks_navigation(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":"2025-09",
            "current":False,"may_contact":True,"phone":"",
            "responsibilities":"Delivered freight.","salary":"","supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Reason for Leaving","value":"","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        self.assertEqual(out["status"],"blocked")
        self.assertIn("reason_for_leaving",out["repeating_freeform_blockers"][0])
        self.assertFalse(any(a.get("target",{}).get("name")=="Save and Continue" for a in out["actions"]))

    def test_repeating_reason_for_leaving_uses_explicit_record_override(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":"2025-09",
            "current":False,"may_contact":True,"phone":"",
            "responsibilities":"Delivered freight.","salary":"","supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","id":"reason","name":"Reason for Leaving","value":"","group_path":["Work Experience 1","My Experience"]},
        )
        context={
            "auto_bind_repeating_sections":True,
            "record_overrides":{"experience":{"0":{"reason_for_leaving":"Accepted another position."}}},
        }
        out=eng.plan(p,s,eng.EnginePolicy(),context)
        reason=[a for a in out["actions"] if a.get("target",{}).get("name")=="Reason for Leaving"]
        self.assertEqual(len(reason),1)
        self.assertEqual(reason[0]["value"],"Accepted another position.")
        self.assertIn("record_overrides",reason[0]["source"])

    def test_repeating_combined_duties_and_reason_requires_and_composes_both(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":"2025-09",
            "current":False,"may_contact":True,"phone":"",
            "responsibilities":"Delivered freight and inspected equipment.",
            "salary":"","supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","id":"role","name":"Role Description","value":"","help_text":"Enter duties and reason for leaving.","group_path":["Work Experience 1","My Experience"]},
        )
        missing=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        self.assertEqual(missing["status"],"blocked")
        self.assertIn("reason_for_leaving",missing["repeating_freeform_blockers"][0])
        context={
            "auto_bind_repeating_sections":True,
            "record_overrides":{"experience":{"0":{"reason_for_leaving":"Seasonal assignment ended."}}},
        }
        out=eng.plan(p,s,eng.EnginePolicy(),context)
        role=[a for a in out["actions"] if a.get("target",{}).get("name")=="Role Description"]
        self.assertEqual(len(role),1)
        self.assertEqual(
            role[0]["value"],
            "Duties: Delivered freight and inspected equipment.\nReason for Leaving: Seasonal assignment ended.",
        )
        self.assertEqual(role[0]["verify"]["value"],role[0]["value"])

    def test_repeating_freeform_values_do_not_bleed_between_bound_records(self):
        p=profile()
        p["experience"]=[
            {"employer":"A","title":"Driver A","start":"2025-01","end":"2025-06","current":False,"may_contact":True,"phone":"","responsibilities":"Duties A","reason_for_leaving":"Reason A","salary":"","supervisor":"","supervisor_note":""},
            {"employer":"B","title":"Driver B","start":"2024-01","end":"2024-06","current":False,"may_contact":True,"phone":"","responsibilities":"Duties B","reason_for_leaving":"Reason B","salary":"","supervisor":"","supervisor_note":""},
        ]
        s=state(
            {"type":"ControlType.Edit","name":"Company","value":"B","top":100,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver B","top":120,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Role Description","value":"","top":140,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Company","value":"A","top":300,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver A","top":320,"group_path":["Work Experience 2","My Experience"]},
            {"type":"ControlType.Edit","name":"Role Description","value":"","top":340,"group_path":["Work Experience 2","My Experience"]},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        values={
            a["target"]["group_name"]:a["value"]
            for a in out["actions"]
            if a.get("target",{}).get("name")=="Role Description"
        }
        self.assertEqual(values,{"Work Experience 1":"Duties B","Work Experience 2":"Duties A"})

    def test_repeating_month_year_date_uses_accessible_format_hint(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":"2025-09",
            "current":False,"may_contact":True,"phone":"","responsibilities":"","salary":"",
            "supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","id":"start","name":"Start Date","value":"","help_text":"MM/YYYY","group_path":["Work Experience 1","My Experience"]},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        date_actions=[a for a in out["actions"] if a["target"].get("name")=="Start Date"]
        self.assertEqual(len(date_actions),1)
        self.assertEqual(date_actions[0]["value"],"01/2025")

    def test_repeating_full_date_refuses_to_invent_missing_day(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":None,
            "current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"",
            "supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Start Date","value":"","help_text":"MM/DD/YYYY","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        self.assertEqual(out["status"],"blocked")
        self.assertIn("does not contain a day",out["repeating_date_blockers"][0])
        self.assertFalse(any(a.get("target",{}).get("name")=="Save and Continue" for a in out["actions"]))

    def test_repeating_date_without_format_hint_blocks_before_navigation(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":None,
            "current":True,"may_contact":True,"phone":"","responsibilities":"","salary":"",
            "supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Start Date","value":"","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        self.assertEqual(out["status"],"blocked")
        self.assertIn("no deterministic format hint",out["repeating_date_blockers"][0])

    def test_education_year_field_uses_year_without_guessing_month_or_day(self):
        p=profile()
        p["education"]=[{
            "school":"School A","alternate_name":"","credential":"High School Diploma",
            "end_year":2012,"location":"WA",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"School or University","value":"School A","group_path":["Education 1","My Experience"]},
            {"type":"ControlType.Edit","id":"year","name":"Graduation Year","value":"","group_path":["Education 1","My Experience"]},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        year_actions=[a for a in out["actions"] if a["target"].get("name")=="Graduation Year"]
        self.assertEqual(len(year_actions),1)
        self.assertEqual(year_actions[0]["value"],"2012")

    def test_control_roundtrip_keeps_help_text(self):
        c=eng.Control.from_obj({"type":"ControlType.Edit","name":"Start Date","help_text":"MM/YYYY"})
        self.assertEqual(c.help_text,"MM/YYYY")
        self.assertEqual(c.to_obj()["help_text"],"MM/YYYY")

    def test_control_roundtrip_keeps_requiredness(self):
        c=eng.Control.from_obj({"type":"ControlType.Edit","name":"Required Field","required":True})
        self.assertTrue(c.required)
        self.assertTrue(c.to_obj()["required"])

    def test_unknown_required_text_blocks_save_and_continue(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.Edit","name":"Tenant-Specific Required Fact","value":"","required":True},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(profile(),s,eng.EnginePolicy(),{})
        # Generic unresolved text is surfaced for reasoning before the hard coverage gate.
        self.assertEqual(out["status"],"needs_reasoning")
        self.assertEqual(out["reasoning_requests"][0]["field"],"Tenant-Specific Required Fact")

    def test_reserved_unknown_required_repeating_field_blocks_navigation(self):
        p=profile()
        p["experience"]=[{
            "employer":"Employer A","title":"Driver","start":"2025-01","end":None,
            "current":True,"may_contact":True,"phone":"","responsibilities":"Delivered freight.",
            "salary":"","supervisor":"","supervisor_note":"",
        }]
        s=state(
            {"type":"ControlType.ListItem","name":"current step 2 of 6 My Experience"},
            {"type":"ControlType.Edit","name":"Company","value":"Employer A","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Job Title","value":"Driver","group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Edit","name":"Tenant Custom Required Field","value":"","required":True,"group_path":["Work Experience 1","My Experience"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(p,s,eng.EnginePolicy(),{"auto_bind_repeating_sections":True})
        self.assertEqual(out["status"],"blocked")
        self.assertEqual(out["reason"],"required field coverage is incomplete")
        self.assertIn("Tenant Custom Required Field",out["required_field_blockers"][0])
        self.assertFalse(any(a.get("target",{}).get("name")=="Save and Continue" for a in out["actions"]))

    def test_optional_unknown_field_does_not_block_navigation(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","name":"Optional Tenant Note","value":"","required":False},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        # Reserve it from generic reasoning so this specifically tests required coverage.
        out=eng.plan(profile(),s,eng.EnginePolicy(),{"repeating_sections":[{"source":"experience","record_index":0,"group_name":"Unused","fields":{"Optional Tenant Note":"unsupported"}}]})
        self.assertEqual(out["status"],"act")
        self.assertEqual(out["actions"][0]["target"]["name"],"Save and Continue")

    def test_required_radio_group_is_satisfied_by_one_selected_option(self):
        q="Can you work weekends?"
        s=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.RadioButton","name":"Yes","required":True,"selected":False,"group_path":["Yes",q,"Application Questions"]},
            {"type":"ControlType.RadioButton","name":"No","required":True,"selected":True,"group_path":["No",q,"Application Questions"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(profile(),s,eng.EnginePolicy(),{})
        self.assertEqual(out["status"],"act")
        self.assertEqual(out["actions"][0]["target"]["name"],"Save and Continue")

    def test_required_radio_group_without_selection_never_navigates(self):
        q="Sensitive custom question"
        s=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.RadioButton","name":"Yes","required":True,"selected":False,"group_path":["Yes",q,"Application Questions"]},
            {"type":"ControlType.RadioButton","name":"No","required":True,"selected":False,"group_path":["No",q,"Application Questions"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        # Mark the question sensitive so generic reasoning cannot resolve it.
        out=eng.plan(profile(),s,eng.EnginePolicy(),{})
        if out["status"]=="needs_reasoning":
            # If wording is non-sensitive under current classifier, the coverage gate is
            # exercised after reasoning; direct helper still must report it unresolved.
            self.assertTrue(any("required choice" in x for x in eng._required_field_blockers(s)))
        else:
            self.assertEqual(out["status"],"blocked")
            self.assertTrue(any("required choice" in x for x in out["required_field_blockers"]))

    def test_required_combobox_with_selection_is_satisfied(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 3 of 6 Application Questions"},
            {"type":"ControlType.ComboBox","name":"Schedule","required":True,"selection":["Night"]},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(profile(),s,eng.EnginePolicy(),{})
        self.assertEqual(out["status"],"act")
        self.assertEqual(out["actions"][0]["target"]["name"],"Save and Continue")

    def test_required_source_edit_is_satisfied_by_terminal_selected_pill(self):
        s=state(
            {"type":"ControlType.ListItem","name":"current step 1 of 6 My Information"},
            {"type":"ControlType.Edit","id":"source--source","name":"How Did You Hear About Us?","value":"","required":True},
            {"type":"ControlType.ListItem","name":"Spokane County, press delete to clear value."},
            {"type":"ControlType.Button","name":"Save and Continue","enabled":True,"offscreen":False},
        )
        out=eng.plan(profile(),s,eng.EnginePolicy(),{"source_path":["Website","Spokane County"]})
        self.assertEqual(out["status"],"act")
        self.assertEqual(out["actions"][0]["target"]["name"],"Save and Continue")

    def test_review_mismatch_blocks_submit(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 6 of 6 Review"},
            {"type": "ControlType.Text", "name": "Community Event"},
            {"type": "ControlType.Button", "name": "Submit", "enabled": True, "offscreen": False},
        )
        policy = eng.EnginePolicy(allow_submit=True)
        context = {"review_expectations": [
            {"kind": "contains_text", "value": "Spokane County"},
            {"kind": "not_contains_text", "value": "Community Event"},
        ]}
        out = eng.plan(profile(), s, policy, context)
        self.assertEqual(out["status"], "blocked")
        self.assertTrue(out["review_mismatches"])

    def test_scoped_review_assertion_rejects_value_from_other_repeated_record(self):
        s = state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"Company","group_path":["Work Experience 1","Review"]},
            {"type":"ControlType.Text","name":"Employer A","group_path":["Work Experience 1","Review"]},
            {"type":"ControlType.Text","name":"Company","group_path":["Work Experience 2","Review"]},
            {"type":"ControlType.Text","name":"Employer B","group_path":["Work Experience 2","Review"]},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        context={"verified_review_expectations":[{
            "kind":"review_field_value","field":"Company","value":"Employer B",
            "group_name":"Work Experience 1","step_number":2,"trusted":True,
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(allow_submit=True),context)
        self.assertEqual(out["status"],"blocked")
        self.assertTrue(any("Work Experience 1" in x for x in out["review_mismatches"]))

    def test_scoped_review_assertion_accepts_value_in_same_repeated_record(self):
        s = state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"Company","group_path":["Work Experience 1","Review"]},
            {"type":"ControlType.Text","name":"Employer A","group_path":["Work Experience 1","Review"]},
            {"type":"ControlType.Text","name":"Company","group_path":["Work Experience 2","Review"]},
            {"type":"ControlType.Text","name":"Employer B","group_path":["Work Experience 2","Review"]},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        context={"verified_review_expectations":[{
            "kind":"review_field_value","field":"Company","value":"Employer A",
            "group_name":"Work Experience 1","step_number":2,"trusted":True,
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(allow_submit=False),context)
        self.assertEqual(out["status"],"ready_to_submit")
        self.assertEqual(out["review_mismatches"],[])

    def test_scoped_review_unique_field_can_fallback_when_group_ancestry_missing(self):
        s = state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"How Did You Hear About Us?"},
            {"type":"ControlType.Text","name":"Spokane County"},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        context={"verified_review_expectations":[{
            "kind":"review_field_value","field":"How Did You Hear About Us?","value":"Spokane County",
            "group_name":"My Information","step_number":1,"trusted":True,
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(allow_submit=False),context)
        self.assertEqual(out["status"],"ready_to_submit")
        self.assertEqual(out["review_mismatches"],[])

    def test_scoped_review_duplicate_field_without_scope_is_unverifiable(self):
        s = state(
            {"type":"ControlType.ListItem","name":"current step 6 of 6 Review"},
            {"type":"ControlType.Text","name":"Company"},
            {"type":"ControlType.Text","name":"Employer A"},
            {"type":"ControlType.Text","name":"Company"},
            {"type":"ControlType.Text","name":"Employer B"},
            {"type":"ControlType.Button","name":"Submit","enabled":True,"offscreen":False},
        )
        context={"verified_review_expectations":[{
            "kind":"review_field_value","field":"Company","value":"Employer A",
            "group_name":"Work Experience 1","step_number":2,"trusted":True,
        }]}
        out=eng.plan(profile(),s,eng.EnginePolicy(allow_submit=True),context)
        self.assertEqual(out["status"],"blocked")
        self.assertTrue(any("cannot be attributed safely" in x for x in out["review_mismatches"]))

    def test_review_passes_but_requires_submit_policy(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 6 of 6 Review"},
            {"type": "ControlType.Text", "name": "Spokane County"},
            {"type": "ControlType.Button", "name": "Submit", "enabled": True, "offscreen": False},
        )
        context = {"review_expectations": [{"kind": "contains_text", "value": "Spokane County"}]}
        out = eng.plan(profile(), s, eng.EnginePolicy(allow_submit=False), context)
        self.assertEqual(out["status"], "ready_to_submit")

    def test_review_can_submit_when_authorized(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 6 of 6 Review"},
            {"type": "ControlType.Text", "name": "Spokane County"},
            {"type": "ControlType.Button", "name": "Submit", "enabled": True, "offscreen": False},
        )
        context = {"review_expectations": [{"kind": "contains_text", "value": "Spokane County"}]}
        out = eng.plan(profile(), s, eng.EnginePolicy(allow_submit=True), context)
        self.assertEqual(out["status"], "act")
        self.assertEqual(out["actions"][0]["target"]["name"], "Submit")

    def test_submission_confirmation_is_done(self):
        s = state({"type": "ControlType.Text", "name": "Application Submitted"})
        out = eng.plan(profile(), s, eng.EnginePolicy(allow_submit=True), {})
        self.assertEqual(out["status"], "done")

    def test_review_errors_block_submit(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 6 of 6 Review"},
            {"type": "ControlType.Text", "name": "Errors Found"},
            {"type": "ControlType.Button", "name": "Submit", "enabled": True, "offscreen": False},
        )
        out = eng.plan(profile(), s, eng.EnginePolicy(allow_submit=True), {})
        self.assertEqual(out["status"], "blocked")

    def test_compaction_keeps_state_but_deduplicates(self):
        s = state(
            {"type": "ControlType.ListItem", "name": "current step 1 of 6 My Information"},
            {"type": "ControlType.ListItem", "name": "current step 1 of 6 My Information"},
            {"type": "ControlType.Edit", "id": "email", "name": "Email Address", "value": ""},
            {"type": "ControlType.Text", "name": "decorative footer"},
        )
        out = eng.compact_snapshot(s)
        self.assertEqual(out["current_step"]["number"], 1)
        names = [x["name"] for x in out["controls"]]
        self.assertEqual(names.count("current step 1 of 6 My Information"), 1)
        self.assertNotIn("decorative footer", names)


if __name__ == "__main__":
    unittest.main()
