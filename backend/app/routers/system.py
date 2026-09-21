"""Settings (versioned), connectors (all not_connected), policies — read + settings update."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Setting, Connector, Policy, User
from ..deps import require_permission
from ..schemas import SettingUpdate
from .. import audit

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/settings")
def get_settings(db: Session = Depends(get_db),
                 user: User = Depends(require_permission("setting:read"))):
    rows = db.execute(select(Setting)).scalars().all()
    return [{"key": s.key, "value": s.value, "version": s.version,
             "updated_at": s.updated_at.isoformat()} for s in rows]


@router.put("/settings/{key}")
def update_setting(key: str, body: SettingUpdate, db: Session = Depends(get_db),
                   user: User = Depends(require_permission("setting:update"))):
    s = db.execute(select(Setting).where(Setting.key == key)).scalar_one_or_none()
    if s is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    old = s.value
    s.value = body.value
    s.version = s.version + 1
    s.updated_by = user.id
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="setting.updated", resource_type="setting", resource_id=key,
                       payload={"old": old, "new": body.value, "version": s.version})
    db.commit()
    return {"key": s.key, "value": s.value, "version": s.version}


@router.get("/connectors")
def list_connectors(db: Session = Depends(get_db),
                    user: User = Depends(require_permission("connector:list"))):
    rows = db.execute(select(Connector).order_by(Connector.name)).scalars().all()
    return [{"id": c.id, "name": c.name, "category": c.category, "status": c.status,
             "credential_fields": []} for c in rows]


@router.get("/policies")
def list_policies(db: Session = Depends(get_db),
                  user: User = Depends(require_permission("policy:list"))):
    rows = db.execute(select(Policy).order_by(Policy.name)).scalars().all()
    return [{"id": p.id, "name": p.name, "description": p.description, "rules": p.rules,
             "enabled": p.enabled, "version": p.version} for p in rows]
