"""Request-scoped auth + RBAC dependencies. Default-deny enforcement lives here."""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, Session as AuthSession
from .security import decode_token
from . import audit


def _extract_token(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if not token:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header[7:]
    return token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user = db.get(User, payload.get("sub"))
    if user is None or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled")
    if payload.get("ver", 0) != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalidated")

    # Server-side session validity (expiry + revocation).
    sess = db.execute(
        select(AuthSession).where(AuthSession.jti == payload.get("jti"))
    ).scalar_one_or_none()
    if sess is None or sess.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    if sess.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    return user


def user_permissions(user: User) -> set[str]:
    """Resolve the union of permissions across the user's roles from PostgreSQL."""
    perms: set[str] = set()
    for role in user.roles:
        for p in role.permissions:
            perms.add(p.name)
    return perms


def user_role_names(user: User) -> list[str]:
    return sorted(r.name for r in user.roles)


class PermissionChecker:
    """Callable dependency that enforces an explicit permission. Default-deny.

    Carries `caul_permission` so the CI route-coverage test can assert every
    protected route maps to a declared permission.
    """

    def __init__(self, permission: str):
        self.caul_permission = permission

    def __call__(self, request: Request, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)) -> User:
        perms = user_permissions(user)
        if self.caul_permission not in perms:
            # Audit the denied attempt (transactional).
            audit.append_event(
                db,
                actor_id=user.id, actor_label=user.display_name,
                action="authorization.denied", resource_type="route",
                resource_id=request.url.path[:255],
                payload={"required_permission": self.caul_permission,
                         "method": request.method, "roles": user_role_names(user)},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Default-deny: missing permission '{self.caul_permission}'",
            )
        return user


def require_permission(permission: str) -> PermissionChecker:
    if permission not in _known_permissions():
        raise RuntimeError(f"Unknown permission declared on route: {permission}")
    return PermissionChecker(permission)


def _known_permissions() -> set[str]:
    from .rbac_matrix import PERMISSION_CATALOG
    return set(PERMISSION_CATALOG.keys())
