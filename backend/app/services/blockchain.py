"""
Blockchain evidence ledger (SHA-256 notarization).

File-backed ledger (ledger.json) mirroring the frontend's localStorage
contract so records are portable and inspectable. Response shapes match
the React frontend verbatim.
"""

import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path

LEDGER_FILE = Path(__file__).resolve().parent.parent.parent / "ledger.json"
MAX_LEDGER = 100
_HEX_RE = re.compile(r"[0-9a-fA-F]+")
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]")


def load_ledger() -> list[dict]:
    if LEDGER_FILE.exists():
        try:
            data = json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def save_ledger(records: list[dict]) -> None:
    LEDGER_FILE.write_text(json.dumps(records[:MAX_LEDGER], indent=2), encoding="utf-8")


def _safe_name(fname) -> str:
    cleaned = _SAFE_NAME_RE.sub("", str(fname))
    return cleaned[:255] or "file"


def _is_hex(value, max_len=128) -> bool:
    return isinstance(value, str) and len(value) <= max_len and _HEX_RE.fullmatch(value) is not None


def notarize(payload: dict) -> dict:
    """Record a SHA-256 hash (or derive one) into the ledger. Returns the ledger record."""
    fhash = payload.get("hash", "")
    if not _is_hex(fhash):
        fhash = hashlib.sha256((str(payload.get("fileName", "")) + str(time.time())).encode()).hexdigest()

    rec = {
        "hash": fhash,
        "fileName": _safe_name(payload.get("fileName", "evidence.bin")),
        "fileSize": str(payload.get("fileSize", "1.2 MB"))[:64],
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M"),
        "isoTimestamp": datetime.now().isoformat(),
        "officer": str(payload.get("officer", "InvestCops AI Unit"))[:128],
        "badge": str(payload.get("badge", "IC-001"))[:64],
        "caseId": str(payload.get("caseId", "IC-2026-0001"))[:64],
        "txHash": "0x" + fhash[:64],
        "blockNumber": 8000000 + int(time.time()) % 500000,
        "verified": True,
    }
    ledger = load_ledger()
    ledger.insert(0, rec)
    save_ledger(ledger)
    return rec


def verify(hash_value: str) -> dict:
    """Verify a hash against the ledger. Returns {verified: bool, record?: dict}."""
    found = next((r for r in load_ledger() if r["hash"] == hash_value), None)
    if found:
        return {"verified": True, "record": found}
    return {"verified": False}


def get_ledger() -> dict:
    return {"ledger": load_ledger()}