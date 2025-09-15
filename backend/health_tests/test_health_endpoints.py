import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure the backend package is importable when tests are executed from the
# health_tests directory.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Use lightweight in-memory embedder to avoid external downloads during tests.
os.environ.setdefault("USE_FAKE_EMBEDDER", "1")

from app import app

client = TestClient(app)


def test_health_mm():
    resp = client.get("/health/mm")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_browser():
    resp = client.get("/health/browser")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
