"""
app/api/routes.py

API router for the frontend dashboard. Every endpoint here is called by the
React frontend (see frontend/src/lib/api.ts and the views). Response shapes
match what the UI expects -- do not rename fields.

Endpoints:
  GET  /health                 -> service status + ledger count
  POST /fir/convert            -> informal text -> FIR draft (Ollama, mock fallback)
  POST /blockchain/notarize    -> SHA-256 evidence -> ledger record
  POST /blockchain/verify      -> verify a hash against the ledger
  GET  /blockchain/ledger      -> full ledger
  GET  /field/status           -> ADB device info (mock when offline)
  GET  /field/list             -> past field extraction backups
  POST /field/extract          -> one-click logical extraction (mock when offline)
"""

import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Request

from ..core.config import settings
from .field_extractor import device_info, is_adb_available, logical_extract

router = APIRouter()

# ── File-based ledger (mirrors frontend localStorage) ────────────────────────
LEDGER_FILE = Path(__file__).resolve().parent.parent.parent / "ledger.json"


def load_ledger():
    if LEDGER_FILE.exists():
        try:
            return json.loads(LEDGER_FILE.read_text())
        except Exception:
            return []
    return []


def save_ledger(data):
    LEDGER_FILE.write_text(json.dumps(data, indent=2))


# ── FIR mock generator (deterministic, demo-safe) ────────────────────────────
def mock_fir(text: str):
    date = datetime.now().strftime("%d %B %Y")
    t = datetime.now().strftime("%H:%M")
    phone = re.search(r"\+91\s?\d{5}\s?\d{5}|\b\d{10}\b", text)
    phone = phone.group(0) if phone else "+91 98XXX XXXXX"
    amount = re.search(r"Rs\.?\s?[\d,]+|₹\s?[\d,]+|\b\d+\s*lakh\b|\b\d{4,6}\b", text, re.I)
    if amount:
        amt = amount.group(0)
        if re.match(r"^\d{4,6}$", amt.strip()):
            amt = f"Rs. {amt}"
        amount = amt
    else:
        amount = "Rs. 50,000"
    is_malayalam = bool(re.search(r"[\u0D00-\u0D7F]", text))
    plat = re.search(r"whatsapp|telegram|instagram|upi|phonepe|gpay|loan app|apk|kseb", text, re.I)
    plat = plat.group(0) if plat else ("WhatsApp/KSEB" if is_malayalam else "WhatsApp/Telegram")
    return f"""FIRST INFORMATION REPORT
(Under Section 173 BNSS / 154 CrPC) - NoteNext Draft

1. DISTRICT: Thiruvananthapuram | PS: Cyber Crime PS, NoteNext Cyber Lab
2. FIR No: NN-FIR-2026-{int(time.time()) % 9000 + 1000} | Date: {date} | Time: {t} IST
3. ACTS & SECTIONS:
   - BNS Sec 318(4), 319(2) - Cheating
   - IT Act 66C, 66D - Identity theft & impersonation
4. PLACE: Online - {plat}
5. COMPLAINT (Converted from informal text):
---
{text}
---
6. FORMAL NARRATIVE:
"On {date}, complainant stated that unknown person contacted via {plat} using {phone} and induced to transfer {amount} under false pretext. Believing it genuine, complainant transferred amount via UPI. Later found profile fraudulent. Produced screenshots/UTR as evidence. Prima facie offences under BNS & IT Act disclosed."

7. EVIDENCE: Screenshots, UTR, Chat exports (SHA-256 verified, Blockchain notarized)
8. ACTION: Case entrusted to NoteNext Investigation Unit; 1930/NCRP freeze request sent; evidence sent for 65B examination.

Investigating Officer: NoteNext AI Unit
[Draft by NoteNext AI + Qwen3 - to be verified by SHO]
"""


def call_ollama(prompt: str, system: str = ""):
    """Call local Ollama /api/generate. Raises on failure (caller falls back to mock)."""
    payload = {
        "model": settings.ollama_model,
        "prompt": (system + "\n\nUser: " + prompt + "\nAssistant:") if system else prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 1200},
    }
    req = Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
            return data.get("response", "").strip()
    except Exception as e:
        raise Exception(f"Ollama error: {e}")


# ── Routes ───────────────────────────────────────────────────────────────────
@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "InvestCops AI Backend (NoteNext-compatible API)",
        "time": datetime.now().isoformat(),
        "ollama_base": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "ledger_count": len(load_ledger()),
    }


