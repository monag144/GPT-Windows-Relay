#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


LAB = Path(__file__).resolve().parents[1] / "job_application_provider_lab_v2.html"


class _LabParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attrs: list[dict[str, str]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        item={"tag":tag}
        item.update({str(k):str(v or "") for k,v in attrs})
        self.attrs.append(item)

    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())


class ProviderLabV2Tests(unittest.TestCase):
    def _parsed(self):
        raw=LAB.read_text(encoding="utf-8")
        parser=_LabParser()
        parser.feed(raw)
        return raw,parser

    def test_lab_is_local_only_and_has_unique_title(self):
        raw,_=self._parsed()
        self.assertIn("<title>GPT Job Provider Lab</title>",raw)
        self.assertNotRegex(raw,re.compile(r"https?://",re.I))
        self.assertNotIn("fetch(",raw)
        self.assertNotIn("XMLHttpRequest",raw)

    def test_lab_exposes_semantic_controls_for_provider_actions(self):
        _,parser=self._parsed()
        attrs=parser.attrs
        def has(**wanted):
            return any(all(item.get(k)==v for k,v in wanted.items()) for item in attrs)
        self.assertTrue(has(tag="input",**{"aria-label":"First Name"}))
        self.assertTrue(has(tag="input",type="checkbox",**{"aria-label":"Email Updates"}))
        self.assertTrue(has(tag="input",type="radio",**{"aria-label":"Yes"}))
        self.assertTrue(has(tag="input",role="combobox",**{"aria-label":"Schedule"}))
        self.assertTrue(has(tag="ul",role="listbox",**{"aria-label":"Options Expanded"}))
        self.assertTrue(has(tag="button",**{"aria-label":"Select Files"}))
        self.assertTrue(has(tag="button",**{"aria-label":"Continue Lab"}))

    def test_lab_has_exact_dropdown_and_verification_markers(self):
        raw,parser=self._parsed()
        self.assertIn("data-value=\"Day\"",raw)
        self.assertIn("data-value=\"Night\"",raw)
        self.assertIn("data-value=\"Weekend\"",raw)
        joined="\n".join(parser.text)
        self.assertIn("Successfully Uploaded!",raw)
        self.assertIn("Lab Continue Verified",raw)
        self.assertIn("Continue Lab",joined)


if __name__=="__main__":
    unittest.main()
