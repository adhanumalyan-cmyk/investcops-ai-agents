"""
Agent 3: Entity Extraction.

Hybrid pipeline:
1. deterministic regex extraction (phones, emails, usernames, IPs, URLs,
   dates, times, vehicles, bank refs, persons, locations)
2. normalization
3. optional LLM-assisted interpretation of candidates
4. deduplication across evidence
5. provenance attachment

Entities are always produced from actual evidence text.
"""

import re
from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.extract import (
    BANK_ACCOUNT_RE,
    IFSC_RE,
    MONEY_RE,
    extract_dates,
    extract_emails,
    extract_ips,
    extract_locations,
    extract_names,
    extract_phones,
    extract_times,
    extract_urls,
    extract_usernames,
    extract_vehicles,
)
from core.llm import complete, extract_json, llm_enabled
from core.state import Entity, InvestigationState, Provenance, utc_now_iso
from core.utils import normalize_email, normalize_phone, normalize_text, normalize_username


class Agent3Entities(BaseAgent):
    name = "agent_3_entities"
    description = "Entity Extraction"
    prompt_version = "3.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        docs = {d["evidence_id"]: d for d in state.cleaned_documents}
        if not state.validated_evidence and not docs:
            raise InsufficientEvidenceError("No validated evidence available for entity extraction.")

        entities: List[Entity] = []
        provenance: List[Provenance] = []

        for ev in state.validated_evidence:
            text = docs.get(ev.evidence_id, {}).get("text", "") if docs else ""
            if not text:
                continue
            text = normalize_text(text)
            found = self._extract_from_text(ev.evidence_id, ev.file_name, text)
            entities.extend(found)
            if found:
                provenance.append(
                    self._provenance(
                        ev.evidence_id,
                        source_reference=ev.file_name,
                        file_name=ev.file_name,
                        excerpt_or_locator=f"{len(found)} candidate entities",
                        confidence=max(e.confidence for e in found),
                    )
                )

        # Optional LLM-assisted reclassification of candidates only.
        if llm_enabled() and entities:
            try:
                entities = self._llm_refine(state, entities)
            except Exception as exc:
                self.logger.warning("LLM entity refinement unavailable: %s (deterministic results kept)", exc)

        deduped = self._dedupe(entities)
        deduped.sort(key=lambda e: (e.entity_type, e.normalized_value))

        result = {
            "entity_count": len(deduped),
            "by_type": _count_by_type(deduped),
            "top_entities": [
                {"entity_id": e.entity_id, "type": e.entity_type, "value": e.normalized_value, "confidence": e.confidence}
                for e in sorted(deduped, key=lambda x: -x.confidence)[:20]
            ],
        }
        confidence = round(
            sum(e.confidence * e.frequency for e in deduped) / max(1, sum(e.frequency for e in deduped)),
            3,
        )
        return {
            "result": result,
            "state_fields": {"entities": deduped},
            "confidence": confidence,
            "evidence_references": provenance,
            "warnings": [] if deduped else ["No entities extractable from current evidence."],
            "evidence_ids": [e.evidence_id for e in deduped],
        }

    # --- extraction ----------------------------------------------------------

    def _extract_from_text(self, evidence_id: str, file_name: str, text: str) -> List[Entity]:
        out: List[Entity] = []
        lines = text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            ref = f"{file_name}:L{line_no}"
            for value, etype, conf, norm in _line_extractions(line):
                out.append(
                    Entity(
                        entity_type=etype,
                        value=value,
                        normalized_value=norm or value,
                        confidence=conf,
                        evidence_id=evidence_id,
                        source_reference=ref,
                        first_seen=utc_now_iso(),
                        last_seen=utc_now_iso(),
                    )
                )
        return out

    def _dedupe(self, entities: List[Entity]) -> List[Entity]:
        merged: dict[tuple[str, str], Entity] = {}
        for e in entities:
            key = (e.normalized_value.lower(), e.entity_type)
            prev = merged.get(key)
            if prev is None:
                merged[key] = e.model_copy(deep=True)
                continue
            prev.frequency += 1
            prev.confidence = round(max(prev.confidence, e.confidence), 3)
            if e.evidence_id not in prev.evidence_id:
                prev.evidence_id = f"{prev.evidence_id},{e.evidence_id}"
            prev.last_seen = utc_now_iso()
        return list(merged.values())

    def _llm_refine(self, state: InvestigationState, entities: List[Entity]) -> List[Entity]:
        """Ask the LLM to reclassify/merge candidates; keep deterministic fallback on failure."""
        sample = [
            {"value": e.value, "normalized": e.normalized_value, "type": e.entity_type, "evidence": e.evidence_id}
            for e in entities[:80]
        ]
        if not sample:
            return entities
        reply = complete(
            "Below are entities extracted deterministically from digital evidence. "
            "Return ONLY a JSON list of objects {\"value\", \"type\"} where 'type' is one of "
            "PERSON,PHONE,EMAIL,USERNAME,LOCATION,ORGANIZATION,DEVICE,IP,URL,ACCOUNT,DATE,TIME,VEHICLE,TRANSACTION,OTHER. "
            "Do not add entities that are not present in the input.\n\n" + str(sample),
            system="Evidence-grounded entity classification only. Never invent entities.",
        )
        parsed = extract_json(reply)
        if not parsed or "value" not in parsed and not isinstance(parsed, list):
            return entities
        items = parsed if isinstance(parsed, list) else [parsed]
        by_value = {(e.normalized_value.lower(), e.entity_type): e for e in entities}
        for item in items:
            value = str(item.get("value", ""))
            ntype = str(item.get("type", "")).upper()
            if not value or ntype not in _VALID_TYPES:
                continue
            key = (normalize_text(value).lower(), "OTHER")
            for (nv, et), ent in by_value.items():
                if ent.normalized_value.lower() == normalize_text(value).lower():
                    key = (nv, et)
                    break
            ent = by_value.get(key)
            if ent is not None and ntype in _VALID_TYPES:
                ent.entity_type = ntype
        return list(by_value.values())


