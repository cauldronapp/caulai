"""In-process TestClient integration coverage for every /api router, the auth flow,
default-deny (PermissionChecker), get_current_user token branches, server root/health/CSRF,
and the cron endpoint. Uses Bearer-token auth (captured from login) so cookie Secure flags
do not affect the in-process http testserver."""
import os
import re
import uuid
from datetime import datetime, timezone, timedelta

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from dotenv import load_dotenv

from server import app
from app.database import SessionLocal
from app.models import (
    User, Session as AuthSession, Notification, ExecutionQueueItem, PauseState,
)
from app.security import create_access_token
from app.config import get_jwt_secret, get_session_ttl_minutes

load_dotenv("/app/backend/.env")

PW = "StubPass!2026"
DEV_CRON = os.environ.get("WEBHOOK_CRON_SECRET_DEV")


def _token_for(client: TestClient, email: str, password: str = PW) -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    tok = r.cookies.get("access_token")
    if not tok:
        m = re.search(r"access_token=([^;]+)", r.headers.get("set-cookie", ""))
        tok = m.group(1) if m else None
    assert tok, "no access_token issued"
    return tok


def as_role(email: str):
    c = TestClient(app)
    tok = _token_for(c, email)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    return c


def _user(email: str):
    db = SessionLocal()
    try:
        u = db.execute(select(User).where(User.email == email)).scalar_one()
        return u.id, u.token_version
    finally:
        db.close()


ADMIN = "admin@example.invalid"
EXEC = "execowner@example.invalid"
MARKETING = "marketing@example.invalid"
NOROLE = "norole@example.invalid"
AUDITOR = "auditor@example.invalid"


# ===================== server-level =====================
def test_root_and_health():
    c = TestClient(app)
    r = c.get("/api/")
    assert r.status_code == 200 and r.json()["system_of_record"] == "PostgreSQL"
    r = c.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    assert r.headers["X-Frame-Options"] == "DENY"


def test_csrf_blocks_cross_origin_mutation():
    c = TestClient(app)
    r = c.post("/api/auth/login", headers={"origin": "https://evil.example"},
               json={"email": ADMIN, "password": PW})
    assert r.status_code == 403


def test_lifespan_startup_runs_seed():
    with TestClient(app) as c:  # triggers lifespan startup (seed)
        assert c.get("/api/health").status_code == 200


def test_readiness_probe_ok():
    r = TestClient(app).get("/api/health/ready")
    assert r.status_code == 200 and r.json()["status"] == "ready"
    assert r.json()["permissions"] > 0


def test_request_id_header_present_and_echoed():
    c = TestClient(app)
    r = c.get("/api/health")
    assert r.headers.get("X-Request-ID")
    r2 = c.get("/api/health", headers={"X-Request-ID": "fixed-req-123"})
    assert r2.headers.get("X-Request-ID") == "fixed-req-123"


def test_json_log_formatter_outputs_json():
    import json as _json
    import logging as _logging
    from server import JsonLogFormatter, request_id_var
    request_id_var.set("rid-xyz")
    rec = _logging.LogRecord("caul", _logging.INFO, __file__, 1, "hello %s", ("world",), None)
    payload = _json.loads(JsonLogFormatter().format(rec))
    assert payload["msg"] == "hello world" and payload["request_id"] == "rid-xyz"
    assert payload["level"] == "INFO" and payload["logger"] == "caul"


# ===================== auth =====================
def test_provider_metadata_public():
    c = TestClient(app)
    r = c.get("/api/auth/provider")
    assert r.status_code == 200 and r.json()["is_stub"] is True


def test_login_success_logout_and_me():
    c = TestClient(app)
    tok = _token_for(c, ADMIN)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    c.cookies.set("access_token", tok)  # so logout can decode+revoke the session
    me = c.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["email"] == ADMIN
    out = c.post("/api/auth/logout")
    assert out.status_code == 200 and out.json()["ok"] is True


def test_login_bad_credentials():
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": ADMIN, "password": "wrong"})
    assert r.status_code == 401


