"""RBAC matrix integrity + default-deny invariants."""
from app.rbac_matrix import (
    PERMISSION_CATALOG, ROLE_PERMISSIONS, SERVICE_IDENTITY_FORBIDDEN, HIGH_RISK_PERMISSIONS,
)


def test_all_role_grants_reference_known_permissions():
    for role, grant in ROLE_PERMISSIONS.items():
        for p in grant:
            assert p in PERMISSION_CATALOG, f"Role {role} references unknown permission {p}"


def test_no_role_is_empty_default_deny():
    assert ROLE_PERMISSIONS["No-Role"] == set()


def test_service_identity_holds_no_forbidden_permissions():
    grant = ROLE_PERMISSIONS["Agent Service Identity"]
    assert grant.isdisjoint(SERVICE_IDENTITY_FORBIDDEN)
    # Service identity may never approve/grant/pause.
    for forbidden in ("approval:approve", "role:manage", "emergency:pause"):
        assert forbidden not in grant


def test_execowner_has_full_grant():
    assert ROLE_PERMISSIONS["ExecOwner"] == set(PERMISSION_CATALOG.keys())


def test_high_risk_permissions_are_known():
    for p in HIGH_RISK_PERMISSIONS:
        assert p in PERMISSION_CATALOG


def test_db_roles_match_matrix(db):
    from app.models import Role
    db_roles = {r.name for r in db.query(Role).all()}
    for role in ROLE_PERMISSIONS:
        assert role in db_roles, f"Seeded roles missing {role}"


def test_db_service_identity_has_no_forbidden_perms(db):
    from app.models import User
    agent = db.query(User).filter_by(email="agent-service@example.invalid").one()
    perms = {p.name for r in agent.roles for p in r.permissions}
    assert perms.isdisjoint(SERVICE_IDENTITY_FORBIDDEN)
