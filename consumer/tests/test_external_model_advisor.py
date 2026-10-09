"""Unit tests must never make a live provider call."""
import contextlib
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import external_model_advisor as adv


class FakeResponse:
    def __init__(self, body):
        self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return self.body[:n]


class ExternalAdvisorTests(unittest.TestCase):
    def test_pinned_free_and_trial_models(self):
        self.assertEqual(adv.get_provider("zai-free").model, "glm-4.7-flash")
        self.assertEqual(adv.get_provider("nvidia-trial").model, "z-ai/glm-5.3-flash")
        with self.assertRaises(adv.AdvisorError): adv.get_provider("arbitrary-paid-model")

    def test_dry_run_never_calls_network(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(adv.main(["--question", "public test"]), 0)
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["mode"], "DRY_RUN_NO_NETWORK")
        self.assertFalse(parsed["result_can_execute_actions"])

    def test_question_and_budget_limits(self):
        for invalid in ("", "  ", "x" * 4001):
            with self.assertRaises(adv.AdvisorError): adv.build_payload(invalid)
        for count in (-1, 0, 901, True):
            with self.assertRaises(adv.AdvisorError): adv.build_payload("test", max_tokens=count)

    def test_send_pinned_endpoint_and_return_inert_text(self):
        captured = {}
        def opener(req, timeout):
            captured.update({"url": req.full_url, "timeout": timeout,
                             "payload": json.loads(req.data)})
            return FakeResponse(b'{"choices":[{"message":{"content":"Consider inspecting the URL."}}]}')
        result = adv.request_advice("public diagnostic", provider="nvidia-trial",api_key="temporary-test-key",opener=opener)
        self.assertEqual(result, "Consider inspecting the URL.")
        self.assertEqual(captured["payload"]["model"], "z-ai/glm-5.3-flash")
        self.assertEqual(captured["url"], "https://integrate.api.nvidia.com/v1/chat/completions")
        self.assertNotIn("tools", captured["payload"])

    def test_no_secret_in_http_errors(self):
        def opener(req, timeout):
            raise HTTPError(req.full_url, 401, "key=temporary-test-key", None, None)
        with self.assertRaises(adv.AdvisorError) as raised:
            adv.request_advice("public",api_key="temporary-test-key",opener=opener)
        self.assertNotIn("temporary-test-key", str(raised.exception))

    def test_invalid_response_fails_closed(self):
        for raw in (b"bad-json", b'{"choices":[]}', b'{"choices":[{"message":{"content":""}}]}'):
            with self.assertRaises(adv.AdvisorError):
                adv.request_advice("public",api_key="test",opener=lambda req,timeout: FakeResponse(raw))

    def test_missing_credentials_refuses_request(self):
        with self.assertRaises(adv.AdvisorError):
            adv.request_advice("public",api_key="")

if __name__ == "__main__": unittest.main()
