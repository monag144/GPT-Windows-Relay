"""Authenticated browser -> backend dispatch contract; no live relay usage."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import windows_relay as relay  # noqa: E402


def packet(action_id="TRANSPORT-UNIT-001", session="default"):
    fields = {
        "version": 1, "platform": "windows", "action": "EXEC",
        "id": action_id, "session": session, "shell": "python",
        "command": "print('ISOLATED_CANARY')", "timeout": 10,
    }
    return relay.OPEN + "\n" + json.dumps(fields) + "\n" + relay.CLOSE


def transport_for(pkt, key="https://chatgpt.com/c/test-owner", tab=17, session="default"):
    action = relay.extract(pkt)
    return {
        "issuance": {
            "id": action.id,
            "session": session,
            "packet_hash": hashlib.sha256(pkt.encode("utf-8")).hexdigest(),
        },
        "owner": {
            "conversation_key": key,
            "session": session,
            "tab_id": tab,
        },
    }


class AuthenticatedTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = relay.State(Path(self.temp.name) / "state.json")
        self.packet = packet()
        self.valid = transport_for(self.packet)

    def bind(self):
        self.state.bind_conversation_owner(self.valid["owner"])

    def test_missing_transport_fails_before_execution_or_reservation(self):
        self.bind()
        for metadata in (None, {}, {"issuance": {}, "owner": {}}):
            with self.subTest(metadata=metadata):
                with mock.patch.object(relay, "execute", side_effect=AssertionError("must not execute")):
                    with self.assertRaisesRegex(relay.RelayError, "authenticated_transport_required|transport_identity_missing"):
                        relay.process(self.packet, self.state, metadata)
        self.assertIsNone(self.state.lookup(relay.extract(self.packet).id))

    def test_unbound_owner_is_not_authorized_by_pairing_metadata(self):
        with self.assertRaisesRegex(relay.RelayError, "conversation_owner_mismatch"):
            relay.validate_transport_identity(self.packet, **self.valid, state=self.state)
        self.assertIsNone(self.state.lookup(relay.extract(self.packet).id))

    def test_bound_owner_and_exact_hash_are_accepted(self):
        self.bind()
        self.assertTrue(relay.validate_transport_identity(
            self.packet, self.valid["issuance"], self.valid["owner"], self.state
        ))
        journal = Path(self.temp.name) / "issuance-journal.jsonl"
        self.assertTrue(journal.is_file())
        self.assertEqual(len(journal.read_text(encoding="utf-8").splitlines()), 1)
        self.assertTrue(relay.validate_transport_identity(
            self.packet, self.valid["issuance"], self.valid["owner"], self.state
        ))
        self.assertEqual(len(journal.read_text(encoding="utf-8").splitlines()), 1)

    def test_wrong_tab_rejected(self):
        self.bind()
        candidate = transport_for(self.packet, tab=18)
        with self.assertRaisesRegex(relay.RelayError, "conversation_tab_mismatch"):
            relay.validate_transport_identity(
                self.packet, candidate["issuance"], candidate["owner"], self.state
            )

    def test_invalid_tab_rejected(self):
        self.bind()
        for tab in (None, 0, -1, True, "17"):
            with self.subTest(tab=tab):
                candidate = transport_for(self.packet, tab=tab)
                with self.assertRaisesRegex(relay.RelayError, "conversation_tab_mismatch"):
                    relay.validate_transport_identity(
                        self.packet, candidate["issuance"], candidate["owner"], self.state
                    )

    def test_issuance_packet_tampering_rejected(self):
        self.bind()
        for patch in ({"id": "OTHER"}, {"packet_hash": "bad"}):
            candidate = dict(self.valid["issuance"], **patch)
            with self.subTest(patch=patch):
                with self.assertRaisesRegex(relay.RelayError, "issuance_packet_mismatch"):
                    relay.validate_transport_identity(
                        self.packet, candidate, self.valid["owner"], self.state
                    )

    def test_mismatched_conversation_rejected(self):
        self.bind()
        candidate = transport_for(self.packet, key="https://chatgpt.com/c/other")
        with self.assertRaisesRegex(relay.RelayError, "conversation_owner_mismatch"):
            relay.validate_transport_identity(
                self.packet, candidate["issuance"], candidate["owner"], self.state
            )

    def test_operator_bind_requires_positive_tab_and_is_persisted(self):
        for tab in (0, False, "1"):
            with self.subTest(tab=tab):
                with self.assertRaisesRegex(relay.RelayError, "conversation_owner_invalid"):
                    self.state.bind_conversation_owner(
                        {"conversation_key": "https://chatgpt.com/c/test", "session": "default", "tab_id": tab}
                    )
        self.bind()
        reloaded = relay.State(Path(self.temp.name) / "state.json")
        self.assertEqual(reloaded.data["conversation_owner"]["authorization"], "operator")
        self.assertEqual(reloaded.data["conversation_owner"]["tab_id"], 17)


if __name__ == "__main__":
    unittest.main()
