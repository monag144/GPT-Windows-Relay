#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import job_application_session_v2 as sessions


class SessionStoreTests(unittest.TestCase):
    def test_backward_step_marks_downstream_revalidation(self):
        s=sessions.empty_session("app-1")
        sessions.observe_step(s,5)
        sessions.observe_step(s,2)
        self.assertEqual(s["downstream_revalidation_required_from"],3)

    def test_revalidation_advances_until_highest_step(self):
        s=sessions.empty_session("app-1")
        sessions.observe_step(s,5)
        sessions.observe_step(s,2)
        sessions.mark_revalidated_through(s,3)
        self.assertEqual(s["downstream_revalidation_required_from"],4)
        sessions.mark_revalidated_through(s,4)
        self.assertEqual(s["downstream_revalidation_required_from"],5)
        sessions.mark_revalidated_through(s,5)
        self.assertIsNone(s["downstream_revalidation_required_from"])

    def test_verified_action_becomes_review_assertion(self):
        s=sessions.empty_session("app-1")
        sessions.record_verified_action(
            s,
            {"op":"select_hierarchy","target":{"name":"How Did You Hear About Us?"},"verify":{"kind":"selected_pill_equals","value":"Spokane County"}},
            1,
        )
        self.assertEqual(len(s["review_assertions"]),1)
        item=s["review_assertions"][0]
        self.assertEqual(item["field"],"How Did You Hear About Us?")
        self.assertEqual(item["value"],"Spokane County")
        self.assertTrue(item["trusted"])

    def test_review_assertion_scope_persists_and_validates(self):
        s=sessions.empty_session("app-scope")
        sessions.record_verified_action(
            s,
            {"op":"set_text","target":{"name":"Company","group_name":"Work Experience 2"},"value":"Employer B"},
            2,
        )
        item=s["review_assertions"][0]
        self.assertEqual(item["group_name"],"Work Experience 2")
        sessions.validate_session(s)
        item["group_name"]=""
        with self.assertRaises(sessions.SessionStoreError):
            sessions.validate_session(s)

    def test_backward_navigation_untrusts_downstream_assertions_then_retrusts(self):
        s=sessions.empty_session("app-1")
        sessions.record_verified_action(s,{"op":"set_text","target":{"name":"Question"},"value":"Answer"},3)
        sessions.observe_step(s,5)
        sessions.observe_step(s,2)
        self.assertFalse(s["review_assertions"][0]["trusted"])
        self.assertEqual(sessions.trusted_review_assertions(s),[])
        sessions.mark_revalidated_through(s,3)
        self.assertTrue(s["review_assertions"][0]["trusted"])
        self.assertEqual(len(sessions.trusted_review_assertions(s)),1)

    def test_nonsemantic_actions_do_not_become_review_assertions(self):
        s=sessions.empty_session("app-1")
        sessions.record_verified_action(s,{"op":"invoke","target":{"name":"Save and Continue"}},2)
        sessions.record_verified_action(s,{"op":"set_toggle","target":{"name":"I agree"},"checked":True},4)
        self.assertEqual(s["review_assertions"],[])

    def test_browser_tab_selector_persists_locally(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=sessions.empty_session("app-tab")
            sessions.set_browser_tab(s,{"tab_name":"Road Maintenance Specialist"})
            sessions.save(s)
            loaded=sessions.load("app-tab")
        self.assertEqual(loaded["browser_tab"],{"tab_name":"Road Maintenance Specialist"})

    def test_browser_tab_requires_exactly_one_selector(self):
        s=sessions.empty_session("app-tab")
        with self.assertRaises(sessions.SessionStoreError):
            sessions.set_browser_tab(s,{"tab_name":"A","contains":"B"})
        with self.assertRaises(sessions.SessionStoreError):
            sessions.set_browser_tab(s,{})

    def test_manifest_fingerprint_binding_is_restart_safe(self):
        fp="a"*64
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=sessions.empty_session("manifest-app")
            sessions.bind_manifest_fingerprint(s,fp)
            sessions.save(s)
            loaded=sessions.load("manifest-app")
        self.assertEqual(loaded["manifest_fingerprint"],fp)
        sessions.bind_manifest_fingerprint(loaded,fp)
        with self.assertRaises(sessions.SessionStoreError):
            sessions.bind_manifest_fingerprint(loaded,"b"*64)

    def test_legacy_operational_session_cannot_silently_adopt_manifest(self):
        s=sessions.empty_session("legacy-app")
        sessions.observe_step(s,2)
        with self.assertRaises(sessions.SessionStoreError):
            sessions.bind_manifest_fingerprint(s,"a"*64)
        self.assertIsNone(s["manifest_fingerprint"])

    def test_invalid_manifest_fingerprint_is_rejected(self):
        s=sessions.empty_session("manifest-app")
        for bad in ("", "A"*64, "abc", "g"*64):
            with self.subTest(bad=bad):
                with self.assertRaises(sessions.SessionStoreError):
                    sessions.bind_manifest_fingerprint(s,bad)

    def test_completion_requires_exact_verified_evidence(self):
        s=sessions.empty_session("app-complete")
        sessions.mark_completed(s,evidence="Application Submitted")
        self.assertTrue(sessions.is_completed(s))
        self.assertEqual(s["completion"]["status"],"submitted")
        with self.assertRaises(sessions.SessionStoreError):
            sessions.mark_completed(s,evidence="no submit button")

    def test_completion_persists_across_restart(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=sessions.empty_session("app-complete")
            sessions.mark_completed(s)
            sessions.save(s)
            loaded=sessions.load("app-complete")
        self.assertTrue(sessions.is_completed(loaded))
        self.assertEqual(loaded["completion"]["evidence"],"Application Submitted")

    def test_authorization_flags_are_rejected(self):
        s=sessions.empty_session("app-1")
        s["allow_submit"]=True
        with self.assertRaises(sessions.SessionStoreError):
            sessions.validate_session(s)

    def test_save_and_load_are_local_and_atomic(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{"LOCALAPPDATA":td}):
            s=sessions.empty_session("JR100708")
            sessions.observe_step(s,3)
            sessions.merge_reasoned_answers(s,{"q1":"answer"})
            path=sessions.save(s)
            self.assertTrue(path.is_file())
            loaded=sessions.load("JR100708")
            self.assertEqual(loaded["last_step_number"],3)
            self.assertEqual(loaded["reasoned_answers"]["q1"],"answer")


if __name__=="__main__":
    unittest.main()
