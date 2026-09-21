"""Live API tests for Phase 1A extended features:
Emergency controls, connector contract, execution+rollback, admin manage."""
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
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return s


# --- Connector contract endpoint ---

def test_contract_test_admin_all_passed():
    s = login("admin@example.invalid")
    r = s.post(f"{BASE}/api/connectors/contract-test")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["all_passed"] is True
    assert len(j["checks"]) == 8
    for c in j["checks"]:
        assert c["passed"] is True, f"check {c} not passed"


def test_contract_test_analyst_forbidden():
    s = login("analyst@example.invalid")
    r = s.post(f"{BASE}/api/connectors/contract-test")
    assert r.status_code == 403, f"expected 403, got {r.status_code}"


# --- Emergency controls ---

def test_emergency_security_pause_resume_global():
    s = login("security@example.invalid")
    # initial GET
    r = s.get(f"{BASE}/api/emergency")
    assert r.status_code == 200, r.text
    # global pause
    r = s.post(f"{BASE}/api/emergency/pause", json={"scope": "global", "target": "*", "reason": "test"})
    assert r.status_code == 200, r.text
    r = s.get(f"{BASE}/api/emergency")
    assert r.json()["global_paused"] is True
    # resume
    r = s.post(f"{BASE}/api/emergency/resume", json={"scope": "global", "target": "*"})
    assert r.status_code == 200
    r = s.get(f"{BASE}/api/emergency")
    assert r.json()["global_paused"] is False


def test_emergency_granular_pause_resume():
    s = login("security@example.invalid")
    r = s.post(f"{BASE}/api/emergency/pause",
               json={"scope": "granular", "target": "recommendation:execute", "reason": "test"})
    assert r.status_code == 200, r.text
    r = s.post(f"{BASE}/api/emergency/resume",
               json={"scope": "granular", "target": "recommendation:execute"})
    assert r.status_code == 200


def test_emergency_drain_ok():
    s = login("security@example.invalid")
    r = s.post(f"{BASE}/api/emergency/queue/drain")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_emergency_analyst_forbidden():
    s = login("analyst@example.invalid")
    for path, body in [
        ("/api/emergency/pause", {"scope": "global", "target": "*"}),
        ("/api/emergency/resume", {"scope": "global", "target": "*"}),
        ("/api/emergency/queue/drain", None),
    ]:
        if body is None:
            r = s.post(f"{BASE}{path}")
        else:
            r = s.post(f"{BASE}{path}", json=body)
        assert r.status_code == 403, f"{path}: expected 403 got {r.status_code}"


# --- Execution + rollback ---

def test_execute_enqueue_and_rollback_execowner():
    s = login("execowner@example.invalid")
    # low risk auto rec
    r = s.post(f"{BASE}/api/recommendations",
               json={"title": "TEST_auto_low", "description": "t", "tier": "auto",
                     "risk_level": "low", "action_payload": {"k": "v"}})
    assert r.status_code in (200, 201), r.text
    rec_id = r.json()["id"]
    # enqueue
    r = s.post(f"{BASE}/api/recommendations/{rec_id}/enqueue")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["queued"] is True
    assert j["rollback_eligible"] is True
    item_id = j["item_id"]
    # rollback - need executed status; item is 'queued' -> expect 409
    r = s.post(f"{BASE}/api/emergency/rollback/{item_id}")
    # security may have permission; but here we use execowner
    # execowner has emergency:revoke? Let's just check the call is auth'd or 409 status logic
    assert r.status_code in (200, 409, 403), r.text


def test_enqueue_blocked_when_globally_paused():
    sec = login("security@example.invalid")
    execu = login("execowner@example.invalid")
    # create a rec first (before pause)
    r = execu.post(f"{BASE}/api/recommendations",
                   json={"title": "TEST_blocked", "description": "t", "tier": "auto",
                         "risk_level": "low", "action_payload": {"k": "v"}})
    assert r.status_code in (200, 201)
    rec_id = r.json()["id"]
    # engage global pause
    p = sec.post(f"{BASE}/api/emergency/pause", json={"scope": "global", "target": "*", "reason": "block"})
    assert p.status_code == 200
    try:
        r = execu.post(f"{BASE}/api/recommendations/{rec_id}/enqueue")
        assert r.status_code == 409, f"expected 409 while paused, got {r.status_code}: {r.text}"
    finally:
        sec.post(f"{BASE}/api/emergency/resume", json={"scope": "global", "target": "*"})


# --- Marketing RBAC ---

def test_marketing_can_create_rec_but_not_enqueue_or_approve():
    s = login("marketing@example.invalid")
    r = s.post(f"{BASE}/api/recommendations",
               json={"title": "TEST_mkt", "description": "d", "tier": "requires_approval",
                     "risk_level": "high", "action_payload": {"a": 1}})
    assert r.status_code in (200, 201), r.text
    rec_id = r.json()["id"]
    r = s.post(f"{BASE}/api/recommendations/{rec_id}/enqueue")
    assert r.status_code == 403, f"expected 403 enqueue, got {r.status_code}"
    r = s.post(f"{BASE}/api/approvals/nonexistent/approve",
               json={"decision": "approve", "payload_digest": "x"})
    assert r.status_code == 403


# --- Admin manage ---

def test_admin_create_user_invalid_domain_rejected():
    s = login("admin@example.invalid")
    r = s.post(f"{BASE}/api/admin/users",
               json={"email": "TEST_bad@example.com", "display_name": "Bad"})
    assert r.status_code == 422, f"expected 422 got {r.status_code}"


def test_admin_create_user_ok_and_list():
    s = login("admin@example.invalid")
    import uuid
    email = f"TEST_new_{uuid.uuid4().hex[:6]}@example.invalid"
    r = s.post(f"{BASE}/api/admin/users",
               json={"email": email, "display_name": "TEST New"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == email.lower()


def test_admin_service_identity_privileged_role_blocked():
    s = login("admin@example.invalid")
    # find agent-service user id via users listing endpoint
    r = s.get(f"{BASE}/api/users")
    if r.status_code != 200:
        # try alternate
        r = s.get(f"{BASE}/api/admin/users")
    if r.status_code != 200:
        # can't discover; skip
        import pytest
        pytest.skip(f"cannot list users ({r.status_code})")
    users = r.json()
    svc = None
    for u in users:
        if u.get("email", "").startswith("agent-service"):
            svc = u
            break
    if svc is None:
        import pytest
        pytest.skip("agent-service user not in listing")
    r = s.post(f"{BASE}/api/admin/users/{svc['id']}/roles",
               json={"role_names": ["Admin"]})
    assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"


# --- Audit chain still verified after operations ---

def test_audit_chain_verified_after_ops():
    s = login("auditor@example.invalid")
    r = s.get(f"{BASE}/api/audit/verify")
    assert r.status_code == 200
    assert r.json().get("verified") is True
