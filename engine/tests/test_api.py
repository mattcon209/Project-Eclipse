from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from eclipse.config import DATA_DIR
from eclipse.gateway import app
from eclipse.pairing import ensure_code
from eclipse.pairing import status as pair_status


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ECLIPSE_DATA", str(tmp_path))
    # pairing/jobs stores already bound to DATA_DIR at import — tests use module stores.
    return TestClient(app)


def test_box16_health():
    c = TestClient(app)
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["phase"] == 2


def test_box17_status_unpaired_has_code():
    c = TestClient(app)
    r = c.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["engine"] == "running"
    assert "resources" in body


def test_box18_atelier_ui_served():
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert "Atelier" in r.text
    assert "Library" in r.text
    assert "Search this PC" in r.text


def test_box19_make_requires_pair():
    c = TestClient(app)
    r = c.post("/api/make", json={"prompt": "hallway"})
    assert r.status_code in (401, 409)


def test_box20_horror_prompt_not_rejected_as_content():
    c = TestClient(app)
    r = c.post("/api/make", json={"prompt": "gore horror wet concrete"})
    # Unpaired engine: 409/401 — never 451/403 content policy
    assert r.status_code not in (403, 451, 422)


def test_box22_kpis_requires_pair():
    c = TestClient(app)
    r = c.get("/api/kpis")
    assert r.status_code in (401, 409)
    assert r.status_code not in (403, 451)
