"""DEV-ONLY Stage-1 usage/value measurement.

Pseudonymous, server-side-generated, per-(tenant, product)-scoped refs with NO
cross-product person linkage. No free-text fields, no PII, no message content.
Append-only events; de-identified roll-ups; bounded retention; tenant/account purge.
$CAUL market price is NEVER a cost input — only provider token rates are.
"""
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from .models import UsageEvent, UsageAggregate, ModelCostRate
from .config import get_app_env
from . import audit

# ---- controlled vocabularies (schema rejects anything outside these) ----
EVENT_TYPES = {
    "workflow.started", "ai.step", "workflow.approval_requested",
    "workflow.approval_decided", "workflow.completed", "workflow.failed",
    "workflow.abandoned", "outcome.recorded", "human.time_logged",
}
WORKFLOW_TYPES = {"support_triage", "onboarding", "renewal_followup",
                  "usage_reporting", "feedback_analysis"}
ACTOR_TYPES = {"human", "ai", "system"}
RESULTS = {"success", "failure", "pending", "n/a"}
COHORTS = {"baseline", "caul_assisted"}
ATTRIBUTIONS = {"assisted", "baseline", "unattributed"}
OUTCOME_TYPES = {"ticket_resolved", "onboarding_step_completed", "onboarding_completed",
                 "renewal_confirmed", "renewal_lapsed", "conversion"}
ERROR_CLASSES = {"timeout", "validation", "upstream", "unknown"}
DECISIONS = {"approve", "reject"}

_NS = uuid.uuid5(uuid.NAMESPACE_URL, "caul-usage-surrogate")


def tenant_ref(tenant_key: str) -> str:
    return str(uuid.uuid5(_NS, f"tenant:{tenant_key}"))


def product_ref(product_key: str) -> str:
    return str(uuid.uuid5(_NS, f"product:{product_key}"))


def account_ref(person_key: str, tenant_key: str, product_key: str) -> str:
    # Scoped per (tenant, product): the same person in two products gets two
    # unrelated surrogates, so there is no cross-product join key.
    return str(uuid.uuid5(_NS, f"acct:{tenant_key}:{product_key}:{person_key}"))


def _validate_in(field: str, value, allowed: set):
    if value not in allowed:
        raise ValueError(f"Invalid {field}={value!r}; allowed={sorted(allowed)}")


def _raw_retention_days() -> int:
    return int(os.environ.get("USAGE_RAW_RETENTION_DAYS", "30"))


def _aggregate_retention_months() -> int:
    return int(os.environ.get("USAGE_AGGREGATE_RETENTION_MONTHS", "24"))


def record_event(db: Session, *, event_type: str, workflow_type: str, workflow_run_id: str,
                 actor_type: str, actor_id: str, tenant_ref: str, product_ref: str,
                 account_ref: str | None = None, cohort: str | None = None,
                 attribution: str | None = None, result: str = "n/a",
                 error_class: str | None = None, model_ref: str | None = None,
                 tokens_in: int | None = None, tokens_out: int | None = None,
                 tokens_cached: int | None = None, work_unit_type: str | None = None,
                 work_units: int | None = None, est_cost_usd: float | None = None,
                 latency_ms: int | None = None, cache_hit: bool | None = None,
                 approval_gate: str | None = None, decision: str | None = None,
                 decision_latency_ms: int | None = None, outcome_type: str | None = None,
                 outcome_value: int | None = None, handling_seconds: int | None = None,
                 occurred_at: datetime | None = None, env: str | None = None) -> UsageEvent:
    """Append one validated, PII-free usage event. Explicit kwargs only (unknown
    fields are impossible); controlled vocabularies are enforced."""
    _validate_in("event_type", event_type, EVENT_TYPES)
    _validate_in("workflow_type", workflow_type, WORKFLOW_TYPES)
    _validate_in("actor_type", actor_type, ACTOR_TYPES)
    _validate_in("result", result, RESULTS)
    if cohort is not None:
        _validate_in("cohort", cohort, COHORTS)
    if attribution is not None:
        _validate_in("attribution", attribution, ATTRIBUTIONS)
    if outcome_type is not None:
        _validate_in("outcome_type", outcome_type, OUTCOME_TYPES)
    if error_class is not None:
        _validate_in("error_class", error_class, ERROR_CLASSES)
    if decision is not None:
        _validate_in("decision", decision, DECISIONS)

    ev = UsageEvent(
        id=str(uuid.uuid4()), event_type=event_type,
        occurred_at=occurred_at or datetime.now(timezone.utc),
        env=env or get_app_env(), schema_version=1,
        workflow_type=workflow_type, workflow_run_id=workflow_run_id,
        actor_type=actor_type, actor_id=actor_id, account_ref=account_ref,
        tenant_ref=tenant_ref, product_ref=product_ref, cohort=cohort,
        attribution=attribution, result=result, error_class=error_class,
        model_ref=model_ref, tokens_in=tokens_in, tokens_out=tokens_out,
        tokens_cached=tokens_cached, work_unit_type=work_unit_type, work_units=work_units,
        est_cost_usd=est_cost_usd, latency_ms=latency_ms, cache_hit=cache_hit,
        approval_gate=approval_gate, decision=decision,
        decision_latency_ms=decision_latency_ms, outcome_type=outcome_type,
        outcome_value=outcome_value, handling_seconds=handling_seconds,
    )
    db.add(ev)
    db.flush()
    return ev


