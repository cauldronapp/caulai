"""Platform cron endpoints. Scheduled audit-chain verification for dev + staging.

Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
Auth: per-environment HMAC Bearer secret (constant-time compare). Failed auth is
rate-limited and audited WITHOUT ever recording the secret.
"""
import hmac
import logging

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import get_runtime_database_url, get_chain_org, get_cron_secret
from ..database import SessionLocal
from ..audit import verify_chain, create_checkpoint, append_event
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
        except Exception as e:  # never crash the scheduler
            db.rollback()
            results[env] = {"error": str(e)}
        finally:
            db.close()
            eng.dispose()
    logger.info("SCHEDULED_AUDIT_VERIFY %s", results)
    return results


def _audit_cron_auth_failure(host: str, reason: str) -> None:
    db = SessionLocal()
    try:
        # NOTE: never record the presented token/secret.
        append_event(db, actor_id=None, actor_label=f"cron-client:{host}",
                     action="cron.auth_failed", resource_type="cron",
                     resource_id="/api/cron/verify-audit", payload={"reason": reason})
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@router.post("/verify-audit")
async def verify_audit(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
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
        _audit_cron_auth_failure(host, "missing_or_invalid_bearer")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron auth")
    background.add_task(run_scheduled_verification)
    return {"accepted": True, "scope": ["dev", "staging"]}


# Marker recognised by the CI route-permission coverage test: HMAC/webhook-authenticated
# (per-env cron secret), intentionally not RBAC-gated. Applies to all cron endpoints.
verify_audit.caul_webhook_auth = True
