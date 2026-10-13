"""Idempotent seed with production guards.

Guards (Rejection criteria: demo/seed must never reach a production path):
  - Refuses to run unless APP_ENV is exactly 'dev' or 'staging'.
  - Refuses if the connected database name is not the expected dev/staging name.
  - All seeded identities are synthetic, marked is_stub=True, and use non-deliverable
    *.invalid addresses. They are seeded ONLY into the dev/staging databases.

Seeds: permission catalog, roles + role->permission grants, synthetic stub users,
settings ($24.99/mo subscription, 2.30% fee), connectors (all not_connected),
sample policies, and demo recommendations/approvals for the Command Center.
"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .config import get_app_env
from .database import SessionLocal, engine
from .models import (
    User, Role, Permission, UserRole, RolePermission, Recommendation, Approval,
    Setting, Connector, Policy,
)
from .rbac_matrix import (
    PERMISSION_CATALOG, ROLE_PERMISSIONS, SERVICE_IDENTITY_FORBIDDEN,
)
from .security import hash_password
from .canonical import payload_digest
from . import audit

EXPECTED_DB = {"dev": "caul_dev", "staging": "caul_staging"}

# Synthetic stub identities (non-deliverable *.invalid). Never real personal data.
STUB_PASSWORD = "StubPass!2026"
STUB_USERS = [
    {"key": "execowner", "email": "execowner@example.invalid",
     "name": "Sean Gaden — Demo ExecOwner", "role": "ExecOwner", "service": False},
    {"key": "admin", "email": "admin@example.invalid",
     "name": "Demo Admin", "role": "Admin", "service": False},
    {"key": "marketing", "email": "marketing@example.invalid",
     "name": "Demo Marketing Manager", "role": "Marketing Manager", "service": False},
    {"key": "developer", "email": "developer@example.invalid",
     "name": "Demo Developer", "role": "Developer", "service": False},
    {"key": "security", "email": "security@example.invalid",
     "name": "Demo Security/Compliance", "role": "Security/Compliance", "service": False},
    {"key": "analyst", "email": "analyst@example.invalid",
     "name": "Demo Analyst", "role": "Analyst", "service": False},
    {"key": "auditor", "email": "auditor@example.invalid",
     "name": "Demo Auditor", "role": "Auditor", "service": False},
    {"key": "agent", "email": "agent-service@example.invalid",
     "name": "Demo Agent Service Identity", "role": "Agent Service Identity", "service": True},
    {"key": "norole", "email": "norole@example.invalid",
     "name": "Demo No-Role (default-deny test)", "role": "No-Role", "service": False},
]


class SeedGuardError(RuntimeError):
    pass


def _assert_safe_to_seed(db: Session):
    env = get_app_env()  # raises if not dev/staging
    dbname = db.execute(text("SELECT current_database()")).scalar_one()
    if dbname != EXPECTED_DB.get(env):
        raise SeedGuardError(
            f"Refusing to seed: connected DB '{dbname}' does not match expected "
            f"'{EXPECTED_DB.get(env)}' for APP_ENV='{env}'. Production guard engaged."
        )


def _get_or_create_permissions(db: Session) -> dict[str, Permission]:
    by_name: dict[str, Permission] = {
        p.name: p for p in db.execute(select(Permission)).scalars().all()
    }
    for name, desc in PERMISSION_CATALOG.items():
        if name not in by_name:
            resource, action = name.split(":", 1)
            perm = Permission(name=name, resource=resource, action=action, description=desc)
            db.add(perm)
            by_name[name] = perm
    db.flush()
    return by_name


def _get_or_create_roles(db: Session, perms: dict[str, Permission]) -> dict[str, Role]:
    by_name: dict[str, Role] = {r.name: r for r in db.execute(select(Role)).scalars().all()}
    for role_name, grant in ROLE_PERMISSIONS.items():
        role = by_name.get(role_name)
        if role is None:
            role = Role(name=role_name, description=f"{role_name} (system role)", is_system=True)
            db.add(role)
            db.flush()
            by_name[role_name] = role

        # Service identity may never hold forbidden permissions (hard guard).
        effective = set(grant)
        if role_name == "Agent Service Identity":
            effective -= SERVICE_IDENTITY_FORBIDDEN

        current = {rp.permission_id for rp in db.execute(
            select(RolePermission).where(RolePermission.role_id == role.id)
        ).scalars().all()}
        want_ids = {perms[p].id for p in effective if p in perms}
        for pid in want_ids - current:
            db.add(RolePermission(role_id=role.id, permission_id=pid))
    db.flush()
    return by_name


def _get_or_create_users(db: Session, roles: dict[str, Role]):
    for spec in STUB_USERS:
        existing = db.execute(select(User).where(User.email == spec["email"])).scalar_one_or_none()
        if existing is None:
            user = User(
                subject=f"stub|{spec['key']}", email=spec["email"], display_name=spec["name"],
                password_hash=hash_password(STUB_PASSWORD),
                is_service_identity=spec["service"], is_stub=True,
            )
            db.add(user)
            db.flush()
        else:
            user = existing
        role = roles.get(spec["role"])
        if role is not None:
            link = db.execute(
                select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
            ).scalar_one_or_none()
            if link is None:
                db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()


def _seed_settings(db: Session):
    defaults = {
        "subscription": {"label": "CAUL AI Subscription", "amount": 24.99, "currency": "USD", "period": "month"},
        "platform_fee": {"label": "Platform Fee", "percent": 2.30},
    }
    for key, value in defaults.items():
        if db.execute(select(Setting).where(Setting.key == key)).scalar_one_or_none() is None:
            db.add(Setting(key=key, value=value, version=1))
    db.flush()


def _seed_connectors(db: Session):
    names = [
        ("Google Ads", "advertising"), ("Meta Ads", "advertising"), ("Stripe", "payments"),
        ("Slack", "messaging"), ("HubSpot", "crm"), ("Snowflake", "data"),
    ]
    for name, cat in names:
        if db.execute(select(Connector).where(Connector.name == name)).scalar_one_or_none() is None:
            db.add(Connector(name=name, category=cat, status="not_connected"))
    db.flush()


def _seed_policies(db: Session):
    policies = [
        {"name": "High-risk dual approval", "description": "High-risk actions require two distinct reviewers.",
         "rules": {"risk_level": "high", "required_approvals": 2}},
        {"name": "Prohibited: production DB access", "description": "Direct Cauldron production DB access is permanently prohibited.",
         "rules": {"tier": "permanently_prohibited"}},
    ]
    for p in policies:
        if db.execute(select(Policy).where(Policy.name == p["name"]).limit(1)).scalar_one_or_none() is None:
            db.add(Policy(**p))
    db.flush()


def _seed_demo_recommendations(db: Session, users: dict[str, User]):
    if db.execute(select(Recommendation).limit(1)).scalar_one_or_none() is not None:
        return
    marketing = users.get("marketing@example.invalid")
    agent = users.get("agent-service@example.invalid")
    demos = [
        {"title": "Increase Q3 email cadence to weekly", "tier": "auto", "risk_level": "low",
         "category": "marketing", "submitter": marketing,
         "payload": {"campaign": "q3-nurture", "cadence": "weekly"}},
        {"title": "Reallocate $12k ad budget to top segment", "tier": "requires_approval",
         "risk_level": "high", "category": "advertising", "submitter": agent,
         "payload": {"from": "broad", "to": "segment-A", "amount_usd": 12000}},
        {"title": "Enable direct Cauldron production DB sync", "tier": "permanently_prohibited",
         "risk_level": "high", "category": "infrastructure", "submitter": agent,
         "payload": {"target": "cauldron_prod_db"}},
    ]
    for d in demos:
        submitter = d["submitter"]
        if submitter is None:
            continue
        digest = payload_digest(d["payload"])
        required = 2 if d["risk_level"] == "high" else 1
        status = {"auto": "auto_approved", "requires_approval": "pending",
                  "permanently_prohibited": "prohibited"}[d["tier"]]
        rec = Recommendation(
            title=d["title"], description=d["title"], category=d["category"], tier=d["tier"],
            risk_level=d["risk_level"], action_payload=d["payload"], payload_digest=digest,
            required_approvals=required, submitted_by=submitter.id, status=status,
        )
        db.add(rec)
        db.flush()
        if d["tier"] == "requires_approval":
            db.add(Approval(recommendation_id=rec.id, payload_digest=digest, status="pending",
                            required_approvals=required,
                            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)))
        audit.append_event(db, actor_id=submitter.id, actor_label=submitter.display_name,
                           action="recommendation.submitted", resource_type="recommendation",
                           resource_id=rec.id,
                           payload={"tier": d["tier"], "risk_level": d["risk_level"],
                                    "payload_digest": digest, "seed": True})
    db.flush()


def run_seed() -> dict:
    db = SessionLocal()
    try:
        _assert_safe_to_seed(db)
        perms = _get_or_create_permissions(db)
        roles = _get_or_create_roles(db, perms)
        _get_or_create_users(db, roles)
        _seed_settings(db)
        _seed_connectors(db)
        _seed_policies(db)
        users = {u.email: u for u in db.execute(select(User)).scalars().all()}
        _seed_demo_recommendations(db, users)
        # Genesis-anchoring audit event if the chain is empty is created by demo recs;
        # ensure at least one system event exists.
        db.commit()
        return {"seeded": True, "env": get_app_env(),
                "permissions": len(perms), "roles": len(roles), "users": len(STUB_USERS)}
    except Exception:  # pragma: no cover  (defensive: surface seed failures)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(run_seed())
