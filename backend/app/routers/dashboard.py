"""Governance dashboard aggregates."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Recommendation, Approval, AuditEvent, PauseState, Connector, User, ExecutionQueueItem
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


def _grouped_counts(db, model, column):
    rows = db.execute(select(column, func.count()).select_from(model).group_by(column)).all()
    return [{"key": r[0], "count": r[1]} for r in rows]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db),
              user: User = Depends(require_permission("dashboard:read"))):
    """Aggregate trends for the governance dashboard (read-only, computed from stored data)."""
    audit_rows = db.execute(
        select(func.date(AuditEvent.created_at).label("d"), func.count())
        .group_by(func.date(AuditEvent.created_at))
        .order_by(func.date(AuditEvent.created_at))
    ).all()
    return {
        "stub_notice": "AUTH STUB — NOT PRODUCTION",
        "recommendations_by_status": _grouped_counts(db, Recommendation, Recommendation.status),
        "recommendations_by_tier": _grouped_counts(db, Recommendation, Recommendation.tier),
        "approvals_by_status": _grouped_counts(db, Approval, Approval.status),
        "executions_by_status": _grouped_counts(db, ExecutionQueueItem, ExecutionQueueItem.status),
        "audit_daily": [{"date": str(r[0]), "count": r[1]} for r in audit_rows],
    }
