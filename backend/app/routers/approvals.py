"""Approvals: list/read + approve/reject/revoke with hardened safeguards."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Approval, ApprovalDecision, Recommendation, User
from ..deps import require_permission, get_current_user
from ..schemas import DecisionRequest, RevokeRequest
from .. import approvals

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


def _serialize(appr: Approval, db: Session) -> dict:
    rec = db.get(Recommendation, appr.recommendation_id)
    decisions = [{
        "id": d.id, "reviewer_id": d.reviewer_id, "decision": d.decision,
        "payload_digest": d.payload_digest, "comment": d.comment,
        "created_at": d.created_at.isoformat(),
    } for d in appr.decisions]
    distinct_approvers = sorted({d.reviewer_id for d in appr.decisions if d.decision == "approve"})
    return {
        "id": appr.id, "recommendation_id": appr.recommendation_id,
        "recommendation_title": rec.title if rec else None,
        "risk_level": rec.risk_level if rec else None,
        "tier": rec.tier if rec else None,
        "payload_digest": appr.payload_digest,
        "current_payload_digest": rec.payload_digest if rec else None,
        "payload_bound": bool(rec and rec.payload_digest == appr.payload_digest),
        "status": appr.status, "required_approvals": appr.required_approvals,
        "distinct_approvals": len(distinct_approvers),
        "revoked": appr.revoked,
        "created_at": appr.created_at.isoformat(),
        "expires_at": appr.expires_at.isoformat(),
        "decisions": decisions,
    }


@router.get("")
def list_approvals(db: Session = Depends(get_db),
                   user: User = Depends(require_permission("approval:list"))):
    rows = db.execute(select(Approval).order_by(Approval.created_at.desc())).scalars().all()
    return [_serialize(a, db) for a in rows]


@router.get("/{approval_id}")
def get_approval(approval_id: str, db: Session = Depends(get_db),
                 user: User = Depends(require_permission("approval:read"))):
    appr = db.get(Approval, approval_id)
    if appr is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return _serialize(appr, db)


@router.post("/{recommendation_id}/approve")
def approve(recommendation_id: str, body: DecisionRequest, db: Session = Depends(get_db),
            user: User = Depends(require_permission("approval:approve"))):
    try:
        appr = approvals.cast_decision(db, actor=user, recommendation_id=recommendation_id,
                                       decision="approve", submitted_payload_digest=body.payload_digest,
                                       comment=body.comment)
        db.commit()
        db.refresh(appr)
        return _serialize(appr, db)
    except approvals.ApprovalError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})


@router.post("/{recommendation_id}/reject")
def reject(recommendation_id: str, body: DecisionRequest, db: Session = Depends(get_db),
           user: User = Depends(require_permission("approval:reject"))):
    try:
        appr = approvals.cast_decision(db, actor=user, recommendation_id=recommendation_id,
                                       decision="reject", submitted_payload_digest=body.payload_digest,
                                       comment=body.comment)
        db.commit()
        db.refresh(appr)
        return _serialize(appr, db)
    except approvals.ApprovalError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})


@router.post("/{approval_id}/revoke")
def revoke(approval_id: str, body: RevokeRequest, db: Session = Depends(get_db),
           user: User = Depends(require_permission("approval:revoke"))):
    try:
        appr = approvals.revoke_approval(db, actor=user, approval_id=approval_id, reason=body.reason)
        db.commit()
        db.refresh(appr)
        return _serialize(appr, db)
    except approvals.ApprovalError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})
