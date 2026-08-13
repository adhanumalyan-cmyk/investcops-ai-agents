"""
Frontend-compat routes: the exact endpoints the React dashboard calls.

Shapes are fixed by the frontend contract - do not rename fields.
  GET  /api/health                -> service status       ({status: "ok", ...})
  POST /api/fir/convert           -> informal text -> FIR draft
  POST /api/blockchain/notarize   -> SHA-256 evidence -> ledger record
  POST /api/blockchain/verify     -> verify a hash against the ledger
  GET  /api/blockchain/ledger     -> full evidence ledger
  GET  /api/field/status          -> ADB device info (mock when offline)
  GET  /api/field/list            -> past field extraction backups
  POST /api/field/extract         -> one-click logical extraction (mock when offline)
"""

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.database.session import check_db_connection
from app.services import blockchain, fir_converter
from app.services.field_extractor import (
    BACKUP_DIR,
    device_info,
    is_adb_available,
    logical_extract,
)

router = APIRouter(tags=["frontend-compat"])


# ── Request models ───────────────────────────────────────────────────────────
class FirConvertRequest(BaseModel):
    text: str = ""
    mock: bool | None = None
    system: str | None = None
    model: str | None = None


class NotarizeRequest(BaseModel):
    fileName: str | None = None
    fileSize: str | None = None
    hash: str | None = None
    officer: str | None = None
    badge: str | None = None
    caseId: str | None = None


class VerifyRequest(BaseModel):
    hash: str = ""


class ExtractRequest(BaseModel):
    caseId: str | None = None
    case_id: str | None = None


# ── Routes ───────────────────────────────────────────────────────────────────
@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "InvestCops AI Backend (frontend-compatible API)",
        "database": "connected" if check_db_connection() else "unreachable",
        "environment": settings.ENVIRONMENT,
        "time": datetime.now().isoformat(),
        "ollama_base": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "ledger_count": len(blockchain.load_ledger()),
    }


@router.post("/api/fir/convert")
def fir_convert(payload: FirConvertRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "text is required"})
    if len(text) > settings.MAX_FIR_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"text exceeds {settings.MAX_FIR_CHARS} characters"},
        )
    system = payload.system or ""
    if len(system) > settings.MAX_SYSTEM_CHARS:
        system = ""
    return fir_converter.convert(text, mock=bool(payload.mock), system=system, model=payload.model)


@router.post("/api/blockchain/notarize")
def blockchain_notarize(payload: NotarizeRequest):
    return blockchain.notarize(payload.model_dump())


@router.post("/api/blockchain/verify")
def blockchain_verify(payload: VerifyRequest):
    if not payload.hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "hash must be a hex string"})
    return blockchain.verify(payload.hash)


@router.get("/api/blockchain/ledger")
def blockchain_ledger():
    return blockchain.get_ledger()


@router.get("/api/field/status")
def field_status():
    try:
        info = device_info()
        info["adb_available"] = is_adb_available()
        return info
    except Exception as exc:
        return {"connected": False, "mock": True, "reason": str(exc), "adb_available": False}


@router.get("/api/field/list")
def field_list():
    try:
        return {"backups": _list_backups()}
    except Exception as exc:
        return {"backups": [], "error": str(exc)}


def _list_backups() -> list[dict]:
    cases = []
    if not BACKUP_DIR.exists():
        return cases
    for d in sorted(BACKUP_DIR.iterdir(), reverse=True)[:20]:
        if not d.is_dir():
            continue
        mf = d / "manifest.json"
        if not mf.exists():
            continue
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            cases.append(
                {
                    "folder": d.name,
                    "case_id": m.get("case_id"),
                    "timestamp": m.get("timestamp"),
                    "files": len(m.get("files", [])),
                    "mock": m.get("mock"),
                }
            )
        except Exception:
            pass
    return cases


@router.post("/api/field/extract")
def field_extract(payload: ExtractRequest):
    case_id = str(payload.caseId or payload.case_id or "KPC-2026-8941")[:128]
    try:
        res = logical_extract(case_id)
        for f in res.get("files", [])[:10]:
            try:
                blockchain.notarize(
                    {
                        "hash": f["sha256"],
                        "fileName": f["path"],
                        "fileSize": str(f["size"]) + " bytes",
                        "officer": "Field Extractor",
                        "badge": "IC-FIELD",
                        "caseId": case_id,
                    }
                )
            except Exception:
                pass
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"success": False, "error": str(exc)})