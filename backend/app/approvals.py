"""Approval + recommendation state machines with hardened, adversarially-tested safeguards.

Enforced invariants (see tests/test_adversarial.py):
  - Approvals bind to the exact action-payload digest; any payload change invalidates them.
  - No self-approval of high-risk recommendations (submitter != reviewer).
  - No single reviewer counted twice (DB unique constraint + check here).
  - No expired-approval reuse.
  - No reuse after payload change.
  - No execution after revocation.
  - No execution while a matching pause (global or granular) is active.
  - No agent/service identity may approve, reject, or revoke anything.
  - permanently_prohibited can never be approved or executed.
"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Recommendation, Approval, ApprovalDecision, PauseState, User
from .canonical import payload_digest
from . import audit

APPROVAL_TTL_HOURS = 24

TIER_AUTO = "auto"
TIER_REQUIRES = "requires_approval"
TIER_PROHIBITED = "permanently_prohibited"


class ApprovalError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def active_pause_blocking(db: Session, target_permission: str | None) -> PauseState | None:
    """Return an active pause that blocks execution: global, or granular matching target."""
    rows = db.execute(select(PauseState).where(PauseState.active.is_(True))).scalars().all()
    for p in rows:
        if p.scope == "global":
            return p
        if p.scope == "granular" and target_permission and p.target == target_permission:
            return p
    return None


def open_approval_for(db: Session, rec: Recommendation) -> Approval | None:
    return db.execute(
        select(Approval)
        .where(Approval.recommendation_id == rec.id, Approval.status == "pending")
        .order_by(Approval.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def submit_recommendation(db: Session, *, actor: User, title: str, description: str,
                          category: str, tier: str, risk_level: str,
                          action_payload: dict, target_permission: str | None = None) -> Recommendation:
    digest = payload_digest(action_payload)
    required = 2 if risk_level == "high" else 1
    rec = Recommendation(
        title=title, description=description, category=category, tier=tier,
        risk_level=risk_level, action_payload=action_payload, payload_digest=digest,
        required_approvals=required, submitted_by=actor.id,
    )

    if tier == TIER_PROHIBITED:
        rec.status = "prohibited"
    elif tier == TIER_AUTO:
        rec.status = "auto_approved"
    else:
        rec.status = "pending"
    db.add(rec)
    db.flush()

    if tier == TIER_REQUIRES:
        approval = Approval(
            recommendation_id=rec.id, payload_digest=digest, status="pending",
            required_approvals=required, expires_at=_now() + timedelta(hours=APPROVAL_TTL_HOURS),
        )
        db.add(approval)
        db.flush()

    audit.append_event(
        db, actor_id=actor.id, actor_label=actor.display_name,
        action="recommendation.submitted", resource_type="recommendation", resource_id=rec.id,
        payload={"tier": tier, "risk_level": risk_level, "payload_digest": digest,
                 "status": rec.status, "target_permission": target_permission},
    )
    return rec


def _assert_can_review(actor: User):
    # No agent/service identity may approve/reject/revoke anything.
    if actor.is_service_identity:
        raise ApprovalError("service_identity_forbidden",
                            "Agent/service identities may never approve, reject, or revoke.")


def cast_decision(db: Session, *, actor: User, recommendation_id: str, decision: str,
                  submitted_payload_digest: str, comment: str = "") -> Approval:
    _assert_can_review(actor)

    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise ApprovalError("not_found", "Recommendation not found.")

    if rec.tier == TIER_PROHIBITED:
        raise ApprovalError("permanently_prohibited",
                            "This recommendation is permanently prohibited and can never be approved.")
    if rec.tier != TIER_REQUIRES:
        raise ApprovalError("not_reviewable", "Only requires_approval recommendations accept decisions.")

    approval = open_approval_for(db, rec)
    if approval is None:
        raise ApprovalError("no_open_approval", "No open approval for this recommendation.")
    if approval.revoked or approval.status != "pending":
        raise ApprovalError("not_pending", "Approval is not pending.")

    now = _now()
    if approval.expires_at.replace(tzinfo=timezone.utc) < now:
        approval.status = "rejected"
        audit.append_event(db, actor_id=actor.id, actor_label=actor.display_name,
                            action="approval.expired", resource_type="approval",
                            resource_id=approval.id, payload={"recommendation_id": rec.id})
        raise ApprovalError("expired", "Approval window has expired; a new approval is required.")

    # Payload-digest binding: decision must reference the current payload digest.
    if submitted_payload_digest != rec.payload_digest or approval.payload_digest != rec.payload_digest:
        raise ApprovalError("payload_mismatch",
                            "Action payload changed since the approval was opened; decision rejected.")

    # No self-approval of high-risk.
    if rec.risk_level == "high" and decision == "approve" and actor.id == rec.submitted_by:
        raise ApprovalError("self_approval_forbidden",
                            "High-risk recommendations cannot be approved by their submitter.")

    # No single reviewer counted twice (also enforced by DB unique constraint).
    existing = db.execute(
        select(ApprovalDecision).where(
            ApprovalDecision.approval_id == approval.id,
            ApprovalDecision.reviewer_id == actor.id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ApprovalError("duplicate_reviewer", "This reviewer has already decided on this approval.")

    db.add(ApprovalDecision(
        approval_id=approval.id, reviewer_id=actor.id, decision=decision,
        payload_digest=rec.payload_digest, comment=comment,
    ))
    db.flush()

    audit.append_event(db, actor_id=actor.id, actor_label=actor.display_name,
                        action=f"approval.{decision}", resource_type="approval",
                        resource_id=approval.id,
                        payload={"recommendation_id": rec.id, "payload_digest": rec.payload_digest})

    if decision == "reject":
        approval.status = "rejected"
        rec.status = "rejected"
    else:
        approves = [d for d in approval.decisions if d.decision == "approve"]
        distinct_reviewers = {d.reviewer_id for d in approves}
        if len(distinct_reviewers) >= approval.required_approvals:
            approval.status = "approved"
            rec.status = "approved"
            audit.append_event(db, actor_id=actor.id, actor_label=actor.display_name,
                                action="approval.quorum_reached", resource_type="approval",
                                resource_id=approval.id,
                                payload={"recommendation_id": rec.id,
                                         "required": approval.required_approvals,
                                         "distinct_reviewers": sorted(distinct_reviewers)})
    return approval


def revoke_approval(db: Session, *, actor: User, approval_id: str, reason: str = "") -> Approval:
    _assert_can_review(actor)
    approval = db.get(Approval, approval_id)
    if approval is None:
        raise ApprovalError("not_found", "Approval not found.")
    approval.revoked = True
    approval.status = "revoked"
    approval.revoked_by = actor.id
    approval.revoked_at = _now()
    rec = db.get(Recommendation, approval.recommendation_id)
    if rec is not None and rec.status in ("approved", "pending"):
        rec.status = "revoked"
    audit.append_event(db, actor_id=actor.id, actor_label=actor.display_name,
                        action="approval.revoked", resource_type="approval",
                        resource_id=approval.id, payload={"reason": reason})
    return approval


def can_execute(db: Session, rec: Recommendation, target_permission: str | None = None) -> tuple[bool, str]:
    """Gate used by (stub) execution paths. Never executes live connectors in 1A."""
    if rec.tier == TIER_PROHIBITED:
        return False, "permanently_prohibited"
    pause = active_pause_blocking(db, target_permission)
    if pause is not None:
        return False, f"paused:{pause.scope}"
    if rec.tier == TIER_AUTO:
        return True, "auto"
    approval = db.execute(
        select(Approval).where(Approval.recommendation_id == rec.id).order_by(Approval.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    if approval is None or approval.status != "approved":
        return False, "not_approved"
    if approval.revoked:
        return False, "revoked"
    if approval.expires_at.replace(tzinfo=timezone.utc) < _now():
        return False, "expired"
    if approval.payload_digest != rec.payload_digest:
        return False, "payload_changed"
    return True, "approved"
