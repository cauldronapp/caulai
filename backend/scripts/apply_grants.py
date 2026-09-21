"""Apply DB-level least-privilege grants after migrations run as owner (postgres).

Enforces at the DATABASE level (not just app code):
  - App user gets SELECT/INSERT/UPDATE/DELETE on business tables.
  - App user gets ONLY SELECT + INSERT on audit_events and audit_checkpoints;
    UPDATE and DELETE are revoked so audit rows cannot be edited or removed by the
    application role. Tables are owned by postgres, so the revoke is effective.

Usage: python -m scripts.apply_grants   (reads APP_ENV; connects as admin/owner)
"""
import sys
from sqlalchemy import create_engine, text

sys.path.insert(0, ".")
from app.config import get_admin_database_url, get_app_env  # noqa: E402

APP_USER = {"dev": "caul_dev_user", "staging": "caul_staging_user"}
AUDIT_TABLES = ["audit_events", "audit_checkpoints"]


def apply():
    env = get_app_env()
    app_user = APP_USER[env]
    engine = create_engine(get_admin_database_url(), future=True)
    with engine.begin() as conn:
        # Base grants across all current tables/sequences.
        conn.execute(text(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {app_user}"))
        conn.execute(text(
            f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {app_user}"))
        conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {app_user}"))
        # Lock down audit tables to INSERT-only (+SELECT) for the app user.
        for tbl in AUDIT_TABLES:
            conn.execute(text(f"REVOKE UPDATE, DELETE, TRUNCATE ON {tbl} FROM {app_user}"))
            conn.execute(text(f"GRANT SELECT, INSERT ON {tbl} TO {app_user}"))
        # Ensure future tables created by owner remain reachable by app user.
        conn.execute(text(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {app_user}"))
    print(f"Grants applied for env={env}, app_user={app_user}. Audit tables INSERT-only.")


if __name__ == "__main__":
    apply()
