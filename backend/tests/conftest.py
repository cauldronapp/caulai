"""Pytest fixtures. Tests run against the dev PostgreSQL database (APP_ENV=dev)."""
import os
import uuid
import pytest

os.environ.setdefault("APP_ENV", "dev")

from sqlalchemy import create_engine, text  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.config import get_admin_database_url  # noqa: E402
from app.models import User, Role, UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture()
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


@pytest.fixture()
def admin_engine():
    """Owner connection (postgres) used to simulate tampering for tamper-evidence tests."""
    eng = create_engine(get_admin_database_url(), future=True)
    yield eng
    eng.dispose()


@pytest.fixture()
def make_user(db):
    created = []

    def _make(role_name: str, is_service: bool = False) -> User:
        suffix = uuid.uuid4().hex[:8]
        u = User(subject=f"test|{suffix}", email=f"test-{suffix}@example.invalid",
                 display_name=f"Test {role_name} {suffix}",
                 password_hash=hash_password("x"), is_service_identity=is_service, is_stub=True)
        db.add(u)
        db.flush()
        role = db.query(Role).filter_by(name=role_name).one()
        db.add(UserRole(user_id=u.id, role_id=role.id))
        db.flush()
        created.append(u.id)
        return u

    yield _make
