"""Seed production guards + environment isolation."""
import pytest


def test_config_rejects_non_dev_staging(monkeypatch):
    from app import config
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(config.ConfigError):
        config.get_app_env()


def test_seed_refuses_wrong_database(monkeypatch):
    """The seed guard must refuse if the connected DB name doesn't match the env."""
    from app import seed
    from app.config import ConfigError

    class FakeScalar:
        def scalar_one(self):
            return "some_other_db"

    class FakeDB:
        def execute(self, *a, **k):
            return FakeScalar()

    with pytest.raises(seed.SeedGuardError):
        seed._assert_safe_to_seed(FakeDB())


def test_stub_users_use_invalid_domain():
    from app.seed import STUB_USERS
    for u in STUB_USERS:
        assert u["email"].endswith(".invalid"), f"{u['email']} must be non-deliverable"


def test_dev_and_staging_are_separate_databases():
    from app.config import get_runtime_database_url
    dev = get_runtime_database_url("dev")
    staging = get_runtime_database_url("staging")
    assert dev != staging
    assert "caul_dev" in dev and "caul_staging" in staging
    assert "caul_dev_user" in dev and "caul_staging_user" in staging
