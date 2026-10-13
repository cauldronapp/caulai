"""Read-only, searchable, exportable, tamper-evident audit log + verification."""
import csv
import io
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditEvent, AuditCheckpoint, User
from ..deps import require_permission
from ..audit import verify_chain, create_checkpoint
from ..canonical import canonical_json

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _serialize(ev: AuditEvent) -> dict:
    return {
        "id": ev.id, "seq": ev.seq, "chain_env": ev.chain_env, "chain_org": ev.chain_org,
        "timestamp": ev.timestamp, "actor_id": ev.actor_id, "actor_label": ev.actor_label,
        "action": ev.action, "resource_type": ev.resource_type, "resource_id": ev.resource_id,
        "payload": ev.payload, "prev_hash": ev.prev_hash, "hash": ev.hash,
    }


@router.get("")
def list_events(db: Session = Depends(get_db),
                user: User = Depends(require_permission("audit:list")),
                q: str | None = Query(default=None),
                action: str | None = Query(default=None),
                resource_type: str | None = Query(default=None),
                limit: int = Query(default=200, le=1000)):
    stmt = select(AuditEvent).order_by(AuditEvent.seq.desc())
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    if resource_type:
        stmt = stmt.where(AuditEvent.resource_type == resource_type)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            AuditEvent.action.ilike(like), AuditEvent.actor_label.ilike(like),
            AuditEvent.resource_type.ilike(like), AuditEvent.resource_id.ilike(like),
            AuditEvent.hash.ilike(like),
        ))
    rows = db.execute(stmt.limit(limit)).scalars().all()
    return {"genesis_prev_hash": "0" * 64, "events": [_serialize(r) for r in rows]}


@router.get("/verify")
def verify(db: Session = Depends(get_db),
           user: User = Depends(require_permission("audit:verify"))):
    return verify_chain(db)


@router.post("/checkpoint")
def checkpoint(db: Session = Depends(get_db),
               user: User = Depends(require_permission("audit:verify"))):
    cp = create_checkpoint(db, note=f"manual by {user.display_name}")
    db.commit()
    if cp is None:  # pragma: no cover  (seeded chain is never empty via this route)
        return {"created": False, "reason": "empty chain"}
    return {"created": True, "seq": cp.seq, "hash": cp.hash, "event_count": cp.event_count}


@router.get("/checkpoints")
def checkpoints(db: Session = Depends(get_db),
                user: User = Depends(require_permission("audit:read"))):
    rows = db.execute(select(AuditCheckpoint).order_by(AuditCheckpoint.created_at.desc())).scalars().all()
    return [{"id": c.id, "seq": c.seq, "hash": c.hash, "event_count": c.event_count,
             "created_at": c.created_at.isoformat(), "note": c.note} for c in rows]


@router.get("/export")
def export_csv(fmt: str = Query(default="csv"), db: Session = Depends(get_db),
               user: User = Depends(require_permission("audit:export"))):
    rows = db.execute(select(AuditEvent).order_by(AuditEvent.seq.asc())).scalars().all()
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["seq", "timestamp", "actor_label", "action", "resource_type",
                    "resource_id", "prev_hash", "hash", "payload"])
        for ev in rows:
            w.writerow([ev.seq, ev.timestamp, ev.actor_label, ev.action, ev.resource_type,
                        ev.resource_id or "", ev.prev_hash, ev.hash, canonical_json(ev.payload)])
        buf.seek(0)
        return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=caul_audit_export.csv"})
    raise HTTPException(status_code=422, detail="Unsupported format")
