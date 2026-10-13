"""Phase 1A hardening tests: per-env cron secret, cron rate limit, audited
failure without secret, login rate limit, audit immutability."""
import os
import time
import uuid
import requests
import pytest
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
DEV = os.environ.get("WEBHOOK_CRON_SECRET_DEV")
STAG = os.environ.get("WEBHOOK_CRON_SECRET_STAGING")
SHARED = os.environ.get("WEBHOOK_CRON_SECRET")
CRON = f"{BASE}/api/cron/verify-audit"
# In-memory rate limiter is per-pod; target the local pod for deterministic burst tests
# (the external URL may distribute across replicas). Rate limiting is per-pod by design.
LOCAL = "http://localhost:8001"


# ---- CRON per-env secret ----
def test_cron_dev_secret_accepted():
    assert DEV
    r = requests.post(CRON, headers={"Authorization": f"Bearer {DEV}"})
    assert r.status_code == 200, r.text
    assert r.json().get("accepted") is True


def test_cron_staging_secret_rejected_in_dev():
    assert STAG
    r = requests.post(CRON, headers={"Authorization": f"Bearer {STAG}"})
    assert r.status_code in (401, 429), r.text


def test_cron_shared_legacy_secret_rejected():
    if not SHARED or SHARED == DEV:
        pytest.skip("no legacy shared secret different from DEV")
    r = requests.post(CRON, headers={"Authorization": f"Bearer {SHARED}"})
    assert r.status_code in (401, 429), r.text


def test_cron_garbage_token_rejected():
    r = requests.post(CRON, headers={"Authorization": "Bearer nope-xyz"})
    assert r.status_code in (401, 429)


# ---- CRON rate-limit and audited failure (no secret in payload) ----
def _login(session, email, password="StubPass!2026"):
    return session.post(f"{BASE}/api/auth/login",
                        json={"email": email, "password": password})


def test_cron_rate_limit_after_burst_of_bad_tokens_and_audit_no_secret():
    # burst of bad tokens; unique token per request so it never accidentally matches.
    got_429 = False
    for i in range(25):
        r = requests.post(f"{LOCAL}/api/cron/verify-audit", headers={"Authorization": f"Bearer bad-{uuid.uuid4()}"})
        if r.status_code == 429:
            got_429 = True
            break
        assert r.status_code == 401, f"iter {i}: {r.status_code} {r.text}"
    assert got_429, "expected 429 within 25 bad-token requests"

    # Verify audit rows exist for cron.auth_failed and contain no secret value.
    s = requests.Session()
    lg = _login(s, "auditor@example.invalid")
    assert lg.status_code == 200, lg.text
    r = s.get(f"{BASE}/api/audit", params={"q": "cron.auth_failed", "limit": 50})
    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("items") or body.get("events") or body if isinstance(body, dict) else body
    items = [it for it in items if it.get("action") == "cron.auth_failed"]
    assert isinstance(items, list) and len(items) > 0, "expected cron.auth_failed rows"
    for it in items[:20]:
        assert it.get("action") == "cron.auth_failed"
        payload = it.get("payload") or {}
        # must NOT contain the secret in any form
        blob = str(payload).lower()
        for needle in filter(None, [DEV, STAG, SHARED]):
            assert needle.lower() not in blob, "secret leaked in audit payload!"
        # must NOT contain token/secret keys
        assert not any(k in payload for k in ("token", "secret", "authorization", "bearer"))
        # should include a reason field only
        assert "reason" in payload


# ---- LOGIN rate limit ----
def test_login_rate_limit_and_other_account_still_works():
    # bad email dedicated to this test
    bad_email = f"ratelimit-{uuid.uuid4().hex[:8]}@example.invalid"
    got_429 = False
    for i in range(15):
        r = requests.post(f"{LOCAL}/api/auth/login",
                          json={"email": bad_email, "password": "wrong"})
        if r.status_code == 429:
            got_429 = True
            break
        assert r.status_code == 401, f"iter {i}: {r.status_code}"
    assert got_429, "expected 429 within 15 failed logins for same email"

    # A DIFFERENT untried account can still log in fine (limiter is keyed per ip+email).
    s = requests.Session()
    r = _login(s, "auditor@example.invalid")
    assert r.status_code == 200, r.text


def test_admin_login_valid_returns_200_and_sets_cookie():
    s = requests.Session()
    r = _login(s, "admin@example.invalid")
    assert r.status_code == 200, r.text
    assert "access_token" in s.cookies, f"cookies: {s.cookies.items()}"


# ---- Audit immutability + verify still true ----
def test_audit_verify_still_true():
    s = requests.Session()
    assert _login(s, "auditor@example.invalid").status_code == 200
    r = s.get(f"{BASE}/api/audit/verify")
    assert r.status_code == 200, r.text
    assert r.json().get("verified") is True


def test_app_db_user_cannot_update_or_delete_audit_events():
    # App uses runtime user with only INSERT on audit_events. Verify DB-level.
    from sqlalchemy import create_engine, text
    from app.config import get_runtime_database_url
    eng = create_engine(get_runtime_database_url("dev"))
    with eng.connect() as c:
        with pytest.raises(Exception):
            c.execute(text("UPDATE audit_events SET action='x' WHERE id IS NOT NULL"))
    with eng.connect() as c:
        with pytest.raises(Exception):
            c.execute(text("DELETE FROM audit_events"))


# ---- Service identity cannot login (regression) ----
def test_service_identity_cannot_login():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": "agent-service@example.invalid",
                            "password": "StubPass!2026"})
    assert r.status_code in (401, 403), r.text
