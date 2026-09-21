"""Admin: users + roles (RBAC matrix read)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Role, Permission
from ..deps import require_permission
from ..rbac_matrix import PERMISSION_CATALOG, HIGH_RISK_PERMISSIONS

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
def list_users(db: Session = Depends(get_db),
               user: User = Depends(require_permission("user:list"))):
    rows = db.execute(select(User).order_by(User.display_name)).scalars().all()
    return [{"id": u.id, "email": u.email, "display_name": u.display_name,
             "is_service_identity": u.is_service_identity, "is_stub": u.is_stub,
             "disabled": u.disabled, "roles": sorted(r.name for r in u.roles)} for u in rows]


@router.get("/roles")
def list_roles(db: Session = Depends(get_db),
               user: User = Depends(require_permission("role:list"))):
    rows = db.execute(select(Role).order_by(Role.name)).scalars().all()
    return [{"id": r.name, "name": r.name, "description": r.description,
             "permissions": sorted(p.name for p in r.permissions)} for r in rows]


@router.get("/permissions")
def list_permissions(db: Session = Depends(get_db),
                     user: User = Depends(require_permission("role:read"))):
    return {
        "matrix": [{"name": n, "description": d, "high_risk": n in HIGH_RISK_PERMISSIONS}
                   for n, d in sorted(PERMISSION_CATALOG.items())],
        "count": len(PERMISSION_CATALOG),
    }