def upsert_rate(db: Session, *, model_ref: str, provider: str, rate_input_per_1k: float,
                rate_output_per_1k: float, rate_cached_input_per_1k: float,
                source_url: str, effective_date: str, currency: str = "USD") -> ModelCostRate:
    r = db.execute(select(ModelCostRate).where(ModelCostRate.model_ref == model_ref)).scalar_one_or_none()
    if r is None:
        r = ModelCostRate(model_ref=model_ref, provider=provider)
        db.add(r)
    r.provider = provider
    r.currency = currency
    r.rate_input_per_1k = rate_input_per_1k
    r.rate_output_per_1k = rate_output_per_1k
    r.rate_cached_input_per_1k = rate_cached_input_per_1k
    r.source_url = source_url
    r.effective_date = effective_date
    db.flush()
    return r


def compute_cost(rate: ModelCostRate, tokens_in: int = 0, tokens_out: int = 0,
                 tokens_cached: int = 0) -> float:
    """Provider-rate-based compute-cost estimate. Never uses $CAUL market price."""
    return round((tokens_in / 1000) * rate.rate_input_per_1k
                 + (tokens_out / 1000) * rate.rate_output_per_1k
                 + (tokens_cached / 1000) * rate.rate_cached_input_per_1k, 6)


def _rate(num: int, den: int):
    return round(num / den, 4) if den else None


def _avg(values: list):
    return round(sum(values) / len(values), 4) if values else None


def _cohort_rate(num_b: int, den_b: int, num_a: int, den_a: int, min_cell: int) -> dict:
    if den_b < min_cell or den_a < min_cell:
        return {"suppressed": True, "min_cell": min_cell}
    b, a = num_b / den_b, num_a / den_a
    return {"baseline": round(b, 4), "assisted": round(a, 4), "delta": round(a - b, 4),
            "baseline_n": den_b, "assisted_n": den_a, "suppressed": False}


