"""Emergency controls (operate against STUB paths only). Pause/resume/revoke."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PauseState, User
from ..deps import require_permission
from ..schemas import PauseRequest
from .. import audit

router = APIRouter(prefix="/api/emergency", tags=["emergency"])

STUB_NOTE = "Operates against STUB paths only; not proven for live connectors."


@router.get("")
def status(db: Session = Depends(get_db),
           user: User = Depends(require_permission("emergency:read"))):
    rows = db.execute(select(PauseState).order_by(PauseState.scope)).scalars().all()
    active = [p for p in rows if p.active]
    return {
        "stub_note": STUB_NOTE,
        "global_paused": any(p.scope == "global" and p.active for p in rows),
        "active_pauses": [{"id": p.id, "scope": p.scope, "target": p.target,
                           "reason": p.reason, "engaged_at": p.engaged_at.isoformat() if p.engaged_at else None}
                          for p in active],
        "all": [{"id": p.id, "scope": p.scope, "target": p.target, "active": p.active,
                 "reason": p.reason} for p in rows],
    }


@router.post("/pause")
def pause(body: PauseRequest, db: Session = Depends(get_db),
          user: User = Depends(require_permission("emergency:pause"))):
    if body.scope not in ("global", "granular"):
        raise HTTPException(status_code=422, detail="scope must be global or granular")
    existing = db.execute(select(PauseState).where(
        PauseState.scope == body.scope, PauseState.target == body.target)).scalar_one_or_none()
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
                       payload={"scope": body.scope, "target": body.target, "reason": body.reason,
                                "stub_note": STUB_NOTE})
    db.commit()
    return {"ok": True, "scope": body.scope, "target": body.target, "active": True}


@router.post("/resume")
def resume(body: PauseRequest, db: Session = Depends(get_db),
           user: User = Depends(require_permission("emergency:resume"))):
    existing = db.execute(select(PauseState).where(
        PauseState.scope == body.scope, PauseState.target == body.target)).scalar_one_or_none()
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
