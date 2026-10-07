#!/usr/bin/env python3
from __future__ import annotations

import unittest

import reasoning_broker_v2 as broker


class ReasoningBrokerTests(unittest.TestCase):
    def test_static_provider_uses_automation_id_key(self):
        requests=[{
            "kind":"field_answer",
            "field":"Why are you interested?",
            "automation_id":"q-1",
            "profile_context":{"skills":["CDL"]},
            "constraints":[],
        }]
        out=broker.resolve({"provider":"static","answers":{"q-1":"Supported answer"}},requests)
        self.assertEqual(out,{"q-1":"Supported answer"})

    def test_static_provider_can_fallback_to_field_name(self):
        requests=[{"kind":"field_answer","field":"Summary","automation_id":"","constraints":[]}]
        out=broker.resolve({"provider":"static","answers":{"Summary":"Concise summary"}},requests)
        self.assertEqual(out,{"Summary":"Concise summary"})

    def test_missing_static_answer_fails_closed(self):
        requests=[{"kind":"field_answer","field":"Unknown","automation_id":"q-x","constraints":[]}]
        with self.assertRaises(broker.ReasoningBrokerError):
            broker.resolve({"provider":"static","answers":{}},requests)

    def test_static_choice_must_match_allowed_option(self):
        requests=[{"kind":"choice_answer","field":"Work weekends?","key":"Work weekends?","options":["Yes","No"],"constraints":[]}]
        out=broker.resolve({"provider":"static","answers":{"Work weekends?":"Yes"}},requests)
        self.assertEqual(out,{"Work weekends?":"Yes"})
        with self.assertRaises(broker.ReasoningBrokerError):
            broker.resolve({"provider":"static","answers":{"Work weekends?":"Maybe"}},requests)

    def test_explicit_semantic_key_takes_precedence(self):
        requests=[{"kind":"choice_answer","field":"Schedule","key":"Availability::Schedule","automation_id":"dynamic-123","options":["Day","Night"],"constraints":[]}]
        out=broker.resolve({"provider":"static","answers":{"Availability::Schedule":"Night"}},requests)
        self.assertEqual(out,{"Availability::Schedule":"Night"})

    def test_non_field_reasoning_request_rejected(self):
        with self.assertRaises(broker.ReasoningBrokerError):
            broker.resolve({"provider":"static","answers":{}},[{"kind":"choose_option"}])


if __name__ == "__main__":
    unittest.main()
