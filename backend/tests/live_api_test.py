"""Live API tests against REACT_APP_BACKEND_URL for CAUL AI Phase 1A."""
import os
import re
import requests

with open("/app/frontend/.env") as f:
    for line in f:
        m = re.match(r"REACT_APP_BACKEND_URL=(.+)", line.strip())
        if m:
            BASE = m.group(1).rstrip("/")
            break

PW = "StubPass!2026"

def login(email):
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"email": email, "password": PW})
    return s, r

def test_provider_stub_banner():
    r = requests.get(f"{BASE}/api/auth/provider")
    assert r.status_code == 200
    j = r.json()
    assert j["is_stub"] is True
    assert "STUB" in j["label"]

def test_all_interactive_stubs_login_and_me():
    users = [
        "execowner@example.invalid","admin@example.invalid","marketing@example.invalid",
        "developer@example.invalid","security@example.invalid","analyst@example.invalid",
        "auditor@example.invalid"
    ]
    for email in users:
        s, r = login(email)
        assert r.status_code == 200, f"{email} login failed: {r.status_code} {r.text}"
        # httpOnly cookie set
        cookies = s.cookies.get_dict()
        assert "access_token" in cookies, f"no cookie for {email}"
        me = s.get(f"{BASE}/api/auth/me")
        assert me.status_code == 200, f"me failed for {email}"
        body = me.json()
        assert body["email"] == email
        assert isinstance(body.get("roles"), list)
        assert isinstance(body.get("permissions"), list)

def test_agent_service_login_blocked():
    _, r = login("agent-service@example.invalid")
    assert r.status_code == 403, f"expected 403, got {r.status_code}"

def test_norole_default_deny():
    s, r = login("norole@example.invalid")
    assert r.status_code == 200
    d = s.get(f"{BASE}/api/dashboard")
    assert d.status_code == 403, f"expected 403 on dashboard, got {d.status_code}"

def test_rbac_auditor():
    s, _ = login("auditor@example.invalid")
    assert s.get(f"{BASE}/api/audit").status_code == 200
    assert s.get(f"{BASE}/api/audit/export?fmt=csv").status_code == 200
    r = s.post(f"{BASE}/api/emergency/pause", json={"reason": "test"})
    assert r.status_code == 403

def test_rbac_marketing():
    s, _ = login("marketing@example.invalid")
    # POST recommendations - allowed
    r = s.post(f"{BASE}/api/recommendations", json={"title": "TEST_rec", "description": "t", "risk_tier": "low"})
    assert r.status_code in (200, 201, 400, 422), f"unexpected {r.status_code}: {r.text}"
    # Should not be able to approve
    r2 = s.post(f"{BASE}/api/approvals/nonexistent/approve", json={})
    assert r2.status_code == 403, f"expected 403 approve, got {r2.status_code}"

def test_execowner_broad_access():
    s, _ = login("execowner@example.invalid")
    assert s.get(f"{BASE}/api/dashboard").status_code == 200
    assert s.get(f"{BASE}/api/audit").status_code == 200
    assert s.get(f"{BASE}/api/approvals").status_code == 200

def test_logout_revokes_session():
    s, _ = login("admin@example.invalid")
    assert s.get(f"{BASE}/api/auth/me").status_code == 200
    lo = s.post(f"{BASE}/api/auth/logout")
    assert lo.status_code in (200, 204)
    me = s.get(f"{BASE}/api/auth/me")
    assert me.status_code == 401, f"expected 401 after logout, got {me.status_code}"

def test_audit_verify_and_search_and_export():
    s, _ = login("auditor@example.invalid")
    v = s.get(f"{BASE}/api/audit/verify")
    assert v.status_code == 200
    assert v.json().get("verified") is True
    q = s.get(f"{BASE}/api/audit?q=genesis")
    assert q.status_code == 200
    csv = s.get(f"{BASE}/api/audit/export?fmt=csv")
    assert csv.status_code == 200
    assert "text/csv" in csv.headers.get("content-type", "").lower() or csv.text.count(",") > 0
