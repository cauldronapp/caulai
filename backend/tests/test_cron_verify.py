"""Cron verify-audit endpoint auth + effect tests."""
import os
import time
import requests
import pytest
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
SECRET = os.environ.get("WEBHOOK_CRON_SECRET")
URL = f"{BASE_URL}/api/cron/verify-audit"


def test_cron_no_auth_returns_401():
    r = requests.post(URL)
    assert r.status_code == 401


def test_cron_wrong_bearer_returns_401():
    r = requests.post(URL, headers={"Authorization": "Bearer wrong-token"})
    assert r.status_code == 401


def test_cron_correct_bearer_returns_200_and_creates_checkpoint():
    assert SECRET, "WEBHOOK_CRON_SECRET missing"
    r = requests.post(URL, headers={"Authorization": f"Bearer {SECRET}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("accepted") is True
    assert set(body.get("scope", [])) == {"dev", "staging"}

    # Give background task time to run
    time.sleep(3)

    # Verify via API as auditor (has audit:read)
    s = requests.Session()
    login = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "auditor@example.invalid", "password": "StubPass!2026"})
    assert login.status_code == 200, login.text
    cps = s.get(f"{BASE_URL}/api/audit/checkpoints")
    assert cps.status_code == 200, cps.text
    items = cps.json()
    if isinstance(items, dict):
        items = items.get("items") or items.get("checkpoints") or []
    notes = [c.get("note", "") for c in items]
    assert any(n.startswith("scheduled-verify") for n in notes), f"notes seen: {notes[:10]}"