def compute_metrics(db: Session, *, window_days: int = 30, min_cell: int = 5,
                    tenant_ref: str | None = None) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    stmt = select(UsageEvent).where(UsageEvent.occurred_at >= cutoff)
    if tenant_ref is not None:
        stmt = stmt.where(UsageEvent.tenant_ref == tenant_ref)
    events = db.execute(stmt).scalars().all()

    acct = defaultdict(lambda: {"runs": 0, "cost": 0.0, "units": 0})
    wf = defaultdict(lambda: {"started": 0, "completed": 0, "failed": 0, "abandoned": 0})
    step_latency: list = []
    approvals_requested = 0
    started_total = 0
    decided = 0
    rejects = 0
    decision_latencies: list = []
    handling = defaultdict(list)
    onb_started = defaultdict(int)
    onb_completed = defaultdict(int)
    ren_conf = defaultdict(int)
    ren_lapsed = defaultdict(int)
    conv_started = defaultdict(int)
    conversions = defaultdict(int)

    for e in events:
        if e.event_type == "workflow.started":
            started_total += 1
            wf[e.workflow_type]["started"] += 1
            if e.account_ref:
                acct[e.account_ref]["runs"] += 1
            if e.cohort:
                if e.workflow_type == "onboarding":
                    onb_started[e.cohort] += 1
                if e.workflow_type == "usage_reporting":
                    conv_started[e.cohort] += 1
        elif e.event_type == "ai.step":
            if e.est_cost_usd is not None and e.account_ref:
                acct[e.account_ref]["cost"] += float(e.est_cost_usd)
            if e.work_units and e.account_ref:
                acct[e.account_ref]["units"] += e.work_units
            if e.latency_ms is not None:
                step_latency.append(e.latency_ms)
        elif e.event_type == "workflow.completed":
            wf[e.workflow_type]["completed"] += 1
        elif e.event_type == "workflow.failed":
            wf[e.workflow_type]["failed"] += 1
        elif e.event_type == "workflow.abandoned":
            wf[e.workflow_type]["abandoned"] += 1
        elif e.event_type == "workflow.approval_requested":
            approvals_requested += 1
        elif e.event_type == "workflow.approval_decided":
            decided += 1
            if e.decision == "reject":
                rejects += 1
            if e.decision_latency_ms is not None:
                decision_latencies.append(e.decision_latency_ms)
        elif e.event_type == "human.time_logged":
            if e.cohort and e.handling_seconds is not None:
                handling[e.cohort].append(e.handling_seconds)
        elif e.event_type == "outcome.recorded":
            c = e.cohort
            if c:
                if e.outcome_type == "onboarding_completed":
                    onb_completed[c] += 1
                elif e.outcome_type == "renewal_confirmed":
                    ren_conf[c] += 1
                elif e.outcome_type == "renewal_lapsed":
                    ren_lapsed[c] += 1
                elif e.outcome_type == "conversion":
                    conversions[c] += 1

    by_account = []
    suppressed_accounts = 0
    for ref, v in acct.items():
        if v["runs"] < min_cell:
            suppressed_accounts += 1
            continue
        by_account.append({"account_ref": ref, "runs": v["runs"],
                           "ai_cost_usd": round(v["cost"], 4), "work_units": v["units"]})

    workflows = {}
    for name, c in wf.items():
        denom = c["completed"] + c["failed"] + c["abandoned"]
        workflows[name] = {"started": c["started"], "completed": c["completed"],
                           "failed": c["failed"], "abandoned": c["abandoned"],
                           "success_rate": _rate(c["completed"], denom)}

    base_h, ass_h = handling.get("baseline", []), handling.get("caul_assisted", [])
    if len(base_h) < min_cell or len(ass_h) < min_cell:
        support = {"suppressed": True, "min_cell": min_cell}
    else:
        support = {"baseline_avg_seconds": _avg(base_h), "assisted_avg_seconds": _avg(ass_h),
                   "seconds_saved": round(_avg(base_h) - _avg(ass_h), 4),
                   "baseline_n": len(base_h), "assisted_n": len(ass_h), "suppressed": False}

    return {
        "window_days": window_days,
        "min_cell": min_cell,
        "method": "observational — not causal",
        "later_method": "randomized holdout (not built; documented as a possible later method)",
        "ai_cost": {"total_usd": round(sum(a["cost"] for a in acct.values()), 4),
                    "by_account": by_account, "suppressed_accounts": suppressed_accounts},
        "workflows": workflows,
        "human_in_loop": {"approval_rate": _rate(approvals_requested, started_total),
                          "override_rate": _rate(rejects, decided),
                          "avg_decision_latency_ms": _avg(decision_latencies),
                          "avg_ai_step_latency_ms": _avg(step_latency)},
        "operational": {
            "support_time_saved": support,
            "onboarding_completion": _cohort_rate(
                onb_completed["baseline"], onb_started["baseline"],
                onb_completed["caul_assisted"], onb_started["caul_assisted"], min_cell),
            "renewal_followup": _cohort_rate(
                ren_conf["baseline"], ren_conf["baseline"] + ren_lapsed["baseline"],
                ren_conf["caul_assisted"], ren_conf["caul_assisted"] + ren_lapsed["caul_assisted"],
                min_cell),
            "conversion_lift": _cohort_rate(
                conversions["baseline"], conv_started["baseline"],
                conversions["caul_assisted"], conv_started["caul_assisted"], min_cell),
        },
    }