def test_service_identity_login_forbidden():
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": "agent-service@example.invalid", "password": PW})
    assert r.status_code == 403


def test_login_rate_limit():
    c = TestClient(app)
    bad = f"ratelimit-{uuid.uuid4().hex[:8]}@example.invalid"
    got = False
    for _ in range(12):
        r = c.post("/api/auth/login", json={"email": bad, "password": "no"})
        if r.status_code == 429:
            got = True
            break
    assert got


# ===================== get_current_user token branches =====================
def test_auth_missing_token_401():
    assert TestClient(app).get("/api/dashboard").status_code == 401


def test_auth_garbage_token_401():
    c = TestClient(app)
    c.headers.update({"Authorization": "Bearer not-a-jwt"})
    assert c.get("/api/dashboard").status_code == 401


def test_auth_wrong_token_type_401():
    tok = pyjwt.encode({"sub": "x", "type": "refresh", "jti": "j", "ver": 0,
                        "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                       get_jwt_secret(), algorithm="HS256")
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    assert c.get("/api/dashboard").status_code == 401


def test_auth_unknown_user_401():
    tok, _ = create_access_token("nonexistent-user-id", "x@example.invalid", 0, str(uuid.uuid4()))
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    assert c.get("/api/dashboard").status_code == 401


def test_auth_token_version_mismatch_401():
    uid, _ = _user(ADMIN)
    tok, _ = create_access_token(uid, ADMIN, 999, str(uuid.uuid4()))
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    assert c.get("/api/dashboard").status_code == 401


def test_auth_session_missing_401():
    uid, ver = _user(ADMIN)
    tok, _ = create_access_token(uid, ADMIN, ver, str(uuid.uuid4()))  # no session row for this jti
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    assert c.get("/api/dashboard").status_code == 401


def test_auth_session_expired_401():
    uid, ver = _user(ADMIN)
    jti = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(AuthSession(user_id=uid, jti=jti,
                           expires_at=datetime.now(timezone.utc) - timedelta(minutes=1), revoked=False))
        db.commit()
    finally:
        db.close()
    tok, _ = create_access_token(uid, ADMIN, ver, jti)
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    assert c.get("/api/dashboard").status_code == 401


# ===================== default-deny =====================
def test_default_deny_norole_403():
    c = as_role(NOROLE)
    assert c.get("/api/dashboard").status_code == 403
    assert c.get("/api/audit").status_code == 403


# ===================== dashboard =====================
def test_dashboard_ok():
    r = as_role(ADMIN).get("/api/dashboard")
    assert r.status_code == 200 and "pending_approvals" in r.json()


def test_dashboard_analytics():
    r = as_role(ADMIN).get("/api/dashboard/analytics")
    assert r.status_code == 200
    j = r.json()
    for k in ["recommendations_by_status", "recommendations_by_tier",
              "approvals_by_status", "executions_by_status", "audit_daily"]:
        assert k in j and isinstance(j[k], list)
    assert as_role(NOROLE).get("/api/dashboard/analytics").status_code == 403


def test_dashboard_analytics_range_and_export():
    admin = as_role(ADMIN)
    r = admin.get("/api/dashboard/analytics", params={"days": 7})
    assert r.status_code == 200 and r.json()["days"] == 7
    exp = admin.get("/api/dashboard/export")
    assert exp.status_code == 200 and exp.headers["content-type"].startswith("text/csv")
    assert "pending_approvals" in exp.text
    assert as_role(NOROLE).get("/api/dashboard/export").status_code == 403


def test_audit_saved_filters():
    admin = as_role(ADMIN)
    created = admin.post("/api/audit/filters",
                         json={"name": "My View", "query": {"q": "login"}, "shared": True})
    assert created.status_code == 200
    fid = created.json()["id"]
    assert created.json()["owned"] is True
    assert created.json()["is_default"] is False
    assert created.json()["owner_label"]  # owner display name present
    lst = admin.get("/api/audit/filters")
    assert lst.status_code == 200 and any(f["id"] == fid for f in lst.json())
    assert all("owner_label" in f and "is_default" in f for f in lst.json())
    # pin as admin (setting:update) -> team default + stays shared
    pinned = admin.post(f"/api/audit/filters/{fid}/pin", json={"pinned": True})
    assert pinned.status_code == 200
    assert pinned.json()["is_default"] is True and pinned.json()["shared"] is True
    # non-admin (auditor lacks setting:update) cannot pin
    assert as_role(AUDITOR).post(f"/api/audit/filters/{fid}/pin", json={"pinned": True}).status_code == 403
    # pin missing -> 404
    assert admin.post("/api/audit/filters/missing/pin", json={"pinned": True}).status_code == 404
    # unpin
    assert admin.post(f"/api/audit/filters/{fid}/pin", json={"pinned": False}).json()["is_default"] is False
    assert admin.delete("/api/audit/filters/does-not-exist").status_code == 404
    assert admin.delete(f"/api/audit/filters/{fid}").json()["deleted"] is True


# ===================== recommendations =====================
def _create_rec(client, tier="auto", risk="low", payload=None):
    payload = payload or {"k": uuid.uuid4().hex}
    r = client.post("/api/recommendations", json={
        "title": "t", "description": "d", "category": "c",
        "tier": tier, "risk_level": risk, "action_payload": payload})
    assert r.status_code == 200, r.text
    return r.json()


def test_recommendations_crud_and_validation():
    admin = as_role(ADMIN)
    rec = _create_rec(admin, "auto", "low")
    assert admin.get("/api/recommendations").status_code == 200
    assert admin.get(f"/api/recommendations/{rec['id']}").status_code == 200
    assert admin.get("/api/recommendations/does-not-exist").status_code == 404
    # invalid tier / risk
    assert admin.post("/api/recommendations", json={"title": "t", "tier": "bogus",
                      "risk_level": "low", "action_payload": {}}).status_code == 422
    assert admin.post("/api/recommendations", json={"title": "t", "tier": "auto",
                      "risk_level": "bogus", "action_payload": {}}).status_code == 422
    # update payload (re-binds digest)
    up = admin.put(f"/api/recommendations/{rec['id']}/payload", json={"action_payload": {"n": 9}})
    assert up.status_code == 200 and up.json()["payload_digest"]
    assert admin.put("/api/recommendations/missing/payload", json={"action_payload": {}}).status_code == 404
    # prohibited recs are immutable to edits
    proh = _create_rec(admin, "permanently_prohibited", "high")
    assert admin.put(f"/api/recommendations/{proh['id']}/payload",
                     json={"action_payload": {"x": 1}}).status_code == 403
    # updating a pending (requires_approval) rec re-sets status to pending
    pend = _create_rec(admin, "requires_approval", "low")
    up2 = admin.put(f"/api/recommendations/{pend['id']}/payload", json={"action_payload": {"z": 1}})
    assert up2.status_code == 200 and up2.json()["status"] == "pending"


def test_recommendation_enqueue_execute():
    admin = as_role(ADMIN)
    rec = _create_rec(admin, "auto", "low")
    r = admin.post(f"/api/recommendations/{rec['id']}/enqueue")
    assert r.status_code == 200 and r.json()["queued"] is True
    assert admin.post("/api/recommendations/missing/enqueue").status_code == 404
    # prohibited cannot execute
    proh = _create_rec(admin, "permanently_prohibited", "high")
    assert admin.post(f"/api/recommendations/{proh['id']}/enqueue").status_code == 409


# ===================== approvals =====================
def test_approvals_flow():
    admin = as_role(ADMIN)       # submitter
    execo = as_role(EXEC)        # distinct reviewer (approval:approve)
    rec = _create_rec(admin, "requires_approval", "low")
    digest = rec["payload_digest"]
    # list + fetch the approval id
    lst = execo.get("/api/approvals")
    assert lst.status_code == 200
    appr = next(a for a in lst.json() if a["recommendation_id"] == rec["id"])
    assert execo.get(f"/api/approvals/{appr['id']}").status_code == 200
    assert execo.get("/api/approvals/missing").status_code == 404
    # approve with wrong digest -> 409 payload_mismatch
    bad = execo.post(f"/api/approvals/{rec['id']}/approve", json={"decision": "approve",
                     "payload_digest": "wrong"})
    assert bad.status_code == 409
    # approve correctly (required=1) -> approved
    ok = execo.post(f"/api/approvals/{rec['id']}/approve", json={"decision": "approve",
                    "payload_digest": digest})
    assert ok.status_code == 200 and ok.json()["status"] == "approved"


def test_approvals_reject_and_revoke():
    admin = as_role(ADMIN)
    execo = as_role(EXEC)
    rec = _create_rec(admin, "requires_approval", "low")
    rej = execo.post(f"/api/approvals/{rec['id']}/reject", json={"decision": "reject",
                     "payload_digest": rec["payload_digest"]})
    assert rej.status_code == 200 and rej.json()["status"] == "rejected"
    # a second rec to revoke its approval
    rec2 = _create_rec(admin, "requires_approval", "low")
    appr = next(a for a in execo.get("/api/approvals").json() if a["recommendation_id"] == rec2["id"])
    rv = admin.post(f"/api/approvals/{appr['id']}/revoke", json={"reason": "test"})
    assert rv.status_code == 200 and rv.json()["revoked"] is True
    # reject with wrong digest -> 409 (ApprovalError path); revoke missing -> 409
    rec3 = _create_rec(admin, "requires_approval", "low")
    assert execo.post(f"/api/approvals/{rec3['id']}/reject", json={"decision": "reject",
                      "payload_digest": "wrong"}).status_code == 409
    assert admin.post("/api/approvals/missing/revoke", json={"reason": "x"}).status_code == 409


# ===================== audit =====================
def test_audit_endpoints():
    aud = as_role(AUDITOR)
    assert aud.get("/api/audit").status_code == 200
    assert aud.get("/api/audit", params={"q": "login", "action": "auth.login",
                   "resource_type": "session", "limit": 5}).status_code == 200
    assert aud.get("/api/audit/verify").json()["verified"] is True
    cp = aud.post("/api/audit/checkpoint")
    assert cp.status_code == 200 and cp.json()["created"] is True
    assert aud.get("/api/audit/checkpoints").status_code == 200
    exp = aud.get("/api/audit/export")
    assert exp.status_code == 200 and "seq" in exp.text.splitlines()[0]
    assert aud.get("/api/audit/export", params={"fmt": "xml"}).status_code == 422


# ===================== emergency =====================
def test_emergency_status_pause_resume():
    admin = as_role(ADMIN)
    assert admin.get("/api/emergency").status_code == 200
    assert admin.post("/api/emergency/pause", json={"scope": "bogus", "target": "*"}).status_code == 422
    tgt = f"recommendation:execute-{uuid.uuid4().hex[:6]}"
    p = admin.post("/api/emergency/pause", json={"scope": "granular", "target": tgt, "reason": "r"})
    assert p.status_code == 200 and p.json()["active"] is True
    r = admin.post("/api/emergency/resume", json={"scope": "granular", "target": tgt})
    assert r.status_code == 200 and r.json()["active"] is False
    assert admin.post("/api/emergency/resume", json={"scope": "granular",
                      "target": "never-paused"}).status_code == 404


def test_emergency_queue_and_rollback():
    admin = as_role(ADMIN)
    uid, _ = _user(ADMIN)
    rec = _create_rec(admin, "auto", "low")
    db = SessionLocal()
    try:
        queued = ExecutionQueueItem(recommendation_id=rec["id"], status="queued",
                                    irreversible=False, rollback_eligible=True, enqueued_by=uid)
        executed = ExecutionQueueItem(recommendation_id=rec["id"], status="executed",
                                      irreversible=False, rollback_eligible=True, enqueued_by=uid)
        irr = ExecutionQueueItem(recommendation_id=rec["id"], status="executed",
                                 irreversible=True, rollback_eligible=False, enqueued_by=uid)
        noelig = ExecutionQueueItem(recommendation_id=rec["id"], status="executed",
                                    irreversible=False, rollback_eligible=False, enqueued_by=uid)
        db.add_all([queued, executed, irr, noelig]); db.commit()
        qid, eid, iid, nid = queued.id, executed.id, irr.id, noelig.id
    finally:
        db.close()
    # cancel queued -> cancelled; cancel executed -> 409; cancel missing -> 404
    assert admin.post(f"/api/emergency/queue/{qid}/cancel").json()["status"] == "cancelled"
    assert admin.post(f"/api/emergency/queue/{eid}/cancel").status_code == 409
    assert admin.post("/api/emergency/queue/missing/cancel").status_code == 404
    # rollback executed -> rolled_back; irreversible -> 409; not-eligible -> 409; missing -> 404
    assert admin.post(f"/api/emergency/rollback/{eid}").json()["status"] == "rolled_back"
    assert admin.post(f"/api/emergency/rollback/{iid}").status_code == 409
    assert admin.post(f"/api/emergency/rollback/{nid}").status_code == 409
    assert admin.post("/api/emergency/rollback/missing").status_code == 404
    # rollback a cancelled (non-executed) item -> 409
    assert admin.post(f"/api/emergency/rollback/{qid}").status_code == 409

    # emergency revoke: fresh rec with a queued item -> cancels it
    rec_r = _create_rec(admin, "auto", "low")
    db = SessionLocal()
    try:
        rq = ExecutionQueueItem(recommendation_id=rec_r["id"], status="queued",
                                irreversible=False, rollback_eligible=True, enqueued_by=uid)
        db.add(rq); db.commit()
    finally:
        db.close()
    rv = admin.post(f"/api/emergency/revoke/{rec_r['id']}")
    assert rv.status_code == 200 and rv.json()["cancelled_items"] >= 1
    assert admin.post("/api/emergency/revoke/missing").status_code == 404

    # drain: fresh queued item present -> drains it
    rec_d = _create_rec(admin, "auto", "low")
    db = SessionLocal()
    try:
        dq = ExecutionQueueItem(recommendation_id=rec_d["id"], status="queued",
                                irreversible=False, rollback_eligible=True, enqueued_by=uid)
        db.add(dq); db.commit()
    finally:
        db.close()
    assert admin.post("/api/emergency/queue/drain").json()["drained"] >= 1


# ===================== admin (read) =====================
def test_admin_read_endpoints():
    admin = as_role(ADMIN)
    assert admin.get("/api/admin/users").status_code == 200
    assert admin.get("/api/admin/roles").status_code == 200
    perms = admin.get("/api/admin/permissions")
    assert perms.status_code == 200 and perms.json()["count"] > 0


# ===================== admin manage =====================
def test_admin_manage_users_and_roles():
    admin = as_role(ADMIN)
    email = f"created-{uuid.uuid4().hex[:8]}@example.invalid"
    created = admin.post("/api/admin/users", json={"email": email, "display_name": "C"})
    assert created.status_code == 200
    uid = created.json()["id"]
    # non-.invalid rejected; duplicate rejected
    assert admin.post("/api/admin/users", json={"email": "x@example.com",
                      "display_name": "X"}).status_code == 422
    assert admin.post("/api/admin/users", json={"email": email,
                      "display_name": "C"}).status_code == 409
    # disable toggle twice
    assert admin.post(f"/api/admin/users/{uid}/disable").json()["disabled"] is True
    assert admin.post(f"/api/admin/users/{uid}/disable").json()["disabled"] is False
    assert admin.post("/api/admin/users/missing/disable").status_code == 404
    # assign roles
    assert admin.post(f"/api/admin/users/{uid}/roles", json={"role_names": ["Analyst"]}).status_code == 200
    assert admin.post("/api/admin/users/missing/roles", json={"role_names": ["Analyst"]}).status_code == 404
    # service identity may only hold the Agent Service Identity role
    semail = f"svc-{uuid.uuid4().hex[:8]}@example.invalid"
    svc = admin.post("/api/admin/users", json={"email": semail, "display_name": "S",
                     "is_service_identity": True})
    assert svc.status_code == 200
    assert admin.post(f"/api/admin/users/{svc.json()['id']}/roles",
                      json={"role_names": ["Admin"]}).status_code == 403
    # upsert role (create then update)
    rn = f"TestRole-{uuid.uuid4().hex[:6]}"
    assert admin.post("/api/admin/roles", json={"name": rn, "description": "d",
                      "permissions": ["dashboard:read"]}).status_code == 200
    assert admin.post("/api/admin/roles", json={"name": rn, "description": "d2",
                      "permissions": ["dashboard:read", "audit:list"]}).status_code == 200


# ===================== system (settings/connectors/policies) =====================
def test_system_endpoints():
    admin = as_role(ADMIN)
    assert admin.get("/api/settings").status_code == 200
    upd = admin.put("/api/settings/platform_fee", json={"value": {"label": "Platform Fee", "percent": 2.5}})
    assert upd.status_code == 200 and upd.json()["version"] >= 2
    assert admin.put("/api/settings/missing", json={"value": {}}).status_code == 404
    assert admin.get("/api/connectors").status_code == 200
    ct = admin.post("/api/connectors/contract-test")
    assert ct.status_code == 200 and ct.json()["all_passed"] is True
    assert admin.get("/api/policies").status_code == 200


# ===================== notifications =====================
def test_notifications_flow():
    admin = as_role(ADMIN)
    uid, _ = _user(ADMIN)
    other_uid, _ = _user(EXEC)
    db = SessionLocal()
    try:
        g = Notification(user_id=None, kind="info", title="global", body="b")
        own = Notification(user_id=uid, kind="info", title="own", body="b")
        others = Notification(user_id=other_uid, kind="info", title="other", body="b")
        db.add_all([g, own, others]); db.commit()
        gid, ownid, otherid = g.id, own.id, others.id
    finally:
        db.close()
    assert admin.get("/api/notifications").status_code == 200
    assert admin.post(f"/api/notifications/{gid}/read").status_code == 200       # global
    assert admin.post(f"/api/notifications/{ownid}/read").status_code == 200      # own
    assert admin.post(f"/api/notifications/{otherid}/read").status_code == 404    # BOLA
    assert admin.post("/api/notifications/missing/read").status_code == 404
    assert admin.post("/api/notifications/read-all").status_code == 200


# ===================== cron =====================
def test_cron_verify_audit():
    c = TestClient(app)
    assert DEV_CRON
    ok = c.post("/api/cron/verify-audit", headers={"Authorization": f"Bearer {DEV_CRON}"})
    assert ok.status_code == 200 and ok.json()["accepted"] is True
    assert c.post("/api/cron/verify-audit", headers={"Authorization": "Bearer nope"}).status_code in (401, 429)
    assert c.post("/api/cron/verify-audit").status_code in (401, 429)


def test_cron_run_scheduled_verification_direct():
    from app.routers.cron import run_scheduled_verification
    res = run_scheduled_verification()
    assert "dev" in res and "staging" in res


def test_cron_weekly_digest():
    c = TestClient(app)
    assert DEV_CRON
    ok = c.post("/api/cron/weekly-digest", headers={"Authorization": f"Bearer {DEV_CRON}"})
    assert ok.status_code == 200 and ok.json()["accepted"] is True
    assert c.post("/api/cron/weekly-digest",
                  headers={"Authorization": "Bearer nope"}).status_code in (401, 429)


def test_cron_run_weekly_digest_direct():
    from app.routers.cron import run_weekly_digest
    res = run_weekly_digest()
    assert "approvals_by_status" in res
    assert "audit_events_added" in res
    assert res["window_days"] == 7


def test_cron_rate_limit_429():
    c = TestClient(app)
    got = False
    for _ in range(25):
        r = c.post("/api/cron/verify-audit", headers={"Authorization": f"Bearer bad-{uuid.uuid4()}"})
        if r.status_code == 429:
            got = True
            break
    assert got
