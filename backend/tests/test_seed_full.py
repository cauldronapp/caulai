"""Covers the seed CREATE and EXISTS branches deterministically by running the seed
sub-functions against a fresh, throwaway PostgreSQL schema (owner connection).

This exercises _get_or_create_permissions/roles/users, _seed_settings/connectors/policies,
and _seed_demo_recommendations on an empty schema (create paths) and again on the now
populated schema (idempotent exists paths)."""
import uuid
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker

from app.config import get_admin_database_url
from app.database import Base
from app.models import User, Permission, Role, Recommendation
from app import seed


def test_seed_sub_functions_create_then_exists():
    schema = f"seedtest_{uuid.uuid4().hex[:8]}"
    eng = create_engine(get_admin_database_url("dev"), future=True)
    with eng.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    Session = sessionmaker(bind=eng, future=True)
    s = Session()
    try:
        s.execute(text(f'SET search_path TO "{schema}"'))
        Base.metadata.create_all(bind=s.connection())

        # empty users dict -> every demo submitter is None -> continue (covers that branch)
        seed._seed_demo_recommendations(s, {})

        # ---- CREATE pass (empty schema) ----
        perms = seed._get_or_create_permissions(s)
        roles = seed._get_or_create_roles(s, perms)
        seed._get_or_create_users(s, roles)
        seed._seed_settings(s)
        seed._seed_connectors(s)
        seed._seed_policies(s)
        users = {u.email: u for u in s.execute(select(User)).scalars().all()}
        seed._seed_demo_recommendations(s, users)
        s.commit()
        assert s.execute(select(Permission)).scalars().first() is not None
        assert s.execute(select(Role)).scalars().first() is not None
        assert s.execute(select(Recommendation)).scalars().first() is not None

        # ---- EXISTS pass (idempotent; everything already present) ----
        perms2 = seed._get_or_create_permissions(s)
        roles2 = seed._get_or_create_roles(s, perms2)
        seed._get_or_create_users(s, roles2)
        seed._seed_settings(s)
        seed._seed_connectors(s)
        seed._seed_policies(s)
        seed._seed_demo_recommendations(s, users)  # early-return: recs already exist
        s.commit()
        assert len(perms2) == len(perms)
    finally:
        s.close()
        with eng.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        eng.dispose()
