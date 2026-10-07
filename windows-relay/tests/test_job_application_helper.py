import unittest
from unittest import mock
import job_application_helper as j
import resume_profile as rp

class JobApplicationHelperTests(unittest.TestCase):
    def profile(self):
        p=rp.empty_profile(); p["contact"]["email"]="ada@example.invalid"; p["work_authorization"]["requires_sponsorship"]=False; p["experience"]=[{"employer":"Example Logistics","title":"Driver"}]; return p

    def test_deterministic_field_is_ready(self):
        r=j.prepare(self.profile(),"E-mail address","E-mail address")
        self.assertEqual(r["status"],"ready"); self.assertEqual(r["answer"],"ada@example.invalid"); self.assertFalse(r["reasoning_required"])

    def test_boolean_rendering_is_form_friendly(self):
        r=j.prepare(self.profile(),"Will you require sponsorship?","Will you require sponsorship?")
        self.assertEqual(r["status"],"ready"); self.assertEqual(r["answer"],"No")

    def test_subjective_question_returns_reasoning_packet_without_guess(self):
        r=j.prepare(self.profile(),"Why do you want to work here?","Why do you want to work here? 500 characters max")
        self.assertEqual(r["status"],"needs_reasoning"); self.assertTrue(r["reasoning_required"]); self.assertNotIn("answer",r); self.assertIn("profile_context",r["reasoning_request"])

    def test_missing_mapped_fact_does_not_become_reasoning_guess(self):
        r=j.prepare(self.profile(),"Phone number","Phone number")
        self.assertEqual(r["status"],"missing_profile_data"); self.assertNotIn("answer",r)

    def test_clipboard_path_uses_clipboard_primitive(self):
        with mock.patch.object(j.windows_tools,"clipboard_read_text",return_value="E-mail address"):
            r=j.prepare_from_clipboard(self.profile(),"E-mail address")
        self.assertEqual(r["answer"],"ada@example.invalid")

    def test_apply_requires_nonempty_answer(self):
        with self.assertRaises(ValueError): j.apply_answer("",window_title="x",field_name="y")

if __name__=="__main__": unittest.main()