@router.post("/fir/convert")
async def fir_convert(request: Request):
    raw = await _read_json(request)

    text = raw.get("text", "") or raw.get("content", "")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail={"error": "text is required"})
    if len(text) > settings.max_fir_chars:
        raise HTTPException(status_code=400, detail={"error": f"text exceeds {settings.max_fir_chars} characters"})

    system = raw.get("system", "")
    if not isinstance(system, str) or len(system) > settings.max_system_chars:
        system = ""
    system = system or "You are NoteNext legal assistant. Convert informal complaint (Manglish/Malayalam/English) to formal FIR under BNS 318, IT Act 66C/66D. Keep facts, add sections, output only FIR. Add disclaimer it's AI draft."

    if not raw.get("mock"):
        try:
            ans = call_ollama(text, system)
            if ans:
                return {"fir": ans, "provider": "ollama", "model": settings.ollama_model, "mock": False}
        except Exception as e:
            print(f"Ollama failed, using mock: {e}")
    return {"fir": mock_fir(text), "provider": "mock", "model": "mock", "mock": True, "note": "Ollama not reachable, used mock"}


@router.post("/blockchain/notarize")
async def blockchain_notarize(request: Request):
    raw = await _read_json(request)

    fhash = raw.get("hash", "")
    if not _is_hex(fhash):
        fhash = hashlib.sha256((str(raw.get("fileName", "")) + str(time.time())).encode()).hexdigest()

    rec = {
        "hash": fhash,
        "fileName": _safe_name(raw.get("fileName", "evidence.bin")),
        "fileSize": str(raw.get("fileSize", "1.2 MB"))[:64],
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M"),
        "isoTimestamp": datetime.now().isoformat(),
        "officer": str(raw.get("officer", "NoteNext AI Unit"))[:128],
        "badge": str(raw.get("badge", "NN-042"))[:64],
        "caseId": str(raw.get("caseId", "NN-2026-0001"))[:64],
        "txHash": "0x" + fhash[:64],
        "blockNumber": 8000000 + int(time.time()) % 500000,
        "verified": True,
    }
    ledger = load_ledger()
    ledger.insert(0, rec)
    save_ledger(ledger[:100])
    return rec


@router.post("/blockchain/verify")
async def blockchain_verify(request: Request):
    raw = await _read_json(request)
    h = raw.get("hash", "")
    if not _is_hex(h):
        raise HTTPException(status_code=400, detail={"error": "hash must be a hex string"})
    found = next((r for r in load_ledger() if r["hash"] == h), None)
    if found:
        return {"verified": True, "record": found}
    return {"verified": False}


@router.get("/blockchain/ledger")
def blockchain_ledger():
    return {"ledger": load_ledger()}


@router.get("/field/status")
def field_status():
    try:
        info = device_info()
        info["adb_available"] = is_adb_available()
        return info
    except Exception as e:
        return {"connected": False, "mock": True, "reason": str(e), "adb_available": False}


@router.get("/field/list")
def field_list():
    try:
        base = Path(__file__).resolve().parent.parent.parent / "field_backups"
        cases = []
        if base.exists():
            for d in sorted(base.iterdir(), reverse=True)[:20]:
                if d.is_dir():
                    mf = d / "manifest.json"
                    if mf.exists():
                        try:
                            m = json.loads(mf.read_text())
                            cases.append({"folder": d.name, "case_id": m.get("case_id"), "timestamp": m.get("timestamp"), "files": len(m.get("files", [])), "mock": m.get("mock")})
                        except Exception:
                            pass
        return {"backups": cases}
    except Exception as e:
        return {"backups": [], "error": str(e)}


@router.post("/field/extract")
async def field_extract(request: Request):
    raw = await _read_json(request)
    case_id = str(raw.get("caseId") or raw.get("case_id") or "KPC-2026-8941")[:128]
    try:
        res = logical_extract(case_id)
        for f in res.get("files", [])[:10]:
            try:
                ledger = load_ledger()
                rec_full = {
                    "hash": f["sha256"],
                    "fileName": f["path"],
                    "fileSize": str(f["size"]) + " bytes",
                    "timestamp": datetime.now().strftime("%d %b %Y, %H:%M"),
                    "isoTimestamp": datetime.now().isoformat(),
                    "officer": "Field Extractor",
                    "badge": "NN-FIELD",
                    "caseId": case_id,
                    "txHash": "0x" + f["sha256"][:64],
                    "blockNumber": 8000000 + int(time.time()) % 500000,
                    "verified": True,
                }
                ledger.insert(0, rec_full)
                save_ledger(ledger[:100])
            except Exception:
                pass
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


# ── Helpers ──────────────────────────────────────────────────────────────────
async def _read_json(request: Request) -> dict:
    """Read + parse a JSON request body (empty body -> {})."""
    try:
        body = await request.body()
        if not body:
            return {}
        data = json.loads(body.decode("utf-8", errors="ignore"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _safe_name(fname) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "", str(fname))
    return cleaned[:255] or "file"


def _is_hex(value, max_len=128) -> bool:
    return isinstance(value, str) and len(value) <= max_len and re.fullmatch(r"[0-9a-fA-F]+", value) is not None