"""DEV-ONLY usage measurement layer: synthetic fixtures, pseudonymization, metric
formulas (golden numbers), small-cell suppression, retention roll-up/hard-delete,
tenant + pre-aggregation account purge, RBAC-gated endpoints, and the retention cron.
Synthetic data only — no real customer data."""
import os
import uuid
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient

from server import app
from app.database import SessionLocal
from app import usage
from app.usage_synth import generate_synthetic
from app.models import UsageEvent, UsageAggregate

DEV_CRON = os.environ.get("WEBHOOK_CRON_SECRET_DEV")
PW = "StubPass!2026"
ADMIN = "admin@example.invalid"
ANALYST = "analyst@example.invalid"
NOROLE = "norole@example.invalid"


def _as_role(email: str) -> TestClient:
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": email, "password": PW})
    assert r.status_code == 200, r.text
    import re
    tok = r.cookies.get("access_token") or re.search(
        r"access_token=([^;]+)", r.headers.get("set-cookie", "")).group(1)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    return c


def _gen():
    """Generate an isolated synthetic dataset under a unique tenant/product."""
    db = SessionLocal()
    try:
        return generate_synthetic(db, tenant_key=f"t-{uuid.uuid4().hex[:8]}",
                                  product_key=f"p-{uuid.uuid4().hex[:8]}")
    finally:
        db.close()


# ===================== pseudonymization =====================
def test_scoped_refs_no_cross_product_linkage():
    # Same person in two products -> unrelated account refs (no cross-product key).
    a1 = usage.account_ref("person", "tenantA", "prod1")
    a2 = usage.account_ref("person", "tenantA", "prod2")
    assert a1 != a2
    # Stable surrogates for the same scope.
    assert usage.tenant_ref("tenantA") == usage.tenant_ref("tenantA")
    assert usage.product_ref("prod1") != usage.product_ref("prod2")


# ===================== record_event validation =====================
def test_record_event_rejects_invalid_vocab():
    db = SessionLocal()
    try:
        bad = False
        try:
            usage.record_event(db, event_type="not.a.type", workflow_type="support_triage",
                               workflow_run_id="r", actor_type="ai", actor_id="svc",
                               tenant_ref="t", product_ref="p")
        except ValueError:
            bad = True
        assert bad
        # also an out-of-vocab cohort is rejected
        rejected = False
        try:
            usage.record_event(db, event_type="workflow.started", workflow_type="onboarding",
                               workflow_run_id="r", actor_type="ai", actor_id="svc",
                               tenant_ref="t", product_ref="p", cohort="bogus")
        except ValueError:
            rejected = True
        assert rejected
    finally:
        db.rollback()
        db.close()


# ===================== cost math =====================
def test_compute_cost_and_rate_upsert():
    db = SessionLocal()
    try:
        mref = f"rate-test-{uuid.uuid4().hex[:8]}"  # unique so the INSERT branch always runs
        r = usage.upsert_rate(db, model_ref=mref, provider="prov",
                              rate_input_per_1k=1.0, rate_output_per_1k=2.0,
                              rate_cached_input_per_1k=0.5,
                              source_url="https://prov/pricing", effective_date="2026-06-15")
        assert usage.compute_cost(r, tokens_in=1000, tokens_out=500, tokens_cached=1000) == 2.5
        # upsert again (update branch)
        r2 = usage.upsert_rate(db, model_ref=mref, provider="prov2",
                               rate_input_per_1k=3.0, rate_output_per_1k=0.0,
                               rate_cached_input_per_1k=0.0,
                               source_url="https://prov/pricing", effective_date="2026-06-16")
        assert r2.provider == "prov2" and r2.rate_input_per_1k == 3.0
        db.commit()
    finally:
        db.close()


