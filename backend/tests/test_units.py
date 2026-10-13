"""Unit coverage for utility/domain modules: config, canonical, ratelimit, security,
auth_provider, audit (empty-chain paths), approvals (edge branches), connectors base
(negative + stub resume), rbac helpers, and seed guard/happy paths."""
import os
import uuid
import importlib
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app import config, canonical, security, audit, approvals
from app.ratelimit import RateLimiter
from app import auth_provider as ap
from app.auth_provider import IdentityProvider, StubIdentityProvider, identity_provider, STUB_LABEL
from app.rbac_matrix import is_high_risk, all_permissions, PERMISSION_CATALOG
from app.connectors.base import (
    BaseConnector, StubConnector, ConnectorAction, ConnectorResult, run_contract_suite,
)


# ----------------- config -----------------
def test_config_env_and_urls():
    assert config.get_app_env() == "dev"
    assert "caul_dev" in config.get_runtime_database_url("dev")
    assert "caul_staging" in config.get_runtime_database_url("staging")
    assert config.get_admin_database_url("dev")
    assert config.get_admin_database_url("staging")
    assert config.get_jwt_secret()
    assert config.get_session_ttl_minutes() >= 1
    assert config.get_chain_org()
    assert config.get_chain_env() == "dev"


def test_config_invalid_env_raises(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(config.ConfigError):
        config.get_app_env()


def test_config_require_missing_raises():
    with pytest.raises(config.ConfigError):
        config._require("DEFINITELY_MISSING_VAR_XYZ")


def test_config_cron_secret_specific_and_fallback(monkeypatch):
    monkeypatch.setenv("WEBHOOK_CRON_SECRET_DEV", "devsecret")
    assert config.get_cron_secret("dev") == "devsecret"
    monkeypatch.delenv("WEBHOOK_CRON_SECRET_DEV", raising=False)
    monkeypatch.setenv("WEBHOOK_CRON_SECRET", "sharedsecret")
    assert config.get_cron_secret("dev") == "sharedsecret"


# ----------------- canonical -----------------
def test_canonical_stable_and_types():
    a = canonical.canonical_json({"b": 1, "a": 2})
    assert a == '{"a":2,"b":1}'
    blob = canonical.canonical_json({
        "dt": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "d": date(2026, 1, 1), "dec": Decimal("1.5"), "u": uuid.uuid4(),
    })
    assert "2026-01-01" in blob
    assert len(canonical.sha256_hex("x")) == 64
    assert canonical.payload_digest({"x": 1}) == canonical.payload_digest({"x": 1})


def test_canonical_unserializable_raises():
    with pytest.raises(TypeError):
        canonical.canonical_json({"bad": object()})


# ----------------- ratelimit -----------------
def test_ratelimit_add_and_exceeded():
    rl = RateLimiter()
    key = "k"
    assert rl.exceeded(key, 2, 60) is False
    rl.add(key)
    assert rl.exceeded(key, 2, 60) is False
    rl.add(key)
    assert rl.exceeded(key, 2, 60) is True
    # window expiry: 0-second window drops old hits
    assert rl.exceeded(key, 2, 0) is False


# ----------------- security -----------------
def test_security_hash_verify_and_token_roundtrip():
    h = security.hash_password("secret")
    assert security.verify_password("secret", h) is True
    assert security.verify_password("wrong", h) is False
    # malformed hash -> ValueError path -> False
    assert security.verify_password("x", "not-a-bcrypt-hash") is False
    token, exp = security.create_access_token("uid", "e@example.invalid", 0, "jti-1")
    decoded = security.decode_token(token)
    assert decoded["sub"] == "uid" and decoded["type"] == "access" and decoded["stub"] is True


# ----------------- auth_provider -----------------
def test_auth_provider_describe_and_claims():
    desc = identity_provider.describe()
    assert desc["label"] == STUB_LABEL and desc["is_stub"] is True and desc["mfa"] is False
    claims = identity_provider.build_claims(subject="s", email="e@example.invalid", display_name="n")
    assert claims.provider == "stub" and claims.is_stub is True
    with pytest.raises(NotImplementedError):
        identity_provider.authenticate(email="e", credential="c")


def test_auth_provider_abstract_bodies_executed():
    # Exercise the abstract method bodies via super() to keep them covered.
    class Impl(IdentityProvider):
        def authenticate(self, *, email, credential):
            return super().authenticate(email=email, credential=credential)

        def describe(self):
            return super().describe()

    impl = Impl()
    with pytest.raises(NotImplementedError):
        impl.authenticate(email="e", credential="c")
    with pytest.raises(NotImplementedError):
        impl.describe()


# ----------------- rbac helpers -----------------
def test_rbac_helpers():
    assert is_high_risk("role:manage") is True
    assert is_high_risk("dashboard:read") is False
    assert all_permissions() == dict(PERMISSION_CATALOG)


# ----------------- connectors base -----------------
def test_stub_connector_resume_and_full_contract():
    c = StubConnector()
    c.pause(); c.resume()
    assert c._paused is False
    results = run_contract_suite(StubConnector)
    assert all(r["passed"] for r in results)
    assert ConnectorAction("a").payload == {}


class _BadConnector(BaseConnector):
    """Deliberately broken connector: never enforces auth/pause/revoke/timeout/failure.
    Drives the negative (record False) branches of run_contract_suite."""
    name = "bad"
    required_permission = "connector:test"
    execute_count = 0

    def authorize(self, granted_permissions):
        return None

    def execute(self, action):
        return ConnectorResult(status="executed", detail="x")

    def pause(self):
        return None

    def resume(self):
        return None

    def revoke(self):
        return None

    def audit_records(self):
        return []


def test_contract_suite_negative_paths():
    results = run_contract_suite(_BadConnector)
    by = {r["check"]: r["passed"] for r in results}
    # A broken connector must FAIL the safety checks.
    assert by["authorization_default_deny"] is False
    assert by["pause_blocks_execution"] is False
    assert by["revocation_blocks_execution"] is False
    assert by["timeout_no_side_effect"] is False
    assert by["failure_no_side_effect"] is False


# ----------------- audit empty-chain paths -----------------
def test_audit_empty_chain_verify_and_checkpoint(db):
    env = f"unittest-empty-{uuid.uuid4().hex[:8]}"
    report = audit.verify_chain(db, chain_env=env, chain_org="cauldron")
    assert report["verified"] is True and report["event_count"] == 0
    assert report["head_seq"] is None and report["head_hash"] is None and report["genesis_ok"] is True
    assert audit.create_checkpoint(db, note="x", chain_env=env, chain_org="cauldron") is None


# ----------------- approvals edge branches -----------------
def _rec(db, make_user, tier, risk, payload):
    submitter = make_user("Admin")
    rec = approvals.submit_recommendation(
        db, actor=submitter, title="u", description="", category="t",
        tier=tier, risk_level=risk, action_payload=payload)
    db.commit()
    return submitter, rec


def test_cast_decision_not_found(db, make_user):
    reviewer = make_user("Admin")
    with pytest.raises(approvals.ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id="missing",
                                decision="approve", submitted_payload_digest="d")
    assert e.value.code == "not_found"


def test_cast_decision_not_reviewable_auto(db, make_user):
    _, rec = _rec(db, make_user, "auto", "low", {"x": 1})
    reviewer = make_user("Admin")
    with pytest.raises(approvals.ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id,
                                decision="approve", submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "not_reviewable"


def test_cast_decision_no_open_approval(db, make_user):
    from app.models import Recommendation
    submitter = make_user("Admin")
    rec = Recommendation(title="x", description="", category="t", tier="requires_approval",
                         risk_level="low", action_payload={"x": 1},
                         payload_digest=canonical.payload_digest({"x": 1}),
                         required_approvals=1, submitted_by=submitter.id, status="pending")
    db.add(rec); db.commit()
    reviewer = make_user("Admin")
    with pytest.raises(approvals.ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id,
                                decision="approve", submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "no_open_approval"


def test_cast_decision_not_pending(db, make_user):
    _, rec = _rec(db, make_user, "requires_approval", "low", {"x": 1})
    appr = approvals.open_approval_for(db, rec)
    appr.revoked = True  # still status=pending so open_approval_for returns it; revoked -> not_pending
    db.commit()
    reviewer = make_user("Admin")
    with pytest.raises(approvals.ApprovalError) as e:
        approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id,
                                decision="approve", submitted_payload_digest=rec.payload_digest)
    assert e.value.code == "not_pending"


def test_cast_decision_reject_sets_rejected(db, make_user):
    _, rec = _rec(db, make_user, "requires_approval", "low", {"x": 2})
    reviewer = make_user("Admin")
    appr = approvals.cast_decision(db, actor=reviewer, recommendation_id=rec.id,
                                   decision="reject", submitted_payload_digest=rec.payload_digest)
    db.commit()
    assert appr.status == "rejected"


def test_revoke_approval_not_found(db, make_user):
    actor = make_user("Admin")
    with pytest.raises(approvals.ApprovalError) as e:
        approvals.revoke_approval(db, actor=actor, approval_id="missing", reason="x")
    assert e.value.code == "not_found"


def test_can_execute_all_branches(db, make_user):
    from app.models import Approval
    # prohibited
    _, rec_p = _rec(db, make_user, "permanently_prohibited", "high", {"x": 1})
    assert approvals.can_execute(db, rec_p) == (False, "permanently_prohibited")
    # auto
    _, rec_a = _rec(db, make_user, "auto", "low", {"x": 2})
    assert approvals.can_execute(db, rec_a) == (True, "auto")
    # not_approved (pending approval)
    _, rec_na = _rec(db, make_user, "requires_approval", "low", {"x": 3})
    ok, reason = approvals.can_execute(db, rec_na)
    assert ok is False and reason == "not_approved"
    # approved + revoked
    _, rec_r = _rec(db, make_user, "requires_approval", "low", {"x": 4})
    appr = approvals.open_approval_for(db, rec_r)
    appr.status = "approved"; appr.revoked = True
    db.commit()
    assert approvals.can_execute(db, rec_r) == (False, "revoked")
    # approved + expired
    _, rec_e = _rec(db, make_user, "requires_approval", "low", {"x": 5})
    appr = approvals.open_approval_for(db, rec_e)
    appr.status = "approved"; appr.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    assert approvals.can_execute(db, rec_e) == (False, "expired")
    # approved + payload changed
    _, rec_c = _rec(db, make_user, "requires_approval", "low", {"x": 6})
    appr = approvals.open_approval_for(db, rec_c)
    appr.status = "approved"
    rec_c.payload_digest = "changed-digest"
    db.commit()
    assert approvals.can_execute(db, rec_c) == (False, "payload_changed")


# ----------------- seed guard + happy path -----------------
def test_seed_guard_blocks_on_db_mismatch(monkeypatch):
    from app import seed
    from app.database import SessionLocal
    monkeypatch.setattr(seed, "get_app_env", lambda: "staging")  # expects caul_staging, connected to caul_dev
    s = SessionLocal()
    try:
        with pytest.raises(seed.SeedGuardError):
            seed._assert_safe_to_seed(s)
    finally:
        s.close()


def test_run_seed_idempotent_happy_path():
    from app import seed
    result = seed.run_seed()
    assert result["seeded"] is True and result["env"] == "dev"
    assert result["permissions"] == len(PERMISSION_CATALOG)


def test_active_pause_blocking_granular(db, make_user):
    from app.models import PauseState
    tgt = f"res:act-{uuid.uuid4().hex[:6]}"
    db.add(PauseState(scope="granular", target=tgt, active=True, reason="t"))
    db.commit()
    p = approvals.active_pause_blocking(db, tgt)
    assert p is not None and p.scope == "granular"
    for row in db.query(PauseState).filter_by(target=tgt).all():
        db.delete(row)
    db.commit()


def test_require_permission_unknown_raises():
    from app.deps import require_permission
    with pytest.raises(RuntimeError):
        require_permission("bogus:perm")
