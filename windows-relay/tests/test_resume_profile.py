import tempfile
from pathlib import Path
import unittest
import json

import resume_profile as rp

class ResumeProfileTests(unittest.TestCase):
    def profile(self):
        p=rp.empty_profile()
        p["identity"].update(first_name="Ada",last_name="Example")
        p["contact"].update(email="ada@example.invalid",city="Example City",state="WA")
        p["work_authorization"].update(authorized_to_work=True,requires_sponsorship=False)
        p["experience"]=[{"employer":"Example Logistics","title":"Driver","start_date":"2020-01","end_date":"2024-01","highlights":["Safe operations"]}]
        p["skills"]=["Logistics","Customer service"]
        p["custom"]["preferred shift"]="Day"
        return p

    def test_template_has_expected_sections(self):
        p=rp.empty_profile(); rp.validate_profile(p)
        self.assertEqual(p["schema_version"],1)
        for key in ("identity","contact","links","work_authorization","experience","education","certifications","skills","availability","custom"):
            self.assertIn(key,p)

    def test_alias_lookup_is_deterministic(self):
        r=rp.lookup_field(self.profile(),"E-mail address")
        self.assertEqual(r["status"],"found"); self.assertEqual(r["source"],"contact.email"); self.assertEqual(r["value"],"ada@example.invalid"); self.assertTrue(r["deterministic"])

    def test_false_boolean_is_valid_value(self):
        r=rp.lookup_field(self.profile(),"Will you require sponsorship?")
        self.assertEqual(r["status"],"found"); self.assertIs(r["value"],False)

    def test_custom_lookup_is_exact_after_normalization(self):
        r=rp.lookup_field(self.profile(),"Preferred Shift")
        self.assertEqual(r["status"],"found"); self.assertEqual(r["value"],"Day")

    def test_unknown_field_requires_reasoning_instead_of_guessing(self):
        r=rp.lookup_field(self.profile(),"Why do you want to work here?")
        self.assertEqual(r["status"],"needs_reasoning"); self.assertFalse(r["deterministic"]); self.assertIn("experience",r["context"])

    def test_load_validates_schema(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"resume.json"; p.write_text(json.dumps(self.profile()),encoding="utf-8")
            self.assertEqual(rp.load_profile(p)["identity"]["first_name"],"Ada")
            bad=self.profile(); bad["schema_version"]=99; p.write_text(json.dumps(bad),encoding="utf-8")
            with self.assertRaises(ValueError): rp.load_profile(p)

if __name__=="__main__": unittest.main()
