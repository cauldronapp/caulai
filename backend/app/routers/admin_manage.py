"""Admin management: create/update/disable users, assign roles, create/update roles."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Role, UserRole, Permission, RolePermission
from ..deps import require_permission
from ..security import hash_password
from .. import audit

router = APIRouter(prefix="/api/admin", tags=["admin-manage"])


class UserCreate(BaseModel):
    email: str
    display_name: str
    password: str = "StubPass!2026"
    is_service_identity: bool = False


class RoleAssign(BaseModel):
    role_names: list[str]


class RoleUpsert(BaseModel):
    name: str
    description: str = ""
    permissions: list[str] = []


@router.post("/users")
def create_user(body: UserCreate, db: Session = Depends(get_db),
                user: User = Depends(require_permission("user:manage"))):
    if not body.email.endswith(".invalid"):
        raise HTTPException(status_code=422, detail="Stub users must use a non-deliverable .invalid address")
    if db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists")
    u = User(subject=f"stub|{body.email.split('@')[0]}", email=body.email.lower(),
             display_name=body.display_name, password_hash=hash_password(body.password),
             is_service_identity=body.is_service_identity, is_stub=True)
    db.add(u)
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="user.created", resource_type="user", resource_id=u.id,
                       payload={"email": u.email, "is_service_identity": u.is_service_identity})
    db.commit()
    db.refresh(u)
    return {"id": u.id, "email": u.email, "display_name": u.display_name}


@router.post("/users/{user_id}/disable")
def disable_user(user_id: str, db: Session = Depends(get_db),
                 user: User = Depends(require_permission("user:manage"))):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    target.disabled = not target.disabled
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="user.disabled_toggled", resource_type="user", resource_id=target.id,
                       payload={"disabled": target.disabled})
    db.commit()
    return {"id": target.id, "disabled": target.disabled}


@router.post("/users/{user_id}/roles")
def assign_roles(user_id: str, body: RoleAssign, db: Session = Depends(get_db),
                 user: User = Depends(require_permission("user:assign_role"))):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Guard: a service identity may never be granted approver/grantor roles is enforced by
    # SERVICE_IDENTITY_FORBIDDEN at seed; here we still forbid assigning privileged roles to services.
    roles = db.execute(select(Role).where(Role.name.in_(body.role_names))).scalars().all()
    if target.is_service_identity and any(r.name != "Agent Service Identity" for r in roles):
        raise HTTPException(status_code=403, detail="Service identities may only hold the Agent Service Identity role")
    db.query(UserRole).filter(UserRole.user_id == target.id).delete()
    for r in roles:
        db.add(UserRole(user_id=target.id, role_id=r.id))
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="user.roles_assigned", resource_type="user", resource_id=target.id,
                       payload={"roles": [r.name for r in roles]})
    db.commit()
    return {"id": target.id, "roles": [r.name for r in roles]}


@router.post("/roles")
def upsert_role(body: RoleUpsert, db: Session = Depends(get_db),
                user: User = Depends(require_permission("role:manage"))):
    role = db.execute(select(Role).where(Role.name == body.name)).scalar_one_or_none()
    if role is None:
        role = Role(name=body.name, description=body.description, is_system=False)
        db.add(role)
        db.flush()
    else:
        role.description = body.description
    perms = db.execute(select(Permission).where(Permission.name.in_(body.permissions))).scalars().all()
    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id))
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="role.upserted", resource_type="role", resource_id=role.id,
                       payload={"name": role.name, "permissions": [p.name for p in perms]})
    db.commit()
    return {"id": role.id, "name": role.name, "permissions": [p.name for p in perms]}