# ===================== metric formulas (golden numbers) =====================
def test_metrics_golden_numbers():
    info = _gen()
    db = SessionLocal()
    try:
        m = usage.compute_metrics(db, window_days=30, min_cell=5, tenant_ref=info["tenant_ref"])
        assert m["method"] == "observational — not causal"
        # AI cost: alice 6 runs shown; bob 3 runs suppressed; total = (6+3)*2.0 = 18.0
        assert m["ai_cost"]["total_usd"] == 18.0
        assert m["ai_cost"]["suppressed_accounts"] == 1
        alice = next(a for a in m["ai_cost"]["by_account"] if a["account_ref"] == info["account_alice"])
        assert alice["runs"] == 6 and alice["ai_cost_usd"] == 12.0 and alice["work_units"] == 6
        assert all(a["account_ref"] != info["account_bob"] for a in m["ai_cost"]["by_account"])
        # workflow success rate 8/(8+1+1) = 0.8
        assert m["workflows"]["support_triage"]["success_rate"] == 0.8
        # human-in-loop: override 1/4 = 0.25; decision latency avg 100
        assert m["human_in_loop"]["override_rate"] == 0.25
        assert m["human_in_loop"]["avg_decision_latency_ms"] == 100.0
        assert m["human_in_loop"]["approval_rate"] is not None
        # support time saved 100-60 = 40
        st = m["operational"]["support_time_saved"]
        assert st["suppressed"] is False and st["seconds_saved"] == 40.0
        # onboarding 0.5 vs 0.8 -> delta 0.3
        onb = m["operational"]["onboarding_completion"]
        assert onb["baseline"] == 0.5 and onb["assisted"] == 0.8 and onb["delta"] == 0.3
        # renewal 0.3 vs 0.7 -> delta 0.4
        ren = m["operational"]["renewal_followup"]
        assert ren["baseline"] == 0.3 and ren["assisted"] == 0.7 and ren["delta"] == 0.4
        # conversion 0.2 vs 0.5 -> delta 0.3
        conv = m["operational"]["conversion_lift"]
        assert conv["baseline"] == 0.2 and conv["assisted"] == 0.5 and conv["delta"] == 0.3
    finally:
        db.close()


def test_metrics_small_cell_suppression_and_empty_window():
    info = _gen()
    db = SessionLocal()
    try:
        # min_cell huge -> every cohort metric + support + all accounts suppressed
        hi = usage.compute_metrics(db, min_cell=999, tenant_ref=info["tenant_ref"])
        assert hi["operational"]["onboarding_completion"]["suppressed"] is True
        assert hi["operational"]["renewal_followup"]["suppressed"] is True
        assert hi["operational"]["conversion_lift"]["suppressed"] is True
        assert hi["operational"]["support_time_saved"]["suppressed"] is True
        assert hi["ai_cost"]["by_account"] == [] and hi["ai_cost"]["suppressed_accounts"] >= 2
        # empty window -> None/empty branches
        empty = usage.compute_metrics(db, window_days=0)
        assert empty["human_in_loop"]["approval_rate"] is None
        assert empty["human_in_loop"]["avg_decision_latency_ms"] is None
        assert empty["workflows"] == {} and empty["ai_cost"]["by_account"] == []
        assert empty["operational"]["support_time_saved"]["suppressed"] is True
    finally:
        db.close()