def rollup_aggregates(db: Session) -> int:
    """Roll raw events into de-identified per-(day, workflow, tenant, product, cohort)
    aggregates. account_ref is intentionally dropped. Idempotent upsert."""
    events = db.execute(select(UsageEvent)).scalars().all()
    groups: dict = defaultdict(lambda: {"n": 0, "m": {}})
    for e in events:
        day = e.occurred_at.astimezone(timezone.utc).date().isoformat()
        key = (day, e.workflow_type, e.tenant_ref, e.product_ref, e.cohort or "")
        g = groups[key]
        g["n"] += 1
        m = g["m"]
        m[e.event_type] = m.get(e.event_type, 0) + 1
        if e.est_cost_usd:
            m["ai_cost_usd"] = round(m.get("ai_cost_usd", 0.0) + float(e.est_cost_usd), 6)
        if e.work_units:
            m["work_units"] = m.get("work_units", 0) + e.work_units
        if e.outcome_type:
            k = f"outcome.{e.outcome_type}"
            m[k] = m.get(k, 0) + 1

    for (day, wtype, tref, pref, cohort), g in groups.items():
        existing = db.execute(
            select(UsageAggregate).where(
                UsageAggregate.day == day, UsageAggregate.workflow_type == wtype,
                UsageAggregate.tenant_ref == tref, UsageAggregate.product_ref == pref,
                UsageAggregate.cohort == cohort)
        ).scalar_one_or_none()
        if existing is None:
            db.add(UsageAggregate(day=day, workflow_type=wtype, tenant_ref=tref,
                                  product_ref=pref, cohort=cohort, n_events=g["n"], metrics=g["m"]))
        else:
            existing.n_events = g["n"]
            existing.metrics = g["m"]
    db.flush()
    return len(groups)


def run_retention(db: Session, raw_days: int | None = None, agg_months: int | None = None) -> dict:
    raw_days = raw_days if raw_days is not None else _raw_retention_days()
    agg_months = agg_months if agg_months is not None else _aggregate_retention_months()
    now = datetime.now(timezone.utc)

    aggregated = rollup_aggregates(db)
    raw_cutoff = now - timedelta(days=raw_days)
    raw_deleted = db.execute(
        delete(UsageEvent).where(UsageEvent.occurred_at < raw_cutoff)).rowcount
    agg_cutoff_day = (now - timedelta(days=agg_months * 30)).date().isoformat()
    agg_deleted = db.execute(
        delete(UsageAggregate).where(UsageAggregate.day < agg_cutoff_day)).rowcount

    summary = {"aggregated_groups": aggregated, "raw_deleted": raw_deleted,
               "aggregates_deleted": agg_deleted, "raw_retention_days": raw_days,
               "aggregate_retention_months": agg_months}
    audit.append_event(db, actor_id=None, actor_label="system:usage-retention",
                       action="usage.retention_run", resource_type="usage",
                       resource_id=None, payload=summary)
    db.commit()
    return summary


def purge_tenant(db: Session, tenant_ref: str, actor=None) -> dict:
    """Authoritative tenant-wide erasure: removes ALL raw events AND aggregates."""
    raw = db.execute(delete(UsageEvent).where(UsageEvent.tenant_ref == tenant_ref)).rowcount
    agg = db.execute(delete(UsageAggregate).where(UsageAggregate.tenant_ref == tenant_ref)).rowcount
    audit.append_event(db, actor_id=getattr(actor, "id", None),
                       actor_label=getattr(actor, "display_name", "system"),
                       action="usage.tenant_purged", resource_type="usage",
                       resource_id=tenant_ref[:255],
                       payload={"raw_deleted": raw, "aggregates_deleted": agg})
    db.commit()
    return {"tenant_ref": tenant_ref, "raw_deleted": raw, "aggregates_deleted": agg}


def purge_account_raw(db: Session, account_ref: str, actor=None) -> dict:
    """Pre-aggregation deletion: removes an account's still-raw events. Once rolled
    up, an individual contribution can no longer be removed from an aggregate."""
    raw = db.execute(delete(UsageEvent).where(UsageEvent.account_ref == account_ref)).rowcount
    audit.append_event(db, actor_id=getattr(actor, "id", None),
                       actor_label=getattr(actor, "display_name", "system"),
                       action="usage.account_raw_purged", resource_type="usage",
                       resource_id=account_ref[:255],
                       payload={"raw_deleted": raw,
                                "note": "aggregated contributions cannot be individually removed"})
    db.commit()
    return {"account_ref": account_ref, "raw_deleted": raw,
            "note": "aggregated contributions cannot be individually removed"}
