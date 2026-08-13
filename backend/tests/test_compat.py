"""Tests for the frontend-compat endpoints (health, fir, blockchain, field)."""

import hashlib


def test_health_contract(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "ollama_base" in body
    assert "ollama_model" in body
    assert "ledger_count" in body


def test_fir_convert_mock(client):
    r = client.post("/api/fir/convert", json={"text": "I lost 50000 rs via phonepe", "mock": True})
    assert r.status_code == 200
    body = r.json()
    assert body["mock"] is True
    assert body["provider"] == "mock"
    assert body["fir"].startswith("FIRST INFORMATION REPORT")
    assert "50000" in body["fir"]


def test_fir_convert_requires_text(client):
    r = client.post("/api/fir/convert", json={"text": ""})
    assert r.status_code == 400
    assert "text is required" in r.text


def test_fir_convert_overlong(client):
    r = client.post("/api/fir/convert", json={"text": "x" * 21000})
    assert r.status_code == 400


def test_fir_convert_ollama_fallback(client):
    r = client.post("/api/fir/convert", json={"text": "scam me 1 lakh whatsapp"})
    assert r.status_code == 200
    body = r.json()
    assert body["mock"] is True
    assert body["provider"] == "mock"


def test_blockchain_roundtrip(client):
    h = hashlib.sha256(b"evidence-bytes").hexdigest()
    r = client.post(
        "/api/blockchain/notarize",
        json={"fileName": "chat.txt", "fileSize": "12 KB", "hash": h, "caseId": "CASE-1"},
    )
    assert r.status_code == 200
    rec = r.json()
    assert rec["hash"] == h
    assert rec["verified"] is True
    assert rec["txHash"].startswith("0x")

    r = client.post("/api/blockchain/verify", json={"hash": h})
    assert r.status_code == 200
    assert r.json()["verified"] is True
    assert r.json()["record"]["caseId"] == "CASE-1"

    r = client.post("/api/blockchain/verify", json={"hash": "deadbeef" * 8})
    assert r.status_code == 200
    assert r.json()["verified"] is False

    r = client.get("/api/blockchain/ledger")
    assert r.status_code == 200
    assert any(rec["hash"] == h for rec in r.json()["ledger"])


def test_blockchain_verify_requires_hash(client):
    r = client.post("/api/blockchain/verify", json={"hash": ""})
    assert r.status_code == 400


def test_field_status_mock(client):
    r = client.get("/api/field/status")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["connected"], bool)
    assert isinstance(body["mock"], bool)
    assert "adb_available" in body


def test_field_list_empty_or_valid(client):
    r = client.get("/api/field/list")
    assert r.status_code == 200
    body = r.json()
    assert "backups" in body
    for b in body["backups"]:
        assert "folder" in b and "case_id" in b and "files" in b and "mock" in b


def test_field_extract_fake_case(client):
    r = client.post("/api/field/extract", json={"caseId": "TEST-XYZ-1"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["files"], list)
    assert len(body["files"]) > 0
    for f in body["files"]:
        assert f["path"] and f["sha256"] and f["size"] >= 0
    assert isinstance(body["log"], list)
    assert body["out_dir"]

    r = client.get("/api/field/list")
    assert r.status_code == 200
    assert any(b["case_id"] == "TEST-XYZ-1" for b in r.json()["backups"])


def test_field_extract_sanitizes_case_id(client):
    r = client.post("/api/field/extract", json={"caseId": "../../evil;rm"})
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_field_extract_uses_case_id_alias(client):
    r = client.post("/api/field/extract", json={"case_id": "ALIAS-2"})
    assert r.status_code == 200
    r = client.get("/api/field/list")
    assert any(b["case_id"] == "ALIAS-2" for b in r.json()["backups"])