"""Governance dashboard aggregates."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Recommendation, Approval, AuditEvent, PauseState, Connector, User
from ..deps import require_permission
from ..audit import verify_chain

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db),
              user: User = Depends(require_permission("dashboard:read"))):
    pending = db.execute(select(func.count()).select_from(Approval)
                         .where(Approval.status == "pending")).scalar_one()
    recs_total = db.execute(select(func.count()).select_from(Recommendation)).scalar_one()
    prohibited = db.execute(select(func.count()).select_from(Recommendation)
                            .where(Recommendation.tier == "permanently_prohibited")).scalar_one()
    audit_count = db.execute(select(func.count()).select_from(AuditEvent)).scalar_one()
    active_pauses = db.execute(select(PauseState).where(PauseState.active.is_(True))).scalars().all()
    connectors = db.execute(select(Connector)).scalars().all()
    chain = verify_chain(db)

    return {
        "stub_notice": "AUTH STUB — NOT PRODUCTION",
        "pending_approvals": pending,
        "recommendations_total": recs_total,
        "prohibited_count": prohibited,
        "audit_event_count": audit_count,
        "audit_chain_verified": chain["verified"],
        "audit_head_seq": chain["head_seq"],
        "emergency": {
            "global_paused": any(p.scope == "global" for p in active_pauses),
            "active_pause_count": len(active_pauses),
        },
        "connectors": {
            "total": len(connectors),
            "connected": sum(1 for c in connectors if c.status != "not_connected"),
            "not_connected": sum(1 for c in connectors if c.status == "not_connected"),
        },
    }
