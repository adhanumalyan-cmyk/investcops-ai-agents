"""
Deterministic extraction helpers shared by agents 2, 3, 6 and 10.
These parsers are real, reproducible and evidence-grounded; the LLM layer
(below) only adds semantic interpretation on top.
"""

import re
from typing import Iterable

# --- regexes -----------------------------------------------------------------

PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,5}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{3,5}(?!\d)"
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
USERNAME_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_.]{2,30})(?![\w@])")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+")
DATE_RE = re.compile(
    r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\b"
)
TIME_RE = re.compile(r"\b(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\b")
VEHICLE_RE = re.compile(
    r"\b(?:[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,2}\s?\d{1,4}|[A-Z]{2}\d{2}\s[A-Z]{3})\b"
)
BANK_ACCOUNT_RE = re.compile(r"\b(?:\d{9,18})\b")
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
MONEY_RE = re.compile(r"\b(?:Rs\.?|INR|₹|\$|USD|EUR)\s?\d[\d,]*(?:\.\d{1,2})?\b")

# Timestamp lines: WhatsApp/Telegram style "[12/02/2025, 3:45:12 PM] Sender: msg"
CHAT_TIMESTAMP_RE = re.compile(
    r"\[?(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})[, ]+(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\]?\s*([^:\n]+):\s?(.*)"
)

# --- indicator keywords (Agent 2 / Agent 8) ----------------------------------

INDICATOR_KEYWORDS = {
    "threat": ["threat", "will kill", "i kill", "you will be sorry", "harm"],
    "harassment": ["harass", "stalk", "blackmail", "extort"],
    "financial_fraud": ["upi", "transfer", "fraud", "scam", "fake", "investment scheme", "pay me", "send money", "bank account"],
    "coercion": ["forced", "pressure", "threaten", "scared", "afraid", "don't tell anyone"],
    "drugs": ["drug", "ganja", "cocaine", "weed", "parcel"],
    "identity_theft": ["otp", "password", "aadhaar", "pan card", "sim swap"],
}

TITLE_PERSON_RE = re.compile(
    r"(?:Mr|Mrs|Ms|Dr|Er|Prof|Smt)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
)

NAME_HINT_RE = re.compile(
    r"(?:name(?:d| is|:)?|calls? (?:herself|himself|themself)|identity|account (?:name|holder)|sent by|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
)


def indicator_hits(text: str) -> list[tuple[str, str]]:
    """Return (category, matched keyword) hits found in text."""
    hits: list[tuple[str, str]] = []
    low = text.lower()
    for category, keywords in INDICATOR_KEYWORDS.items():
        for kw in keywords:
            if kw in low:
                hits.append((category, kw))
    return hits


def extract_phones(text: str) -> list[str]:
    out = []
    for m in PHONE_RE.finditer(text):
        raw = m.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if len(digits) >= 8 and len(digits) <= 15:
            out.append(raw)
    return out


def extract_emails(text: str) -> list[str]:
    return list(dict.fromkeys(EMAIL_RE.findall(text)))


def extract_usernames(text: str) -> list[str]:
    return [m.group(1) for m in USERNAME_RE.finditer(text)]


def extract_ips(text: str) -> list[str]:
    return [ip for ip in dict.fromkeys(IP_RE.findall(text)) if not any(int(o) > 255 for o in ip.split("."))]


def extract_urls(text: str) -> list[str]:
    return list(dict.fromkeys(URL_RE.findall(text)))


def extract_dates(text: str) -> list[str]:
    return list(dict.fromkeys(DATE_RE.findall(text)))


def extract_times(text: str) -> list[str]:
    return [t for t in dict.fromkeys(TIME_RE.findall(text)) if ":" in t]


def extract_vehicles(text: str) -> list[str]:
    return list(dict.fromkeys(VEHICLE_RE.findall(text)))


def extract_transactions(text: str) -> list[tuple[str, str, str]]:
    """Bank style entries: (date, description, amount)."""
    rows: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        date = DATE_RE.search(line)
        money = MONEY_RE.search(line)
        if date and money and re.search(r"(?:txn|transaction|debit|credit|paid|received|transfer)", line.lower()):
            rows.append((date.group(0), line.strip(), money.group(0)))
    return rows


def extract_locations(text: str) -> list[str]:
    """Heuristic LOCATION candidates: capitalized words after place prepositions."""
    out: list[str] = []
    for m in re.finditer(r"\b(?:at|in|near|from|to|visited|reached|stayed(?:ed)? at)\s+([A-Z][a-zA-Z ]{2,25})", text):
        candidate = m.group(1).strip()
        if not re.search(r"\b(the|a|an|my|his|her|our|their)\b", candidate.lower()):
            out.append(candidate)
    return out


def extract_names(text: str) -> list[str]:
    out: list[str] = []
    for m in TITLE_PERSON_RE.finditer(text):
        out.append(m.group(1))
    for m in NAME_HINT_RE.finditer(text):
        out.append(m.group(1))
    return out


def chat_messages(text: str) -> list[tuple[str, str, str, str]]:
    """Parse timestamped chat lines -> (timestamp_text, sender, message, time)"""
    out: list[tuple[str, str, str, str]] = []
    for m in CHAT_TIMESTAMP_RE.finditer(text):
        out.append((m.group(1), m.group(3).strip(), m.group(4).strip(), m.group(2)))
    return out


def sentence_split(text: str, max_len: int = 320) -> list[str]:
    """Split into reasonable analysis units (lines or sentences)."""
    units = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("---", "===")):
            continue
        if len(line) > max_len:
            line = line[:max_len] + "..."
        units.append(line)
    return units


def sentence_units(text: str) -> list[str]:
    import re as _re

    return [u for u in _re.split(r"(?<=[.!?])\s+", text) if len(u.strip()) > 12]


def rank_units_by_keywords(text: str, keywords: Iterable[str], limit: int = 8) -> list[str]:
    """Return the most keyword-dense sentence units (deterministic ranking)."""
    units = sentence_units(text) or sentence_split(text)
    scored = []
    for u in units:
        low = u.lower()
        score = sum(1 for k in keywords if k in low)
        if score:
            scored.append((score, -len(u), u))
    scored.sort(reverse=True)
    return [u for _, _, u in scored[:limit]]