"""Connector contract-test suite. Every future connector must pass all checks."""
from app.connectors.base import run_contract_suite, StubConnector


def test_stub_connector_passes_full_contract():
    results = run_contract_suite(StubConnector)
    failed = [r for r in results if not r["passed"]]
    assert not failed, f"Connector contract failures: {failed}"


def test_contract_covers_all_required_behaviors():
    checks = {r["check"] for r in run_contract_suite(StubConnector)}
    required = {
        "authorization_default_deny", "pause_blocks_execution", "revocation_blocks_execution",
        "timeout_no_side_effect", "failure_no_side_effect", "audit_generated",
        "idempotent_by_key", "safe_retry_applies_once",
    }
    assert required.issubset(checks), f"Missing contract checks: {required - checks}"
