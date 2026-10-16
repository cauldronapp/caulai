"""DEV/STAGING-ONLY synthetic usage generator. NO real customer data.

Builds a deterministic, PII-free dataset with planted baseline-vs-assisted deltas so
value metrics can be validated against known golden numbers. Guarded to dev/staging
(get_app_env raises otherwise).
"""
import uuid

from sqlalchemy.orm import Session

from .config import get_app_env
from . import usage


def generate_synthetic(db: Session, *, tenant_key: str = "t1", product_key: str = "p1") -> dict:
    get_app_env()  # production guard: raises unless dev/staging
    tref = usage.tenant_ref(tenant_key)
    pref = usage.product_ref(product_key)
    rate = usage.upsert_rate(
        db, model_ref="example-model-v1", provider="example-provider",
        rate_input_per_1k=1.0, rate_output_per_1k=2.0, rate_cached_input_per_1k=0.5,
        source_url="https://example-provider/pricing", effective_date="2026-06-15")
    cost = usage.compute_cost(rate, tokens_in=1000, tokens_out=500, tokens_cached=0)  # 2.0

    def rid() -> str:
        return str(uuid.uuid4())

    def ev(**kw):
        kw.setdefault("tenant_ref", tref)
        kw.setdefault("product_ref", pref)
        usage.record_event(db, **kw)

    # --- Accounts for by-account AI cost (alice shown >=5 runs; bob suppressed <5) ---
    alice = usage.account_ref("alice", tenant_key, product_key)
    bob = usage.account_ref("bob", tenant_key, product_key)
    for _ in range(6):
        r = rid()
        ev(event_type="workflow.started", workflow_type="support_triage", workflow_run_id=r,
           actor_type="ai", actor_id="svc:triage", account_ref=alice, cohort="baseline")
        ev(event_type="ai.step", workflow_type="support_triage", workflow_run_id=r,
           actor_type="ai", actor_id="svc:triage", account_ref=alice, model_ref="example-model-v1",
           tokens_in=1000, tokens_out=500, tokens_cached=0, work_unit_type="classification",
           work_units=1, est_cost_usd=cost, latency_ms=600, cache_hit=False)
    for _ in range(3):
        r = rid()
        ev(event_type="workflow.started", workflow_type="support_triage", workflow_run_id=r,
           actor_type="ai", actor_id="svc:triage", account_ref=bob, cohort="baseline")
        ev(event_type="ai.step", workflow_type="support_triage", workflow_run_id=r,
           actor_type="ai", actor_id="svc:triage", account_ref=bob, model_ref="example-model-v1",
           tokens_in=1000, tokens_out=500, tokens_cached=0, work_unit_type="classification",
           work_units=1, est_cost_usd=cost, latency_ms=600, cache_hit=False)

    # --- Workflow success for support_triage: 8 completed, 1 failed, 1 abandoned -> 0.8 ---
    for _ in range(8):
        ev(event_type="workflow.completed", workflow_type="support_triage",
           workflow_run_id=rid(), actor_type="ai", actor_id="svc:triage", result="success")
    ev(event_type="workflow.failed", workflow_type="support_triage", workflow_run_id=rid(),
       actor_type="ai", actor_id="svc:triage", result="failure", error_class="timeout")
    ev(event_type="workflow.abandoned", workflow_type="support_triage", workflow_run_id=rid(),
       actor_type="system", actor_id="svc:triage", result="n/a")

    # --- Human-in-the-loop: 4 approvals requested + decided; 1 reject -> override 0.25 ---
    for i in range(4):
        r = rid()
        ev(event_type="workflow.approval_requested", workflow_type="support_triage",
           workflow_run_id=r, actor_type="ai", actor_id="svc:triage", approval_gate="send_reply")
        ev(event_type="workflow.approval_decided", workflow_type="support_triage",
           workflow_run_id=r, actor_type="human", actor_id="svc:reviewer",
           approval_gate="send_reply", decision="reject" if i == 0 else "approve",
           decision_latency_ms=100)

    # --- Support time saved: baseline 5x100s, assisted 5x60s -> saved 40 ---
    for _ in range(5):
        ev(event_type="human.time_logged", workflow_type="support_triage", workflow_run_id=rid(),
           actor_type="human", actor_id="svc:agent", cohort="baseline", handling_seconds=100)
        ev(event_type="human.time_logged", workflow_type="support_triage", workflow_run_id=rid(),
           actor_type="human", actor_id="svc:agent", cohort="caul_assisted", handling_seconds=60)

    # --- Onboarding completion: baseline 5/10=0.5, assisted 8/10=0.8 ---
    for cohort, completed in (("baseline", 5), ("caul_assisted", 8)):
        for i in range(10):
            r = rid()
            ev(event_type="workflow.started", workflow_type="onboarding", workflow_run_id=r,
               actor_type="ai", actor_id="svc:onboard", cohort=cohort)
            if i < completed:
                ev(event_type="outcome.recorded", workflow_type="onboarding", workflow_run_id=r,
                   actor_type="system", actor_id="svc:onboard", cohort=cohort,
                   attribution="assisted" if cohort == "caul_assisted" else "baseline",
                   outcome_type="onboarding_completed", outcome_value=1, result="success")

    # --- Renewal follow-up: baseline 3 conf/7 lapsed=0.3, assisted 7/3=0.7 ---
    for cohort, conf in (("baseline", 3), ("caul_assisted", 7)):
        for i in range(10):
            ev(event_type="outcome.recorded", workflow_type="renewal_followup", workflow_run_id=rid(),
               actor_type="system", actor_id="svc:renewal", cohort=cohort,
               attribution="assisted" if cohort == "caul_assisted" else "baseline",
               outcome_type="renewal_confirmed" if i < conf else "renewal_lapsed",
               outcome_value=1, result="success" if i < conf else "failure")

    # --- Conversion: usage_reporting started 10/cohort; baseline 2, assisted 5 conversions ---
    for cohort, conv in (("baseline", 2), ("caul_assisted", 5)):
        for i in range(10):
            r = rid()
            ev(event_type="workflow.started", workflow_type="usage_reporting", workflow_run_id=r,
               actor_type="ai", actor_id="svc:report", cohort=cohort)
            if i < conv:
                ev(event_type="outcome.recorded", workflow_type="usage_reporting", workflow_run_id=r,
                   actor_type="system", actor_id="svc:report", cohort=cohort,
                   attribution="assisted" if cohort == "caul_assisted" else "baseline",
                   outcome_type="conversion", outcome_value=1, result="success")

    db.commit()
    return {"tenant_ref": tref, "product_ref": pref,
            "account_alice": alice, "account_bob": bob, "cost_per_step": cost}
