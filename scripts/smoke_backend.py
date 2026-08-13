"""Backend smoke test: boot uvicorn in a subprocess and exercise the API surface."""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8017"
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"


def wait_ready(timeout: int = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/health", timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Backend did not become ready in time")


def main() -> None:
    (BACKEND_DIR / "smoke_test.db").unlink(missing_ok=True)
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{BACKEND_DIR / 'smoke_test.db'}"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8017", "--log-level", "warning"],
        cwd=str(BACKEND_DIR),
        env=env,
    )
    try:
        wait_ready()
        import httpx

        with httpx.Client(base_url=BASE, timeout=120) as client:
            r = client.get("/api/health")
            print("health:", r.status_code, r.json())

            r = client.post("/api/auth/register", json={
                "email": "detective@test.com", "password": "password123",
                "full_name": "Test Detective", "role": "INVESTIGATOR",
            })
            print("register:", r.status_code)
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            r = client.post("/api/auth/login", data={"username": "detective@test.com", "password": "password123"})
            print("login:", r.status_code, r.text[:100])

            r = client.get("/api/auth/me", headers=headers)
            print("me:", r.status_code, r.json()["email"])

            r = client.post("/api/cases", headers=headers,
                            json={"title": "Phone fraud probe", "description": "complainant: Priya"})
            print("create case:", r.status_code)
            case_id = r.json()["case_id"]

            chat = b"""[12/02/2025, 3:45:12 PM] Ravi Kumar: Please transfer the amount to account 9876543210123
[13/02/2025, 9:10:55 AM] Ravi Kumar: You will be sorry if you don't pay. I will report your office at Mumbai.
[13/02/2025, 9:15:30 AM] Anjali Sharma: I am scared. Please don't threaten me."""

            r = client.post(f"/api/cases/{case_id}/evidence", headers=headers,
                            files={"file": ("whatsapp_chat.txt", chat, "text/plain")})
            print("upload evidence:", r.status_code)
            ev_id = r.json()["evidence_id"]
            print("  sha256:", r.json()["sha256"][:16], "| mime:", r.json()["mime_type"])

            r = client.post(f"/api/cases/{case_id}/evidence", headers=headers,
                            files={"file": ("dup_chat.txt", chat, "text/plain")})
            print("duplicate upload:", r.status_code, r.json().get("detail", "")[:50])

            r = client.post(f"/api/evidence/{ev_id}/process", headers=headers)
            print("process evidence:", r.status_code, r.json()["processing"][0]["status"])

            r = client.post("/api/agents/pipeline", headers=headers, json={"case_id": case_id})
            print("pipeline:", r.status_code)
            if r.status_code == 200:
                print("  agent statuses:", r.json()["agent_status"])

            r = client.get(f"/api/cases/{case_id}/entities", headers=headers)
            print("entities:", r.status_code, r.json().get("count"))

            r = client.get(f"/api/cases/{case_id}/relationships", headers=headers)
            print("relationships:", r.status_code, r.json().get("count"))

            r = client.get(f"/api/cases/{case_id}/timeline", headers=headers)
            print("timeline:", r.status_code, r.json().get("count"))

            r = client.get(f"/api/cases/{case_id}/contradictions", headers=headers)
            print("contradictions:", r.status_code, r.json().get("count"))

            r = client.get(f"/api/cases/{case_id}/risk", headers=headers)
            print("risk:", r.status_code, r.json().get("risk_score"), r.json().get("risk_level"))

            r = client.get(f"/api/cases/{case_id}/explainability", headers=headers)
            print("explainability:", r.status_code, "findings:", len(r.json().get("finding_explanations", [])))

            r = client.post("/api/agents/gpt", headers=headers,
                            json={"case_id": case_id, "question": "What phone number is mentioned and who threatened whom?"})
            print("gpt:", r.status_code, "| conf:", r.json().get("confidence"))

            r = client.get(f"/api/cases/{case_id}/report", headers=headers)
            print("report:", r.status_code, "| body:", r.text[:200])

            r = client.get(f"/api/cases/{case_id}/fir-draft", headers=headers)
            print("fir-draft:", r.status_code, "| disclaimer:", r.json()["content"]["disclaimer"][:40])

            r = client.get(f"/api/cases/{case_id}/audit", headers=headers)
            print("audit:", r.status_code, len(r.json()), "entries")

            r = client.get("/api/cases", headers=headers)
            print("cases list:", r.status_code, r.json()["total"])

            print("--- frontend-compat endpoints ---")
            r = client.get("/api/health")
            print("health:", r.status_code, "status:", r.json()["status"], "| ledger_count:", r.json()["ledger_count"])

            r = client.post("/api/fir/convert", json={"text": "I lost 50000 rs via phonepe", "mock": True})
            print("fir/convert:", r.status_code, "| mock:", r.json()["mock"], "| provider:", r.json()["provider"])

            import hashlib

            h = hashlib.sha256(b"smoke-evidence").hexdigest()
            r = client.post("/api/blockchain/notarize", json={"fileName": "smoke.bin", "fileSize": "4 KB", "hash": h})
            print("blockchain/notarize:", r.status_code, "| verified:", r.json().get("verified"))
            r = client.post("/api/blockchain/verify", json={"hash": h})
            print("blockchain/verify:", r.status_code, "| verified:", r.json().get("verified"))
            r = client.get("/api/blockchain/ledger")
            print("blockchain/ledger:", r.status_code, "| entries:", len(r.json().get("ledger", [])))

            r = client.get("/api/field/status")
            print("field/status:", r.status_code, "| connected:", r.json().get("connected"), "| mock:", r.json().get("mock"))
            r = client.get("/api/field/list")
            print("field/list:", r.status_code, "| backups:", len(r.json().get("backups", [])))
            r = client.post("/api/field/extract", json={"caseId": "SMOKE-CASE-1"})
            print("field/extract:", r.status_code, "| files:", len(r.json().get("files", [])), "| mock:", r.json().get("mock"))
    finally:
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    main()
    print("BACKEND SMOKE TEST COMPLETE")