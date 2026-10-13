"""Governance dashboard aggregates."""
import csv
import io
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
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


def _grouped_counts(db, column, ts_col, cutoff):
    rows = db.execute(
        select(column, func.count()).where(ts_col >= cutoff).group_by(column)
    ).all()
    return [{"key": r[0], "count": r[1]} for r in rows]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db),
              user: User = Depends(require_permission("dashboard:read")),
              days: int = Query(default=30, ge=1, le=365)):
    """Aggregate trends for the governance dashboard (read-only). `days` scopes the window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    audit_rows = db.execute(
        select(func.date(AuditEvent.created_at).label("d"), func.count())
        .where(AuditEvent.created_at >= cutoff)
        .group_by(func.date(AuditEvent.created_at))
        .order_by(func.date(AuditEvent.created_at))
    ).all()
    return {
        "stub_notice": "AUTH STUB — NOT PRODUCTION",
        "days": days,
        "recommendations_by_status": _grouped_counts(db, Recommendation.status, Recommendation.created_at, cutoff),
        "recommendations_by_tier": _grouped_counts(db, Recommendation.tier, Recommendation.created_at, cutoff),
        "approvals_by_status": _grouped_counts(db, Approval.status, Approval.created_at, cutoff),
        "executions_by_status": _grouped_counts(db, ExecutionQueueItem.status, ExecutionQueueItem.enqueued_at, cutoff),
        "audit_daily": [{"date": str(r[0]), "count": r[1]} for r in audit_rows],
    }


@router.get("/export")
def export_dashboard(db: Session = Depends(get_db),
                     user: User = Depends(require_permission("dashboard:read"))):
    """One-click CSV of the headline governance metrics for board/stakeholder circulation."""
    data = dashboard(db, user)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["metric", "value"])
    w.writerow(["pending_approvals", data["pending_approvals"]])
    w.writerow(["recommendations_total", data["recommendations_total"]])
    w.writerow(["prohibited_count", data["prohibited_count"]])
    w.writerow(["audit_event_count", data["audit_event_count"]])
    w.writerow(["audit_chain_verified", data["audit_chain_verified"]])
    w.writerow(["audit_head_seq", data["audit_head_seq"]])
    w.writerow(["active_pause_count", data["emergency"]["active_pause_count"]])
    w.writerow(["connectors_connected", data["connectors"]["connected"]])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=caul_dashboard.csv"})
