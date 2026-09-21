"""Notifications."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Notification, User
from ..deps import require_permission, get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _serialize(n: Notification) -> dict:
    return {"id": n.id, "kind": n.kind, "title": n.title, "body": n.body,
            "read": n.read, "created_at": n.created_at.isoformat()}


@router.get("")
def list_notifications(db: Session = Depends(get_db),
                       user: User = Depends(require_permission("notification:list"))):
    rows = db.execute(
        select(Notification)
        .where((Notification.user_id == user.id) | (Notification.user_id.is_(None)))
        .order_by(Notification.created_at.desc())
    ).scalars().all()
    return [_serialize(n) for n in rows]


@router.post("/{notification_id}/read")
def mark_read(notification_id: str, db: Session = Depends(get_db),
              user: User = Depends(require_permission("notification:update"))):
    n = db.get(Notification, notification_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.commit()
    return _serialize(n)


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db),
                  user: User = Depends(require_permission("notification:update"))):
    db.execute(update(Notification)
               .where((Notification.user_id == user.id) | (Notification.user_id.is_(None)))
               .values(read=True))
    db.commit()
    return {"ok": True}
