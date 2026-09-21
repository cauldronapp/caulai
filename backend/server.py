"""CAUL AI — Phase 1A backend. PostgreSQL system of record. No MongoDB.

AUTH STUB — NOT PRODUCTION. Dev/staging only. No production environment, no external
IdP connection, no live connectors, no external egress.
"""
import logging
import os

from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_app_env, get_chain_env, get_chain_org
from app.database import get_db, engine
from app.routers import (
    auth, dashboard, recommendations, approvals, audit, emergency, admin, system,
    notifications, admin_manage,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("caul")

app = FastAPI(title="CAUL AI — Cauldron Growth OS Command Center (Phase 1A)",
              description="AUTH STUB — NOT PRODUCTION. PostgreSQL system of record.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


for r in (auth, dashboard, recommendations, approvals, audit, emergency, admin, admin_manage, system, notifications):
    app.include_router(r.router)


@app.on_event("startup")
def on_startup():
    logger.info("CAUL AI starting in env=%s (AUTH STUB — NOT PRODUCTION)", get_app_env())
    try:
        from app.seed import run_seed
        result = run_seed()
        logger.info("Seed result: %s", result)
    except Exception as e:  # seed guard or DB not migrated yet
        logger.warning("Seed skipped/failed: %s", e)
