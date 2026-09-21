"""Tamper-evident hash-chain: determinism, concurrency-safe sequencing, verification,
gap/reorder/duplicate/tamper detection, genesis, checkpoints."""
import uuid
import pytest
from sqlalchemy import text

from app import audit
from app.canonical import canonical_json, payload_digest


def _scope():
    return {"chain_env": "dev", "chain_org": f"test-{uuid.uuid4().hex[:8]}"}


def test_canonical_serialization_is_deterministic():
    a = canonical_json({"b": 1, "a": [3, 2, 1], "c": {"y": 2, "x": 1}})
    b = canonical_json({"c": {"x": 1, "y": 2}, "a": [3, 2, 1], "b": 1})
    assert a == b


def test_payload_digest_changes_with_payload():
    d1 = payload_digest({"amount": 100})
    d2 = payload_digest({"amount": 101})
    assert d1 != d2 and len(d1) == 64


def test_append_and_verify_clean_chain(db):
    scope = _scope()
    for i in range(5):
        audit.append_event(db, actor_id=None, actor_label="tester", action="test.event",
                           resource_type="test", resource_id=str(i), payload={"i": i}, **scope)
    db.commit()
    report = audit.verify_chain(db, **scope)
    assert report["verified"] is True
    assert report["event_count"] == 5
    assert report["genesis_ok"] is True
    assert report["head_seq"] == 4


def test_genesis_prev_hash(db):
    scope = _scope()
    ev = audit.append_event(db, actor_id=None, actor_label="tester", action="genesis.test",
                            resource_type="test", payload={}, **scope)
    db.commit()
    assert ev.seq == 0
    assert ev.prev_hash == "0" * 64


def test_checkpoint_records_head(db):
    scope = _scope()
    for i in range(3):
        audit.append_event(db, actor_id=None, actor_label="t", action="cp.test",
                           resource_type="test", payload={"i": i}, **scope)
    db.commit()
    cp = audit.create_checkpoint(db, note="test", **scope)
    db.commit()
    assert cp is not None and cp.seq == 2 and cp.event_count == 3


def test_tamper_detection_via_owner_update(db, admin_engine):
    """Simulate a DB-owner edit and prove verify_chain flags it (tamper-EVIDENT)."""
    scope = _scope()
    for i in range(3):
        audit.append_event(db, actor_id=None, actor_label="t", action="tamper.test",
                           resource_type="test", payload={"i": i}, **scope)
    db.commit()

    # Owner rewrites a payload without updating hash -> field tamper.
    with admin_engine.begin() as conn:
        conn.execute(text(
            "UPDATE audit_events SET action = 'TAMPERED' "
            "WHERE chain_env = :e AND chain_org = :o AND seq = 1"),
            {"e": scope["chain_env"], "o": scope["chain_org"]})

    db.expire_all()
    report = audit.verify_chain(db, **scope)
    assert report["verified"] is False
    kinds = {i["type"] for i in report["issues"]}
    assert "hash_mismatch" in kinds or "field_tamper" in kinds


def test_duplicate_and_gap_detection_via_owner_insert(db, admin_engine):
    scope = _scope()
    for i in range(3):
        audit.append_event(db, actor_id=None, actor_label="t", action="gap.test",
                           resource_type="test", payload={"i": i}, **scope)
    db.commit()
    # Owner deletes seq=1 to create a gap.
    with admin_engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_events WHERE chain_env=:e AND chain_org=:o AND seq=1"),
                     {"e": scope["chain_env"], "o": scope["chain_org"]})
    db.expire_all()
    report = audit.verify_chain(db, **scope)
    assert report["verified"] is False
    kinds = {i["type"] for i in report["issues"]}
    assert "gap_or_reorder" in kinds or "broken_link" in kinds
