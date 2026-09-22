"""Environment-driven configuration. PostgreSQL is the authoritative system of record.

Phase 1A supports only two environments: dev and staging. Each maps to a physically
separate PostgreSQL database with separate credentials. There is NO production
environment; any attempt to select one is refused (production guard).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

ALLOWED_ENVS = {"dev", "staging"}


class ConfigError(RuntimeError):
    pass


def get_app_env() -> str:
    env = (os.environ.get("APP_ENV") or "dev").strip().lower()
    if env not in ALLOWED_ENVS:
        # Production guard: refuse to operate outside dev/staging in Phase 1A.
        raise ConfigError(
            f"APP_ENV='{env}' is not permitted in Phase 1A. Allowed: {sorted(ALLOWED_ENVS)}. "
            "No production environment is authorized."
        )
    return env


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise ConfigError(f"Missing required environment variable: {name}")
    return val


def get_runtime_database_url(env: str | None = None) -> str:
    env = env or get_app_env()
    return _require("DEV_DATABASE_URL" if env == "dev" else "STAGING_DATABASE_URL")


def get_admin_database_url(env: str | None = None) -> str:
    """Owner (postgres) connection used ONLY for migrations + DB-level grant/revoke.
    The running application never uses this connection."""
    env = env or get_app_env()
    return _require("DEV_ADMIN_DATABASE_URL" if env == "dev" else "STAGING_ADMIN_DATABASE_URL")


def get_jwt_secret() -> str:
    return _require("JWT_SECRET")


def get_cron_secret(env: str | None = None) -> str:
    """Per-environment cron/webhook secret. dev and staging use DIFFERENT secrets.
    Falls back to a shared WEBHOOK_CRON_SECRET only if the env-specific one is unset."""
    env = env or get_app_env()
    specific = os.environ.get(f"WEBHOOK_CRON_SECRET_{env.upper()}")
    if specific:
        return specific
    return _require("WEBHOOK_CRON_SECRET")


def get_session_ttl_minutes() -> int:
    return int(os.environ.get("SESSION_TTL_MINUTES", "30"))


def get_chain_org() -> str:
    return os.environ.get("CHAIN_ORG", "cauldron")


# The chain "environment" scope equals the deployment env (dev/staging) so audit
# chains never mix across databases.
def get_chain_env() -> str:
    return get_app_env()
