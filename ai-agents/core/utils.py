"""
Shared utilities: ids, provenance helpers, text normalization.
"""

import hashlib
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Iterable, Optional

# --- IDs --------------------------------------------------------------------

def new_id(prefix: str) -> str:
    """Generate a short unique identifier with a readable prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def utc_now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# --- Text normalization ------------------------------------------------------
# Conservative: usable for matching without destroying legitimate content.

_UNICODE_WS = re.compile(r"\s+")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_REPEATED_PUNCT = re.compile(r"([.!?\-])\1{2,}")


def normalize_text(text: str) -> str:
    """Normalize whitespace/control chars; keep letters, digits and meaning."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = _CTRL.sub(" ", text)
    text = _UNICODE_WS.sub(" ", text)
    text = _REPEATED_PUNCT.sub(r"\1", text)
    return text.strip()


def normalize_phone(value: str) -> str:
    """Normalize a phone number to digits-only (E.164-ish minimal form)."""
    digits = re.sub(r"[^\d]", "", value)
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits.startswith(("91", "1", "44")) and len(digits) == 12:
        digits = "+" + digits
    if len(digits) == 10:
        digits = "+91" + digits  # default fixture region; overridable later
    return digits


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_username(value: str) -> str:
    return value.strip().lstrip("@").lower()


def dedupe_preserving_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


# --- Hashing -----------------------------------------------------------------


def sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    """SHA-256 of a file, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(name: str) -> str:
    """Strip path components and dangerous characters from a filename."""
    base = name.replace("\\", "/").split("/")[-1]
    base = unicodedata.normalize("NFC", base)
    base = re.sub(r"[^\w.\- ]", "_", base)
    base = base.strip(" ._-")
    return base or "unnamed_file"


# --- Provenance convenience --------------------------------------------------


def provenance_kwargs(agent_name: str, evidence_id: str, source_reference: str = "", **extra):
    """Build provenance dict kwargs with the agent name filled in."""
    data = {
        "evidence_id": evidence_id,
        "source_reference": source_reference,
        "agent_name": agent_name,
        **extra,
    }
    return {k: v for k, v in data.items() if v not in (None, "")}


def excerpt(text: str, max_chars: int = 200) -> str:
    """Short evidence excerpt for provenance display."""
    if not text:
        return ""
    text = normalize_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def optional_iso_parse(value: Optional[str]) -> Optional[str]:
    """Parse common timestamp formats into ISO-8601; None when unparseable."""
    if not value:
        return None
    text = value.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %I:%M:%S %p",
        "%d/%m/%Y %I:%M %p",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %I:%M:%S %p",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d %b %Y %H:%M",
        "%d %B %Y %H:%M",
        "%d %b %Y %I:%M %p",
    ):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return None