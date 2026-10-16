"""CAUL AI — Phase 1A backend. PostgreSQL system of record. No MongoDB.

AUTH STUB — NOT PRODUCTION. Dev/staging only. No production environment, no external
IdP connection, no live connectors, no external egress.
"""
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_app_env, get_chain_env, get_chain_org
from app.database import get_db, engine
from app.routers import (
    auth, dashboard, recommendations, approvals, audit, emergency, admin, system,
    notifications, admin_manage, cron, usage,
)

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JsonLogFormatter(logging.Formatter):
    """Structured single-line JSON logs carrying the current request id."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_var.get(),
            "msg": record.getMessage(),
        })


logging.basicConfig(level=logging.INFO)
for _h in logging.getLogger().handlers:
    _h.setFormatter(JsonLogFormatter())
logger = logging.getLogger("caul")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CAUL AI starting in env=%s (AUTH STUB — NOT PRODUCTION)", get_app_env())
    try:
        from app.seed import run_seed
        logger.info("Seed result: %s", run_seed())
    except Exception as e:  # pragma: no cover  (seed guard or DB not migrated yet)
        logger.warning("Seed skipped/failed: %s", e)
    yield


app = FastAPI(title="CAUL AI — Cauldron Growth OS Command Center (Phase 1A)",
              description="AUTH STUB — NOT PRODUCTION. PostgreSQL system of record.",
              lifespan=lifespan)

ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # explicit allowlist; never "*" with credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_and_csrf(request, call_next):
    # CSRF defense: reject cross-origin state-changing requests. Same-origin SPA and
    # server-to-server cron (no Origin header) are allowed; a forged cross-site POST is blocked.
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse(status_code=403, content={"detail": "Cross-origin request blocked"})
    resp = await call_next(request)
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp


@app.middleware("http")
async def request_context(request, call_next):
    # Assign/propagate a request id for structured logs and client correlation.
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = request_id_var.set(rid)
    logger.info("request start %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    logger.info("request done %s %s status=%s", request.method, request.url.path, response.status_code)
    return response


@app.get("/api/")
def root():
    return {"service": "CAUL AI", "phase": "1A",
            "notice": "AUTH STUB — NOT PRODUCTION",
            "system_of_record": "PostgreSQL"}


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "env": get_app_env(),
            "database": db.execute(text("SELECT current_database()")).scalar_one(),
            "chain_env": get_chain_env(), "chain_org": get_chain_org()}


@app.get("/api/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe: DB reachable AND seed/migrations applied (permissions present)."""
    perms = db.execute(text("SELECT COUNT(*) FROM permissions")).scalar_one()
    ready = perms > 0
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready",
                 "env": get_app_env(), "permissions": perms},
    )


for r in (auth, dashboard, recommendations, approvals, audit, emergency, admin, admin_manage, system, notifications, cron, usage):
    app.include_router(r.router)
