"""Local test receiver contract: real loopback HTTP, zero browser input."""
import hashlib
import json
import sys
import threading
import unittest
from pathlib import Path
from urllib import request, error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_chat_fixture as fixture


class ReceiverFixtureTests(unittest.TestCase):
    def setUp(self):
        self.receiver = fixture.Receiver(token="unit-test-secret-only")
        self.server = fixture.server_for(self.receiver)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:" + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def http(self, path, data=None, token="unit-test-secret-only", content_type="application/json"):
        headers = {"X-PCE14-Fixture": token, "Content-Type": content_type}
        encoded = json.dumps(data).encode("utf-8") if data is not None else None
        req = request.Request(self.base + path, data=encoded, headers=headers,
                              method="POST" if data is not None else "GET")
        try:
            with request.urlopen(req, timeout=3) as response:
                return response.status, response.read().decode("utf-8"), dict(response.headers)
        except error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8"), dict(exc.headers)

    def new_chat(self):
        status, body, _ = self.http("/api/new-chat", {})
        self.assertEqual(status, 201)
        return json.loads(body)["conversation_id"]

    def payload(self, conversation, operation="PCE14-FIXTURE-case01", text="hi"):
        return {"conversation_id": conversation, "operation_id": operation, "text": text}

    def test_receiver_binds_only_loopback(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.assertGreater(self.server.server_port, 0)

    def test_new_chat_creates_unique_conversation(self):
        first = self.new_chat()
        second = self.new_chat()
        self.assertNotEqual(first, second)

    def test_submit_yields_independent_receiver_side_hash_receipt(self):
        cid = self.new_chat()
        text = "PCE14 synthetic fixture ✨\nmultiline"
        status, body, _ = self.http("/api/send", self.payload(cid, text=text))
        receipt = json.loads(body)
        self.assertEqual(status, 201)
        self.assertEqual(receipt["role"], "user")
        self.assertEqual(receipt["effect_count"], 1)
        self.assertEqual(receipt["payload_sha256"], hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertEqual(receipt["payload_bytes"], len(text.encode("utf-8")))
        self.assertNotIn(text, body)
        self.assertNotIn("text", receipt)

    def test_receipts_can_be_read_separately_from_sender_response(self):
        cid = self.new_chat()
        self.http("/api/send", self.payload(cid))
        status, body, _ = self.http("/api/receipts")
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result["total_effects"], 1)
        self.assertEqual(result["receipts"][0]["conversation_id"], cid)
        self.assertNotIn('"text"', body)

    def test_duplicate_operation_does_not_create_second_effect(self):
        cid = self.new_chat()
        data = self.payload(cid)
        self.assertEqual(self.http("/api/send", data)[0], 201)
        status, body, _ = self.http("/api/send", data)
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["error"], "DUPLICATE_OPERATION")
        self.assertEqual(self.receiver.snapshot(self.receiver.token)["total_effects"], 1)

    def test_send_before_new_chat_is_rejected(self):
        status, _, _ = self.http("/api/send", self.payload("no-conversation"))
        self.assertEqual(status, 409)

    def test_stale_conversation_rejected(self):
        old = self.new_chat()
        self.new_chat()
        status, _, _ = self.http("/api/send", self.payload(old))
        self.assertEqual(status, 409)

    def test_invalid_token_denies_send_and_receipt_inspection(self):
        cid = self.new_chat()
        status, _, _ = self.http("/api/send", self.payload(cid), token="wrong-token")
        self.assertEqual(status, 403)
        status, _, _ = self.http("/api/receipts", token="wrong-token")
        self.assertEqual(status, 403)
        self.assertEqual(self.receiver.snapshot(self.receiver.token)["total_effects"], 0)

    def test_stop_blocks_new_chat_and_send(self):
        cid = self.new_chat()
        self.assertEqual(self.http("/api/stop", {})[0], 200)
        self.assertEqual(self.http("/api/send", self.payload(cid))[0], 423)
        self.assertEqual(self.http("/api/new-chat", {})[0], 423)

    def test_wrong_field_and_nonstring_message_rejected(self):
        cid = self.new_chat()
        self.assertEqual(self.http("/api/send", dict(self.payload(cid), extra="hidden"))[0], 422)
        self.assertEqual(self.http("/api/send", self.payload(cid, text=123))[0], 422)

    def test_oversized_message_fails_without_receipt(self):
        cid = self.new_chat()
        status, body, _ = self.http("/api/send", self.payload(cid, text="x" * (fixture.MAX_MESSAGE_BYTES+1)))
        self.assertEqual(status, 422)
        self.assertEqual(self.receiver.snapshot(self.receiver.token)["total_effects"], 0)

    def test_wrong_content_type_rejected(self):
        status, _, _ = self.http("/api/new-chat", {}, content_type="text/plain")
        self.assertEqual(status, 415)

    def test_local_fixture_page_is_explicitly_not_chatgpt(self):
        status, body, headers = self.http("/")
        self.assertEqual(status, 200)
        self.assertIn("NOT CHATGPT", body)
        self.assertIn("Geometry uncalibrated; controls disabled.", body)
        self.assertIn('id="new-chat" disabled', body)
        self.assertIn('id="message" placeholder=', body)
        self.assertIn("w*.585", body)
        self.assertIn("h*.56", body)
        self.assertIn("X-PCE14-Fixture", body)
        self.assertIn("no-store", headers.get("Cache-Control", ""))
        self.assertNotIn("https://chatgpt.com", body)
        self.assertNotIn("document.cookie", body)

    def test_unknown_path_has_no_external_redirect(self):
        status, body, _ = self.http("/external-service")
        self.assertEqual(status, 404)
        self.assertIn("NOT_FOUND", body)


if __name__ == "__main__":
    unittest.main()
