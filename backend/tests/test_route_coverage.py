"""CI route-permission coverage: every /api route must declare an explicit permission
(default-deny). Whitelisted routes are identity-only (no specific permission) or public.
"""
from starlette.routing import Route
from server import app
from app.deps import PermissionChecker

# Public or identity-only routes (no resource:action permission required).
# Cron/webhook endpoints are NOT listed here: they carry a `caul_webhook_auth` marker
# on their endpoint function (HMAC Bearer auth) which _is_covered() recognises, so any
# future cron route is auto-covered without editing this file.
WHITELIST = {
    ("GET", "/api/"),
    ("GET", "/api/health"),
    ("GET", "/api/health/ready"),
    ("GET", "/api/auth/provider"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/logout"),
    ("GET", "/api/auth/me"),
}


def _route_permission(route) -> str | None:
    for dep in route.dependant.dependencies:
        call = getattr(dep, "call", None)
        if isinstance(call, PermissionChecker):
            return call.caul_permission
        if hasattr(call, "caul_permission"):
            return call.caul_permission
    return None


def _is_webhook_authed(route) -> bool:
    return bool(getattr(getattr(route, "endpoint", None), "caul_webhook_auth", False))


def _api_routes():
    for r in app.routes:
        if isinstance(r, Route) and r.path.startswith("/api"):
            for method in (r.methods or []):
                if method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    yield method, r.path, r


def test_every_api_route_has_explicit_permission_or_is_whitelisted():
    missing = []
    for method, path, route in _api_routes():
        if (method, path) in WHITELIST:
            continue
        if _is_webhook_authed(route):  # HMAC/webhook-authenticated cron endpoints
            continue
        perm = _route_permission(route)
        if perm is None:
            missing.append(f"{method} {path}")
    assert not missing, f"Routes without an explicit permission (default-deny violation): {missing}"


def test_declared_permissions_exist_in_catalog():
    from app.rbac_matrix import PERMISSION_CATALOG
    for method, path, route in _api_routes():
        perm = _route_permission(route)
        if perm is not None:
            assert perm in PERMISSION_CATALOG, f"{method} {path} uses unknown permission {perm}"
