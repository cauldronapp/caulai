"""Emergency controls (STUB paths only): global + granular pause, resume, revocation,
execution-queue cancel/drain, and rollback of rollback-eligible items."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PauseState, ExecutionQueueItem, Recommendation, User
from ..deps import require_permission
from ..schemas import PauseRequest
from .. import audit

router = APIRouter(prefix="/api/emergency", tags=["emergency"])

STUB_NOTE = "Operates against STUB paths only; not proven for live connectors."


@router.get("")
def status(db: Session = Depends(get_db),
           user: User = Depends(require_permission("emergency:read"))):
    rows = db.execute(select(PauseState).order_by(PauseState.scope)).scalars().all()
    queue = db.execute(select(ExecutionQueueItem).order_by(ExecutionQueueItem.enqueued_at.desc())).scalars().all()
    return {
        "stub_note": STUB_NOTE,
        "global_paused": any(p.scope == "global" and p.active for p in rows),
        "pauses": [{"id": p.id, "scope": p.scope, "target": p.target, "active": p.active,
                    "reason": p.reason,
                    "engaged_at": p.engaged_at.isoformat() if p.engaged_at else None} for p in rows],
        "queue": [{"id": q.id, "recommendation_id": q.recommendation_id, "connector": q.connector,
                   "status": q.status, "irreversible": q.irreversible,
                   "rollback_eligible": q.rollback_eligible,
                   "enqueued_at": q.enqueued_at.isoformat()} for q in queue],
    }


@router.post("/pause")
def pause(body: PauseRequest, db: Session = Depends(get_db),
          user: User = Depends(require_permission("emergency:pause"))):
    if body.scope not in ("global", "granular"):
        raise HTTPException(status_code=422, detail="scope must be global or granular")
    existing = db.execute(select(PauseState).where(
        PauseState.scope == body.scope, PauseState.target == body.target)).scalars().first()
    now = datetime.now(timezone.utc)
    if existing is None:
        existing = PauseState(scope=body.scope, target=body.target)
        db.add(existing)
    existing.active = True
    existing.reason = body.reason
    existing.engaged_by = user.id
    existing.engaged_at = now
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="emergency.pause", resource_type="emergency",
                       resource_id=f"{body.scope}:{body.target}",
                       payload={"scope": body.scope, "target": body.target,
                                "reason": body.reason, "stub_note": STUB_NOTE})
    db.commit()
    return {"ok": True, "scope": body.scope, "target": body.target, "active": True}


@router.post("/resume")
def resume(body: PauseRequest, db: Session = Depends(get_db),
           user: User = Depends(require_permission("emergency:resume"))):
    existing = db.execute(select(PauseState).where(
        PauseState.scope == body.scope, PauseState.target == body.target)).scalars().first()
    if existing is None or not existing.active:
        raise HTTPException(status_code=404, detail="No active pause for that scope/target")
    existing.active = False
    existing.released_by = user.id
    existing.released_at = datetime.now(timezone.utc)
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="emergency.resume", resource_type="emergency",
                       resource_id=f"{body.scope}:{body.target}",
                       payload={"scope": body.scope, "target": body.target})
    db.commit()
    return {"ok": True, "scope": body.scope, "target": body.target, "active": False}


@router.post("/queue/{item_id}/cancel")
def cancel_item(item_id: str, db: Session = Depends(get_db),
                user: User = Depends(require_permission("emergency:revoke"))):
    item = db.get(ExecutionQueueItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if item.status not in ("queued", "executing"):
        raise HTTPException(status_code=409, detail=f"Cannot cancel item in status {item.status}")
    item.status = "cancelled"
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="emergency.queue_cancel", resource_type="execution_queue",
                       resource_id=item.id, payload={"recommendation_id": item.recommendation_id})
    db.commit()
    return {"ok": True, "id": item.id, "status": item.status}


@router.post("/queue/drain")
def drain_queue(db: Session = Depends(get_db),
                user: User = Depends(require_permission("emergency:revoke"))):
    items = db.execute(select(ExecutionQueueItem).where(
        ExecutionQueueItem.status.in_(["queued", "executing"]))).scalars().all()
    for it in items:
        it.status = "drained"
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="emergency.queue_drain", resource_type="execution_queue",
                       resource_id=None, payload={"drained_count": len(items)})
    db.commit()
    return {"ok": True, "drained": len(items)}


@router.post("/revoke/{recommendation_id}")
def revoke_execution(recommendation_id: str, db: Session = Depends(get_db),
                     user: User = Depends(require_permission("emergency:revoke"))):
    """Emergency revocation: cancel any pending queue items for a recommendation and mark it revoked."""
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    items = db.execute(select(ExecutionQueueItem).where(
        ExecutionQueueItem.recommendation_id == recommendation_id,
        ExecutionQueueItem.status.in_(["queued", "executing"]))).scalars().all()
    for it in items:
        it.status = "cancelled"
    rec.status = "revoked"
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="emergency.revoke", resource_type="recommendation",
                       resource_id=rec.id, payload={"cancelled_items": len(items), "stub_note": STUB_NOTE})
    db.commit()
    return {"ok": True, "recommendation_id": rec.id, "cancelled_items": len(items)}


@router.post("/rollback/{item_id}")
def rollback_item(item_id: str, db: Session = Depends(get_db),
                  user: User = Depends(require_permission("emergency:revoke"))):
    item = db.get(ExecutionQueueItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Queue item not found")
    if item.irreversible:
        raise HTTPException(status_code=409,
                            detail="Irreversible action cannot be rolled back (see irreversible-action warning).")
    if not item.rollback_eligible:
        raise HTTPException(status_code=409, detail="Item is not rollback-eligible")
    if item.status != "executed":
        raise HTTPException(status_code=409, detail=f"Only executed items can be rolled back (status={item.status})")
    item.status = "rolled_back"
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="emergency.rollback", resource_type="execution_queue",
                       resource_id=item.id, payload={"recommendation_id": item.recommendation_id})
    db.commit()
    return {"ok": True, "id": item.id, "status": item.status}