# ===================== retention roll-up + hard delete =====================
def test_retention_rollup_and_delete():
    tkey = f"t-{uuid.uuid4().hex[:8]}"
    tref = usage.tenant_ref(tkey)
    old = datetime.now(timezone.utc) - timedelta(days=40)
    db = SessionLocal()
    try:
        for _ in range(2):
            usage.record_event(db, event_type="workflow.started", workflow_type="support_triage",
                               workflow_run_id=str(uuid.uuid4()), actor_type="ai", actor_id="svc",
                               tenant_ref=tref, product_ref=usage.product_ref("p"),
                               cohort="baseline", occurred_at=old)
        # a stale aggregate well beyond the 24-month window
        db.add(UsageAggregate(day="2000-01-01", workflow_type="support_triage", tenant_ref=tref,
                              product_ref=usage.product_ref("p"), cohort="baseline",
                              n_events=1, metrics={"workflow.started": 1}))
        db.commit()
        assert db.query(UsageEvent).filter(UsageEvent.tenant_ref == tref).count() == 2

        summary = usage.run_retention(db, raw_days=30, agg_months=24)
        assert summary["raw_deleted"] >= 2 and summary["aggregated_groups"] >= 1
        assert summary["raw_retention_days"] == 30 and summary["aggregate_retention_months"] == 24
        # old raw gone; de-identified aggregate present (and carries no account_ref column)
        assert db.query(UsageEvent).filter(UsageEvent.tenant_ref == tref).count() == 0
        aggs = db.query(UsageAggregate).filter(UsageAggregate.tenant_ref == tref).all()
        assert any(a.day == old.date().isoformat() for a in aggs)
        # stale aggregate deleted
        assert not any(a.day == "2000-01-01" for a in aggs)
    finally:
        db.close()


# ===================== purge paths =====================
def test_purge_tenant_and_account_raw():
    info = _gen()
    db = SessionLocal()
    try:
        # pre-aggregation account deletion removes still-raw rows for that account
        res_a = usage.purge_account_raw(db, info["account_alice"])
        assert res_a["raw_deleted"] >= 6
        assert db.query(UsageEvent).filter(
            UsageEvent.account_ref == info["account_alice"]).count() == 0
        # tenant-wide purge removes all remaining raw + aggregates for the tenant
        usage.rollup_aggregates(db)
        db.commit()
        res_t = usage.purge_tenant(db, info["tenant_ref"])
        assert res_t["raw_deleted"] >= 0 and res_t["aggregates_deleted"] >= 1
        assert db.query(UsageEvent).filter(
            UsageEvent.tenant_ref == info["tenant_ref"]).count() == 0
        assert db.query(UsageAggregate).filter(
            UsageAggregate.tenant_ref == info["tenant_ref"]).count() == 0
    finally:
        db.close()


# ===================== RBAC-gated endpoints =====================
def test_usage_metrics_endpoint_rbac():
    info = _gen()
    admin = _as_role(ADMIN)
    r = admin.get("/api/usage/metrics", params={"tenant_ref": info["tenant_ref"]})
    assert r.status_code == 200 and r.json()["ai_cost"]["total_usd"] == 18.0
    # analyst has usage:read
    assert _as_role(ANALYST).get("/api/usage/metrics").status_code == 200
    # default-deny
    assert _as_role(NOROLE).get("/api/usage/metrics").status_code == 403


def test_usage_purge_endpoint_rbac_and_validation():
    info = _gen()
    admin = _as_role(ADMIN)
    # analyst lacks usage:purge
    assert _as_role(ANALYST).post("/api/usage/purge",
                                  json={"tenant_ref": info["tenant_ref"]}).status_code == 403
    # neither field -> 422
    assert admin.post("/api/usage/purge", json={}).status_code == 422
    # account purge then tenant purge
    acc = admin.post("/api/usage/purge", json={"account_ref": info["account_alice"]})
    assert acc.status_code == 200 and "note" in acc.json()
    ten = admin.post("/api/usage/purge", json={"tenant_ref": info["tenant_ref"]})
    assert ten.status_code == 200 and ten.json()["tenant_ref"] == info["tenant_ref"]


# ===================== retention cron =====================
def test_cron_usage_retention_endpoint_and_direct():
    _gen()  # ensure some data exists
    c = TestClient(app)
    assert DEV_CRON
    ok = c.post("/api/cron/usage-retention", headers={"Authorization": f"Bearer {DEV_CRON}"})
    assert ok.status_code == 200 and ok.json()["accepted"] is True
    assert c.post("/api/cron/usage-retention",
                  headers={"Authorization": "Bearer nope"}).status_code in (401, 429)
    from app.routers.cron import run_usage_retention
    res = run_usage_retention()
    assert "raw_deleted" in res and "aggregated_groups" in res
