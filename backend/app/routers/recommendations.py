"""Recommendations: list/read/create/update (with payload-digest re-binding)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Recommendation, User
from ..deps import require_permission
from ..schemas import RecommendationCreate
from ..canonical import payload_digest
from .. import approvals, audit

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

VALID_TIERS = {"auto", "requires_approval", "permanently_prohibited"}
VALID_RISK = {"low", "medium", "high"}


def _serialize(rec: Recommendation) -> dict:
    return {
        "id": rec.id, "title": rec.title, "description": rec.description,
        "category": rec.category, "tier": rec.tier, "risk_level": rec.risk_level,
        "action_payload": rec.action_payload, "payload_digest": rec.payload_digest,
        "status": rec.status, "required_approvals": rec.required_approvals,
        "submitted_by": rec.submitted_by,
        "created_at": rec.created_at.isoformat(), "updated_at": rec.updated_at.isoformat(),
    }


@router.get("")
def list_recs(db: Session = Depends(get_db),
              user: User = Depends(require_permission("recommendation:list"))):
    rows = db.execute(select(Recommendation).order_by(Recommendation.created_at.desc())).scalars().all()
    return [_serialize(r) for r in rows]


@router.get("/{rec_id}")
def get_rec(rec_id: str, db: Session = Depends(get_db),
            user: User = Depends(require_permission("recommendation:read"))):
    rec = db.get(Recommendation, rec_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return _serialize(rec)


@router.post("")
def create_rec(body: RecommendationCreate, db: Session = Depends(get_db),
               user: User = Depends(require_permission("recommendation:create"))):
    if body.tier not in VALID_TIERS:
        raise HTTPException(status_code=422, detail="Invalid tier")
    if body.risk_level not in VALID_RISK:
        raise HTTPException(status_code=422, detail="Invalid risk_level")
    rec = approvals.submit_recommendation(
        db, actor=user, title=body.title, description=body.description,
        category=body.category, tier=body.tier, risk_level=body.risk_level,
        action_payload=body.action_payload, target_permission=body.target_permission,
    )
    db.commit()
    db.refresh(rec)
    return _serialize(rec)


@router.put("/{rec_id}/payload")
def update_payload(rec_id: str, body: dict, db: Session = Depends(get_db),
                   user: User = Depends(require_permission("recommendation:update"))):
    """Changing the payload re-derives the digest, invalidating any prior approval binding."""
    rec = db.get(Recommendation, rec_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.tier == "permanently_prohibited":
        raise HTTPException(status_code=403, detail="Permanently prohibited recommendations are immutable to edits")
    new_payload = body.get("action_payload", {})
    old_digest = rec.payload_digest
    rec.action_payload = new_payload
    rec.payload_digest = payload_digest(new_payload)
    if rec.status in ("approved", "pending"):
        rec.status = "pending"
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="recommendation.payload_changed", resource_type="recommendation",
                       resource_id=rec.id, payload={"old_digest": old_digest, "new_digest": rec.payload_digest})
    db.commit()
    db.refresh(rec)
    return _serialize(rec)
