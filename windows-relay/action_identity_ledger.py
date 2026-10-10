"""Experimental durable action-ID tombstone ledger (offline; not wired into Client).

The SQLite identity database is append-only: it bounds the primary state JSON,
NOT total disk usage. A lost, stale or corrupt ledger is an execution blocker.
It MUST NOT be silently recreated when the relay is already provisioned.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


class LedgerError(RuntimeError):
    """Refuse execution if the durable action identity cannot be proven."""


def _legacy_identities(processed: dict, deliveries: dict) -> dict[str, str]:
    if not isinstance(processed, dict) or not isinstance(deliveries, dict):
        raise LedgerError("incomplete legacy identity state")
    found = {}
    for collection in (processed, deliveries):
        for action_id, record in collection.items():
            if not isinstance(action_id, str) or not action_id or not isinstance(record, dict):
                raise LedgerError("invalid legacy identity record")
            payload = record.get("payload_hash")
            if not isinstance(payload, str) or not payload:
                raise LedgerError("historical identity has no payload hash")
            if action_id in found and found[action_id] != payload:
                raise LedgerError("conflicting legacy action identity")
            found[action_id] = payload
    return found


def _connect_existing(path: Path) -> sqlite3.Connection:
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise LedgerError("missing durable identity database")
    connection = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=15, isolation_level=None)
    try:
        connection.execute("PRAGMA busy_timeout=15000")
        connection.execute("PRAGMA synchronous=FULL")
        return connection
    except BaseException:
        connection.close()
        raise


def _verify_ready(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone() != ("1",):
        raise LedgerError("unsupported durable identity schema")
    if connection.execute("SELECT value FROM metadata WHERE key='migration_ready'").fetchone() != ("1",):
        raise LedgerError("durable identity migration incomplete")


def initialize_from_legacy(path: Path, processed: dict, deliveries: dict) -> int:
    """One-shot bootstrap. Caller must separately persist a non-replay cutover marker.

    Do not invoke this automatically on restart: an old/out-of-date snapshot
    cannot reconstruct identities lost from a missing SQLite database.
    """
    path = Path(path).absolute()
    records = _legacy_identities(processed, deliveries)
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise LedgerError("ledger already exists or destination is invalid")
    connection = sqlite3.connect(str(path), timeout=15, isolation_level=None)
    try:
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE identities (action_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL)")
        connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.executemany("INSERT INTO identities (action_id,payload_hash) VALUES (?,?)", sorted(records.items()))
        connection.executemany(
            "INSERT INTO metadata (key,value) VALUES (?,?)",
            [("schema_version", "1"), ("migration_ready", "1")],
        )
        connection.execute("COMMIT")
    except BaseException:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()
    return len(records)


def verify_legacy_coverage(path: Path, processed: dict, deliveries: dict) -> int:
    """A stale backup database missing even one known identity blocks startup."""
    records = _legacy_identities(processed, deliveries)
    connection = _connect_existing(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _verify_ready(connection)
        if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise LedgerError("identity store integrity check failed")
        for action_id, payload in records.items():
            present = connection.execute("SELECT payload_hash FROM identities WHERE action_id=?", (action_id,)).fetchone()
            if present != (payload,):
                raise LedgerError("known legacy action absent or conflicted in ledger")
        connection.execute("COMMIT")
        return len(records)
    except BaseException:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def claim(path: Path, action_id: str, payload_hash: str) -> str:
    """NEW, REPLAY, COLLISION. Atomic across connections/processes.

    NEW means an identity is durably reserved, NOT that it is safe to retry
    after a crash. Backend must mark a reserved but incomplete ID uncertain.
    """
    if not isinstance(action_id, str) or not action_id or not isinstance(payload_hash, str) or not payload_hash:
        raise LedgerError("invalid new action identity")
    connection = _connect_existing(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _verify_ready(connection)
        row = connection.execute("SELECT payload_hash FROM identities WHERE action_id=?", (action_id,)).fetchone()
        if row is None:
            connection.execute("INSERT INTO identities (action_id,payload_hash) VALUES (?,?)", (action_id, payload_hash))
            outcome = "NEW"
        else:
            outcome = "REPLAY" if row[0] == payload_hash else "COLLISION"
        connection.execute("COMMIT")
        return outcome
    except BaseException:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def identity_count(path: Path) -> int:
    connection = _connect_existing(path)
    try:
        _verify_ready(connection)
        return connection.execute("SELECT COUNT(*) FROM identities").fetchone()[0]
    finally:
        connection.close()
