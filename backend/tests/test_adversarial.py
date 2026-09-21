"""Adversarial approval-safeguard tests. 100% must pass (rejection criteria)."""
import pytest
from datetime import datetime, timezone, timedelta

from app import approvals
from app.approvals import ApprovalError
from app.models import Recommendation, Approval
from app.canonical import payload_digest


def _submit(db, actor, tier, risk, payload):
    rec = approvals.submit_recommendation(
        db, actor=actor, title="adv", description="", category="test",
        tier=tier, risk_level=risk, action_payload=payload)
    db.commit()
    return rec


def test_no_self_approval_of_high_risk(db, make_user):
    submitter = make_user("Admin")
    rec = _submit(db, submitter, "requires_approval", "high", {"x": 1})
    with pytest.raises(ApprovalError) as e:
        approvals.cast_decision(db, actor=submitter, recommendation_id=rec.id,
                                decision="approve", submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "self_approval_forbidden"


def test_no_single_reviewer_counts_twice(db, make_user):
    submitter = make_user("Admin")
    reviewer = make_user("Admin")
    rec = _submit(db, submitter, "requires_approval", "high", {"x": 2})
    approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id, decision="approve",
                            submitted_payload_digest=rec.payload_digest)
    db.commit()
    with pytest.raises(ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id, decision="approve",
                                submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "duplicate_reviewer"


def test_high_risk_requires_two_distinct_reviewers(db, make_user):
    submitter = make_user("Admin")
    r1 = make_user("Admin")
    r2 = make_user("ExecOwner")
    rec = _submit(db, submitter, "requires_approval", "high", {"x": 3})
    a = approvals.cast_decision(db, actor=r1, recommendation_id=rec.id, decision="approve",
                                submitted_payload_digest=rec.payload_digest)
    db.commit()
    assert a.status == "pending"  # one approval not enough
    a = approvals.cast_decision(db, actor=r2, recommendation_id=rec.id, decision="approve",
                                submitted_payload_digest=rec.payload_digest)
    db.commit()
    assert a.status == "approved"


def test_no_reuse_after_payload_change(db, make_user):
    submitter = make_user("Admin")
    reviewer = make_user("Admin")
    rec = _submit(db, submitter, "requires_approval", "low", {"amount": 100})
    # Payload changes -> digest changes.
    rec.action_payload = {"amount": 999}
    rec.payload_digest = payload_digest(rec.action_payload)
    db.commit()
    with pytest.raises(ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id, decision="approve",
                                submitted_payload_digest="stale-digest")
    assert e.value.code == "payload_mismatch"


def test_expired_approval_cannot_be_used(db, make_user):
    submitter = make_user("Admin")
    reviewer = make_user("Admin")
    rec = _submit(db, submitter, "requires_approval", "low", {"x": 4})
    appr = approvals.open_approval_for(db, rec)
    appr.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    with pytest.raises(ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id, decision="approve",
                                submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "expired"


def test_service_identity_cannot_approve(db, make_user):
    submitter = make_user("Admin")
    agent = make_user("Agent Service Identity", is_service=True)
    rec = _submit(db, submitter, "requires_approval", "low", {"x": 5})
    with pytest.raises(ApprovalError) as e:
        approvals.cast_decision(db, actor=agent, recommendation_id=rec.id, decision="approve",
                                submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "service_identity_forbidden"


def test_permanently_prohibited_cannot_be_approved(db, make_user):
    submitter = make_user("Admin")
    reviewer = make_user("Admin")
    rec = _submit(db, submitter, "permanently_prohibited", "high", {"x": 6})
    with pytest.raises(ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id, decision="approve",
                                submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "permanently_prohibited"


def test_no_execution_after_revocation(db, make_user):
    submitter = make_user("Admin")
    r1 = make_user("Admin")
    r2 = make_user("ExecOwner")
    rec = _submit(db, submitter, "requires_approval", "high", {"x": 7})
    approvals.cast_decision(db, actor=r1, recommendation_id=rec.id, decision="approve",
                            submitted_payload_digest=rec.payload_digest)
    appr = approvals.cast_decision(db, actor=r2, recommendation_id=rec.id, decision="approve",
                                   submitted_payload_digest=rec.payload_digest)
    db.commit()
    ok, _ = approvals.can_execute(db, rec)
    assert ok is True
    approvals.revoke_approval(db, actor=r1, approval_id=appr.id, reason="test")
    db.commit()
    ok, reason = approvals.can_execute(db, rec)
    assert ok is False and reason in ("revoked", "not_approved")


def test_no_execution_under_active_pause(db, make_user):
    submitter = make_user("Admin")
    rec = _submit(db, submitter, "auto", "low", {"x": 8})
    from app.models import PauseState
    db.add(PauseState(scope="global", target="*", active=True, reason="test"))
    db.commit()
    ok, reason = approvals.can_execute(db, rec)
    assert ok is False and reason.startswith("paused")
    # cleanup
    for p in db.query(PauseState).filter_by(active=True).all():
        p.active = False
    db.commit()