_VALID_TYPES = {
    "PERSON", "PHONE", "EMAIL", "USERNAME", "LOCATION", "ORGANIZATION",
    "DEVICE", "IP", "URL", "ACCOUNT", "DATE", "TIME", "VEHICLE", "TRANSACTION", "OTHER",
}


def _line_extractions(line: str) -> list[tuple[str, str, float, str]]:
    """Deterministic per-line extraction returning (value, type, confidence, normalized)."""
    found: list[tuple[str, str, float, str]] = []

    for raw in extract_phones(line):
        norm = normalize_phone(raw)
        if norm:
            found.append((raw, "PHONE", 0.9, norm))
    for raw in extract_emails(line):
        found.append((raw, "EMAIL", 0.95, normalize_email(raw)))
    for raw in extract_usernames(line):
        found.append(("@" + raw, "USERNAME", 0.8, normalize_username(raw)))
    for raw in extract_ips(line):
        found.append((raw, "IP", 0.85, raw))
    for raw in extract_urls(line):
        found.append((raw, "URL", 0.9, raw))
    for raw in extract_vehicles(line):
        found.append((raw, "VEHICLE", 0.85, raw.replace(" ", "").upper()))
    for raw in extract_dates(line):
        found.append((raw, "DATE", 0.8, raw))
    for raw in extract_times(line):
        found.append((raw, "TIME", 0.8, raw))
    for raw in IFSC_RE.findall(line):
        found.append((raw, "ACCOUNT", 0.9, raw))
    for m in BANK_ACCOUNT_RE.finditer(line):
        found.append((m.group(0), "ACCOUNT", 0.8, m.group(0)))
    for m in MONEY_RE.finditer(line):
        found.append((m.group(0), "TRANSACTION", 0.75, m.group(0)))
    for name in extract_names(line):
        found.append((name, "PERSON", 0.75, name.title()))
    for loc in extract_locations(line):
        found.append((loc, "LOCATION", 0.65, loc.title()))
    # device-ish tokens (IMEI/IMSI/serial style)
    imei = re.search(r"\b\d{15}\b", line)
    if imei:
        found.append((imei.group(0), "DEVICE", 0.85, imei.group(0)))

    # keep order stable and drop duplicates within the line
    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str, float, str]] = []
    for item in found:
        key = (item[0], item[1])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _count_by_type(entities: List[Entity]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in entities:
        counts[e.entity_type] = counts.get(e.entity_type, 0) + 1
    return dict(sorted(counts.items(), key=lambda i: -i[1]))