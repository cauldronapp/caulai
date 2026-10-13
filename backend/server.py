"""CAUL AI — Phase 1A backend. PostgreSQL system of record. No MongoDB.

AUTH STUB — NOT PRODUCTION. Dev/staging only. No production environment, no external
IdP connection, no live connectors, no external egress.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_app_env, get_chain_env, get_chain_org
from app.database import get_db, engine
from app.routers import (
    auth, dashboard, recommendations, approvals, audit, emergency, admin, system,
    notifications, admin_manage, cron,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("caul")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CAUL AI starting in env=%s (AUTH STUB — NOT PRODUCTION)", get_app_env())
    try:
        from app.seed import run_seed
        logger.info("Seed result: %s", run_seed())
    except Exception as e:  # seed guard or DB not migrated yet
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


for r in (auth, dashboard, recommendations, approvals, audit, emergency, admin, admin_manage, system, notifications, cron):
    app.include_router(r.router)
