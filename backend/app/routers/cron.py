"""Platform cron endpoints. Scheduled audit-chain verification for dev + staging.

Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
"""
import os
import hmac
import logging

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import get_runtime_database_url, get_chain_org
from ..audit import verify_chain, create_checkpoint

logger = logging.getLogger("caul.cron")
router = APIRouter(prefix="/api/cron", tags=["cron"])


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


@router.post("/verify-audit")
async def verify_audit(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    secret = os.environ.get("WEBHOOK_CRON_SECRET")
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if not secret or not token or not hmac.compare_digest(token, secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron auth")
    background.add_task(run_scheduled_verification)
    return {"accepted": True, "scope": ["dev", "staging"]}
