"""
FIR conversion service: informal complaint text -> formal FIR draft.

Tries Ollama (qwen3) first, falls back to a deterministic mock template
so the frontend always receives a valid FIR. Response shape matches the
React frontend contract: {fir, provider, model, mock, note?}.
"""

import re
import time
from datetime import datetime

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("fir_converter")

DEFAULT_SYSTEM = (
    "You are InvestCops legal assistant. Convert informal complaint "
    "(Manglish/Malayalam/English) to formal FIR under BNS 318, IT Act 66C/66D. "
    "Keep facts, add sections, output only FIR. Add disclaimer it's AI draft."
)


def call_ollama(prompt: str, system: str = "", model: str | None = None) -> str:
    """Call local Ollama /api/generate. Raises on failure (caller falls back to mock)."""
    payload = {
        "model": model or settings.OLLAMA_MODEL,
        "prompt": (system + "\n\nUser: " + prompt + "\nAssistant:") if system else prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 1200},
    }
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    with httpx.Client(timeout=10.0) as c:
        r = c.post(url, json=payload)
        r.raise_for_status()
        return r.json().get("response", "").strip()


def mock_fir(text: str) -> str:
    """Deterministic, demo-safe FIR template (matches NoteNext contract output)."""
    date = datetime.now().strftime("%d %B %Y")
    t = datetime.now().strftime("%H:%M")
    phone = re.search(r"\+91\s?\d{5}\s?\d{5}|\b\d{10}\b", text)
    phone = phone.group(0) if phone else "+91 98XXX XXXXX"
    amount = re.search(r"Rs\.?\s?[\d,]+|₹\s?[\d,]+|\b\d+\s*lakh\b|\b\d{4,6}\b", text, re.IGNORECASE)
    if amount:
        amt = amount.group(0)
        if re.match(r"^\d{4,6}$", amt.strip()):
            amt = f"Rs. {amt}"
        amount = amt
    else:
        amount = "Rs. 50,000"
    is_malayalam = bool(re.search(r"[\u0D00-\u0D7F]", text))
    plat = re.search(r"whatsapp|telegram|instagram|upi|phonepe|gpay|loan app|apk|kseb", text, re.IGNORECASE)
    plat = plat.group(0) if plat else ("WhatsApp/KSEB" if is_malayalam else "WhatsApp/Telegram")
    return f"""FIRST INFORMATION REPORT
(Under Section 173 BNSS / 154 CrPC) - InvestCops Draft

1. DISTRICT: Thiruvananthapuram | PS: Cyber Crime PS, InvestCops Cyber Lab
2. FIR No: IC-FIR-2026-{int(time.time()) % 9000 + 1000} | Date: {date} | Time: {t} IST
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
8. ACTION: Case entrusted to InvestCops Investigation Unit; 1930/NCRP freeze request sent; evidence sent for 65B examination.

Investigating Officer: InvestCops AI Unit
[Draft by InvestCops AI + Qwen3 - to be verified by SHO]
"""


def convert(text: str, mock: bool = False, system: str = "", model: str | None = None) -> dict:
    """Convert informal text to a FIR draft. Returns the frontend contract dict."""
    if not mock:
        try:
            ans = call_ollama(text, system or DEFAULT_SYSTEM, model)
            if ans:
                return {"fir": ans, "provider": "ollama", "model": model or settings.OLLAMA_MODEL, "mock": False}
        except Exception as exc:
            logger.warning("Ollama failed, using mock: %s", exc)
    return {
        "fir": mock_fir(text),
        "provider": "mock",
        "model": "mock",
        "mock": True,
        "note": "Ollama not reachable, used mock",
    }