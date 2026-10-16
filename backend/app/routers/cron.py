"""Platform cron endpoints. Scheduled audit-chain verification + weekly governance digest.

Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
Auth: per-environment HMAC Bearer secret (constant-time compare). Failed auth is
rate-limited and audited WITHOUT ever recording the secret. No external/off-box
service is ever contacted — all work is local to the dev/staging databases.
"""
import hmac
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, status
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from ..config import get_runtime_database_url, get_chain_org, get_cron_secret
from ..database import SessionLocal
from ..models import Approval, AuditEvent, PauseState, Notification
from ..audit import verify_chain, create_checkpoint, append_event
from ..usage import run_retention as _usage_run_retention
from ..ratelimit import limiter

logger = logging.getLogger("caul.cron")
router = APIRouter(prefix="/api/cron", tags=["cron"])

_FAIL_LIMIT = 20
_FAIL_WINDOW_S = 300


def run_scheduled_verification() -> dict:
    """Verify + checkpoint the audit chain in BOTH local dev and staging databases.
    Local only — no external/off-box service is contacted."""
    results: dict = {}
    for env in ("dev", "staging"):
        eng = create_engine(get_runtime_database_url(env), pool_pre_ping=True)
        Session = sessionmaker(bind=eng, future=True)
        db = Session()
        try:
            report = verify_chain(db, chain_env=env, chain_org=get_chain_org())
            cp = create_checkpoint(db, note=f"scheduled-verify {env}", chain_env=env,
                                   chain_org=get_chain_org())
            db.commit()
            results[env] = {"verified": report["verified"], "events": report["event_count"],
                            "issues": len(report["issues"]),
                            "checkpoint": cp.id if cp else None}
        except Exception as e:  # pragma: no cover  (never crash the scheduler)
            db.rollback()
            results[env] = {"error": str(e)}
        finally:
            db.close()
            eng.dispose()
    logger.info("SCHEDULED_AUDIT_VERIFY %s", results)
    return results


def build_weekly_digest(db) -> dict:
    """Summarize the last 7 days of governance activity and store it as a broadcast
    notification. No email is sent (no external connectivity / $0 spend)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    approvals = db.execute(
        select(Approval.status, func.count()).where(Approval.created_at >= cutoff)
        .group_by(Approval.status)
    ).all()
    approvals_by_status = {r[0]: r[1] for r in approvals}
    audit_added = db.execute(
        select(func.count()).select_from(AuditEvent).where(AuditEvent.created_at >= cutoff)
    ).scalar_one()
    pauses_engaged = db.execute(
        select(func.count()).select_from(PauseState).where(PauseState.engaged_at >= cutoff)
    ).scalar_one()
    active_pauses = db.execute(
        select(func.count()).select_from(PauseState).where(PauseState.active.is_(True))
    ).scalar_one()

    summary = {
        "window_days": 7,
        "approvals_by_status": approvals_by_status,
        "audit_events_added": audit_added,
        "emergency_pauses_engaged": pauses_engaged,
        "active_pauses": active_pauses,
    }
    appr_line = ", ".join(f"{k}={v}" for k, v in approvals_by_status.items()) or "none"
    body = "\n".join([
        "Governance digest for the last 7 days (generated locally — not emailed).",
        f"Approvals: {appr_line}",
        f"Audit events added: {audit_added}",
        f"Emergency pauses engaged: {pauses_engaged} (currently active: {active_pauses})",
    ])
    db.add(Notification(user_id=None, kind="digest",
                        title=f"Weekly Governance Digest — {datetime.now(timezone.utc).date().isoformat()}",
                        body=body))
    append_event(db, actor_id=None, actor_label="system:scheduled-digest",
                 action="digest.generated", resource_type="notification",
                 resource_id=None, payload=summary)
    db.commit()
    logger.info("WEEKLY_DIGEST %s", summary)
    return summary


def run_weekly_digest() -> dict:
    """Generate the weekly governance digest for the running environment."""
    db = SessionLocal()
    try:
        return build_weekly_digest(db)
    except Exception:  # pragma: no cover  (never crash the scheduler)
        db.rollback()
        raise
    finally:
        db.close()


def _audit_cron_auth_failure(host: str, reason: str, resource_id: str) -> None:
    db = SessionLocal()
    try:
        # NOTE: never record the presented token/secret.
        append_event(db, actor_id=None, actor_label=f"cron-client:{host}",
                     action="cron.auth_failed", resource_type="cron",
                     resource_id=resource_id, payload={"reason": reason})
        db.commit()
    except Exception:  # pragma: no cover  (audit append is best-effort)
        db.rollback()
    finally:
        db.close()


def _require_cron_auth(request: Request, resource_id: str) -> None:
    """Shared HMAC Bearer auth for all cron endpoints. Rate-limits + audits failures."""
    host = request.client.host if request.client else "unknown"
    key = f"cron:{host}"
    secret = get_cron_secret()  # per-environment secret
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if not token or not hmac.compare_digest(token, secret):
        # Rate-limit repeated failures (blunt brute force) before doing any audit work.
        if limiter.exceeded(key, _FAIL_LIMIT, _FAIL_WINDOW_S):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Too many failed cron auth attempts")
        limiter.add(key)
        _audit_cron_auth_failure(host, "missing_or_invalid_bearer", resource_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron auth")


@router.post("/verify-audit")
async def verify_audit(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    _require_cron_auth(request, "/api/cron/verify-audit")
    background.add_task(run_scheduled_verification)
    return {"accepted": True, "scope": ["dev", "staging"]}


@router.post("/weekly-digest")
async def weekly_digest(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    _require_cron_auth(request, "/api/cron/weekly-digest")
    background.add_task(run_weekly_digest)
    return {"accepted": True, "digest": "weekly-governance"}


def run_usage_retention() -> dict:
    """Roll up + expire DEV-ONLY usage measurement data for the running environment."""
    db = SessionLocal()
    try:
        return _usage_run_retention(db)
    except Exception:  # pragma: no cover  (never crash the scheduler)
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/usage-retention")
async def usage_retention(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    _require_cron_auth(request, "/api/cron/usage-retention")
    background.add_task(run_usage_retention)
    return {"accepted": True, "job": "usage-retention"}


# Marker recognised by the CI route-permission coverage test: HMAC/webhook-authenticated
# (per-env cron secret), intentionally not RBAC-gated. Applies to all cron endpoints.
verify_audit.caul_webhook_auth = True
weekly_digest.caul_webhook_auth = True
usage_retention.caul_webhook_auth = True
