"""Server-side RBAC. Default-deny. Complete resource x action permission matrix.

Every protected route declares an explicit permission via require_permission(...).
Authorization is resolved from PostgreSQL (roles -> permissions), never from the IdP.
The permission catalog and the role->permission grants below are the source of truth
that the seed script loads into the database, and the CI route-coverage test checks
that every /api route maps to an explicit permission.
"""
from itertools import product

# ---- Complete resource x action matrix ----
RESOURCES = [
    "dashboard", "recommendation", "approval", "audit", "policy", "connector",
    "emergency", "user", "role", "setting", "notification", "session",
]
ACTIONS = [
    "read", "list", "create", "update", "delete",
    "approve", "reject", "export", "verify",
    "pause", "resume", "revoke", "assign_role", "manage",
]

# Only a curated subset of (resource, action) pairs are meaningful permissions.
PERMISSION_CATALOG: dict[str, str] = {
    # dashboard
    "dashboard:read": "View the governance dashboard",
    # recommendations
    "recommendation:list": "List recommendations",
    "recommendation:read": "Read a recommendation",
    "recommendation:create": "Create a recommendation",
    "recommendation:update": "Update a recommendation payload",
    "recommendation:execute": "Enqueue an approved recommendation for (stub) execution",
    # approvals
    "approval:list": "List approvals",
    "approval:read": "Read an approval",
    "approval:approve": "Cast an approve decision",
    "approval:reject": "Cast a reject decision",
    "approval:revoke": "Revoke an approval",
    # audit (read-only + export + verify; NEVER update/delete)
    "audit:list": "List audit events",
    "audit:read": "Read an audit event",
    "audit:export": "Export audit events",
    "audit:verify": "Run audit chain verification",
    # policies
    "policy:list": "List policies",
    "policy:read": "Read a policy",
    "policy:update": "Update a policy",
    # connectors
    "connector:list": "List connectors",
    "connector:read": "Read a connector",
    "connector:test": "Run the connector contract-test suite (stub)",
    # emergency
    "emergency:read": "View emergency controls",
    "emergency:pause": "Engage a pause",
    "emergency:resume": "Release a pause",
    "emergency:revoke": "Revoke/queue-cancel actions",
    # users / roles admin
    "user:list": "List users",
    "user:read": "Read a user",
    "user:manage": "Create/update/disable users",
    "user:assign_role": "Assign roles to users",
    "role:list": "List roles",
    "role:read": "Read a role and its permissions",
    "role:manage": "Create/update roles and grants",
    # settings
    "setting:read": "Read settings",
    "setting:update": "Update settings (versioned)",
    # notifications
    "notification:list": "List notifications",
    "notification:read": "Read a notification",
    "notification:update": "Mark notifications read",
}

# Permissions considered high-risk for approval safeguards (self-approval forbidden, quorum).
HIGH_RISK_PERMISSIONS = {
    "emergency:pause", "emergency:resume", "emergency:revoke",
    "role:manage", "user:manage", "user:assign_role", "setting:update",
}

# ---- Role -> permission grants (source of truth, loaded by seed) ----
ALL_PERMS = set(PERMISSION_CATALOG.keys())

ROLE_PERMISSIONS: dict[str, set[str]] = {
    # Executive Owner (Sean) — only production Super Admin (production not in 1A). Full grant.
    "ExecOwner": set(ALL_PERMS),
    "Admin": {
        "dashboard:read",
        "recommendation:list", "recommendation:read", "recommendation:create", "recommendation:update",
        "approval:list", "approval:read", "approval:approve", "approval:reject", "approval:revoke",
        "audit:list", "audit:read", "audit:export", "audit:verify",
        "policy:list", "policy:read", "policy:update",
        "connector:list", "connector:read",
        "emergency:read", "emergency:pause", "emergency:resume", "emergency:revoke",
        "user:list", "user:read", "user:manage", "user:assign_role",
        "role:list", "role:read", "role:manage",
        "setting:read", "setting:update",
        "notification:list", "notification:read",
    },
    "Marketing Manager": {
        "dashboard:read",
        "recommendation:list", "recommendation:read", "recommendation:create",
        "approval:list", "approval:read",
        "notification:list", "notification:read",
        "connector:list", "connector:read",
    },
    "Developer": {
        "dashboard:read",
        "recommendation:list", "recommendation:read",
        "audit:list", "audit:read",
        "connector:list", "connector:read",
        "policy:list", "policy:read",
        "notification:list", "notification:read",
    },
    "Security/Compliance": {
        "dashboard:read",
        "recommendation:list", "recommendation:read",
        "approval:list", "approval:read",
        "audit:list", "audit:read", "audit:export", "audit:verify",
        "emergency:read", "emergency:pause", "emergency:resume", "emergency:revoke",
        "policy:list", "policy:read",
        "connector:list", "connector:read",
        "notification:list", "notification:read",
    },
    "Analyst": {
        "dashboard:read",
        "recommendation:list", "recommendation:read",
        "audit:list", "audit:read",
        "notification:list", "notification:read",
    },
    "Auditor": {
        "dashboard:read",
        "approval:list", "approval:read",
        "audit:list", "audit:read", "audit:export", "audit:verify",
        "notification:list", "notification:read",
    },
    # Non-interactive service identity: may READ and CREATE recommendations only.
    # It must NEVER approve, grant, pause, resume, revoke, or manage anything.
    "Agent Service Identity": {
        "recommendation:list", "recommendation:read", "recommendation:create",
    },
    # No-Role user has an empty grant set to exercise default-deny.
    "No-Role": set(),
}

# Permissions no service identity may ever hold (enforced by seed + tests).
SERVICE_IDENTITY_FORBIDDEN = {
    "approval:approve", "approval:reject", "approval:revoke",
    "role:manage", "user:manage", "user:assign_role",
    "emergency:pause", "emergency:resume", "emergency:revoke",
    "setting:update", "policy:update",
    "recommendation:execute",
}

# --- Foundation-continuation grants (new permissions added this milestone) ---
for _r in ("Admin", "Marketing Manager", "Developer", "Security/Compliance", "Analyst", "Auditor"):
    ROLE_PERMISSIONS[_r].add("notification:update")
ROLE_PERMISSIONS["Admin"].update({"recommendation:execute", "connector:test"})
ROLE_PERMISSIONS["Security/Compliance"].update({"connector:test"})
ROLE_PERMISSIONS["Developer"].update({"connector:test"})
# ExecOwner is set(ALL_PERMS) computed above and already includes the new permissions.


def is_high_risk(permission: str) -> bool:
    return permission in HIGH_RISK_PERMISSIONS


def all_permissions() -> dict[str, str]:
    return dict(PERMISSION_CATALOG)
