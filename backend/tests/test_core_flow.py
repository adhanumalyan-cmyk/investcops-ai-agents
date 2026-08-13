"""End-to-end tests for the core investigative flow (auth, cases, evidence, pipeline, results)."""


def _auth_headers(client, email="det@test.com"):
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "full_name": "Det", "role": "INVESTIGATOR"},
    )
    assert r.status_code == 201
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


CHAT = b"""[12/02/2025, 3:45:12 PM] Ravi Kumar: Please transfer the amount to account 9876543210123
[13/02/2025, 9:10:55 AM] Ravi Kumar: You will be sorry if you don't pay. I will report your office at Mumbai.
[13/02/2025, 9:15:30 AM] Anjali Sharma: I am scared. Please don't threaten me."""


def test_auth_flow(client):
    h = _auth_headers(client, "auth1@test.com")
    r = client.get("/api/auth/me", headers=h)
    assert r.status_code == 200
    assert r.json()["email"] == "auth1@test.com"

    r = client.post("/api/auth/login", data={"username": "auth1@test.com", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()

    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_case_requires_auth(client):
    assert client.get("/api/cases").status_code == 401


def test_evidence_requires_case_access(client):
    h = _auth_headers(client, "nobody@test.com")
    r = client.post("/api/cases/CASE-DOESNOTEXIST/evidence", headers=h, files={"file": ("a.txt", b"x", "text/plain")})
    assert r.status_code == 404


def test_full_investigative_flow(client):
    h = _auth_headers(client, "flow@test.com")

    r = client.post("/api/cases", headers=h, json={"title": "Fraud probe", "description": "complainant: Priya"})
    assert r.status_code == 201
    case_id = r.json()["case_id"]

    r = client.post(
        f"/api/cases/{case_id}/evidence", headers=h, files={"file": ("chat.txt", CHAT, "text/plain")}
    )
    assert r.status_code == 201
    ev_id = r.json()["evidence_id"]
    sha = r.json()["sha256"]

    r = client.post(
        f"/api/cases/{case_id}/evidence", headers=h, files={"file": ("dup.txt", CHAT, "text/plain")}
    )
    assert r.status_code == 409

    r = client.post(f"/api/evidence/{ev_id}/process", headers=h)
    assert r.status_code == 200
    assert r.json()["processing"][0]["status"] == "COMPLETED"

    r = client.post("/api/agents/pipeline", headers=h, json={"case_id": case_id})
    assert r.status_code == 200
    assert r.json()["agent_status"].get("agent_3_entities") == "COMPLETED"

    r = client.get(f"/api/cases/{case_id}/entities", headers=h)
    assert r.status_code == 200
    assert r.json()["count"] > 0

    r = client.get(f"/api/cases/{case_id}/risk", headers=h)
    assert r.status_code == 200
    assert r.json()["risk_score"] > 0

    r = client.get(f"/api/cases/{case_id}/report", headers=h)
    assert r.status_code == 200
    assert r.json()["report_type"] == "INVESTIGATION"
    assert "evidence_inventory" in r.json()["content"]

    r = client.get(f"/api/cases/{case_id}/fir-draft", headers=h)
    assert r.status_code == 200
    assert r.json()["content"]["disclaimer"]

    r = client.get(f"/api/cases/{case_id}/audit", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 5

    r = client.get("/api/cases", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert sha  # sanity: sha recorded on upload


def test_pipeline_rejects_missing_case(client):
    h = _auth_headers(client, "pipe@test.com")
    r = client.post("/api/agents/pipeline", headers=h, json={"case_id": "CASE-MISSING"})
    assert r.status_code == 404


def test_gpt_qa_returns_contract(client):
    h = _auth_headers(client, "qa@test.com")
    r = client.post("/api/cases", headers=h, json={"title": "QA case"})
    case_id = r.json()["case_id"]
    r = client.post(
        f"/api/cases/{case_id}/evidence", headers=h, files={"file": ("c.txt", CHAT, "text/plain")}
    )
    ev_id = r.json()["evidence_id"]
    assert client.post(f"/api/evidence/{ev_id}/process", headers=h).status_code == 200
    assert client.post("/api/agents/pipeline", headers=h, json={"case_id": case_id}).status_code == 200

    r = client.post("/api/agents/gpt", headers=h, json={"case_id": case_id, "question": "who threatened whom?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert "question" in body["result"]
    assert "answer" in body["result"]
    assert "confidence" in body["result"]