"""AUTH STUB routes (dev/staging only). Provider-neutral adapter + PostgreSQL RBAC."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Session as AuthSession
from ..security import verify_password, create_access_token
from ..config import get_session_ttl_minutes
from ..auth_provider import identity_provider, STUB_LABEL
from ..deps import get_current_user, user_permissions, user_role_names
from ..schemas import LoginRequest, UserOut
from .. import audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id, email=user.email, display_name=user.display_name,
        is_service_identity=user.is_service_identity, is_stub=user.is_stub,
        roles=user_role_names(user), permissions=sorted(user_permissions(user)),
    )


@router.get("/provider")
def provider_info():
    """Expose the labeled stub provider metadata (AUTH STUB — NOT PRODUCTION)."""
    return identity_provider.describe()


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or user.disabled or not verify_password(body.password, user.password_hash):
        # Audit failed attempt.
        audit.append_event(db, actor_id=user.id if user else None,
                           actor_label=email, action="auth.login_failed",
                           resource_type="session", resource_id=None,
                           payload={"provider": identity_provider.name, "stub": True})
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid stub credentials")

    # Service identities are non-interactive and cannot start interactive sessions.
    if user.is_service_identity:
        audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                           action="auth.login_denied_service_identity",
                           resource_type="session", resource_id=None, payload={"stub": True})
        db.commit()
        raise HTTPException(status_code=403,
                            detail="Agent Service Identity is non-interactive and cannot log in.")

    # Identity confirmed by provider-neutral stub (identity only, no roles from IdP).
    identity_provider.describe()  # ensures stub is the active provider
    jti = str(uuid.uuid4())
    token, expires = create_access_token(user.id, user.email, user.token_version, jti)
    db.add(AuthSession(user_id=user.id, jti=jti, expires_at=expires, revoked=False))
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="auth.login", resource_type="session", resource_id=jti,
                       payload={"provider": identity_provider.name, "stub": True,
                                "label": STUB_LABEL})
    db.commit()

    response.set_cookie(key="access_token", value=token, httponly=True, secure=True,
                        samesite="none", max_age=get_session_ttl_minutes() * 60, path="/")
    return _user_out(user)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    token = request.cookies.get("access_token")
    if token:
        from ..security import decode_token
        try:
            jti = decode_token(token).get("jti")
            sess = db.execute(select(AuthSession).where(AuthSession.jti == jti)).scalar_one_or_none()
            if sess:
                sess.revoked = True
        except Exception:
            pass
    audit.append_event(db, actor_id=user.id, actor_label=user.display_name,
                       action="auth.logout", resource_type="session", resource_id=None, payload={})
    db.commit()
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
