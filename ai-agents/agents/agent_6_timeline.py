"""
Agent 6: Timeline Reconstruction.

Timestamps are extracted from chat lines, email headers, image metadata and
transaction entries in the actual evidence. Events without a parseable
timestamp are NOT added to the timeline.
"""

import re
from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.extract import chat_messages, extract_transactions
from core.state import InvestigationState, TimelineEvent
from core.utils import optional_iso_parse

# WhatsApp/Telegram: [12/02/2025, 3:45:12 PM] or 12/02/2025 3:45:12 PM
_ISO_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?\b")


class Agent6Timeline(BaseAgent):
    name = "agent_6_timeline"
    description = "Timeline Reconstruction"
    prompt_version = "6.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        if not state.validated_evidence:
            raise InsufficientEvidenceError("No validated evidence; timeline cannot be built.")

        events: List[TimelineEvent] = []
        docs = {d["evidence_id"]: d for d in state.cleaned_documents}

        for ev in state.validated_evidence:
            text = docs.get(ev.evidence_id, {}).get("text", "") if docs else ""
            if not text:
                continue
            self._chat_events(ev.evidence_id, ev.file_name, text, events)
            self._iso_events(ev.evidence_id, ev.file_name, text, events)
            self._transaction_events(ev.evidence_id, ev.file_name, text, events)

        unique = self._dedupe(events)
        unique.sort(key=lambda e: e.timestamp_iso or "9999")

        entities_by_evidence: dict[str, List[str]] = {}
        for ent in state.entities:
            for eid in ent.evidence_id.split(","):
                if eid:
                    entities_by_evidence.setdefault(eid, []).append(ent.normalized_value)

        for e in unique:
            e.entities = list(dict.fromkeys(entities_by_evidence.get(e.evidence_ids[0], [])))[:8]

        result = {
            "event_count": len(unique),
            "earliest_event": unique[0].timestamp if unique else None,
            "latest_event": unique[-1].timestamp if unique else None,
            "by_type": _count_by_type(unique),
            "events": [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "description": e.description,
                    "evidence_ids": e.evidence_ids,
                }
                for e in unique
            ],
        }
        confidence = round(sum(e.confidence for e in unique) / len(unique), 3) if unique else 0.0
        warnings = (
            ["No timestamped events could be extracted from the current evidence."]
            if not unique
            else []
        )
        return {
            "result": result,
            "state_fields": {"timeline": unique},
            "confidence": confidence,
            "evidence_references": [
                self._provenance(
                    e.evidence_ids[0],
                    source_reference=e.source_reference,
                    timestamp=e.timestamp,
                    excerpt_or_locator=e.description[:160],
                    confidence=e.confidence,
                )
                for e in unique
            ],
            "warnings": warnings,
            "evidence_ids": sorted({e.evidence_ids[0] for e in unique}),
        }

    def _chat_events(
        self, evidence_id: str, file_name: str, text: str, events: List[TimelineEvent]
    ) -> None:
        for date_pt, sender, message, time_pt in chat_messages(text):
            iso = optional_iso_parse(f"{date_pt} {time_pt}")
            if not iso:
                iso = optional_iso_parse(f"{date_pt}")
            if not iso:
                continue
            events.append(
                TimelineEvent(
                    timestamp=f"{date_pt} {time_pt}",
                    timestamp_iso=iso,
                    event_type="MESSAGE",
                    description=f"{sender}: {message[:240]}",
                    evidence_ids=[evidence_id],
                    source_reference=f"{file_name}:{sender}",
                    confidence=0.85,
                )
            )

    def _iso_events(
        self, evidence_id: str, file_name: str, text: str, events: List[TimelineEvent]
    ) -> None:
        for m in _ISO_RE.finditer(text):
            iso = optional_iso_parse(m.group(0))
            if not iso:
                continue
            start = max(0, m.start() - 120)
            snippet = re.sub(r"\s+", " ", text[start:m.end() + 160])
            events.append(
                TimelineEvent(
                    timestamp=m.group(0),
                    timestamp_iso=iso,
                    event_type="RECORD",
                    description=snippet[:240],
                    evidence_ids=[evidence_id],
                    source_reference=f"{file_name}:iso-timestamp",
                    confidence=0.8,
                )
            )

    def _transaction_events(
        self, evidence_id: str, file_name: str, text: str, events: List[TimelineEvent]
    ) -> None:
        for date_pt, desc, amount in extract_transactions(text):
            iso = optional_iso_parse(date_pt)
            if not iso:
                continue
            events.append(
                TimelineEvent(
                    timestamp=date_pt,
                    timestamp_iso=iso,
                    event_type="TRANSACTION",
                    description=f"Transaction {amount}: {desc[:200]}",
                    evidence_ids=[evidence_id],
                    source_reference=f"{file_name}:txn",
                    confidence=0.8,
                )
            )

    def _dedupe(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        seen: dict[tuple[str, str], TimelineEvent] = {}
        for e in events:
            key = (e.timestamp_iso or e.timestamp, e.description[:80])
            prev = seen.get(key)
            if prev is None:
                seen[key] = e
            elif e.evidence_ids[0] not in prev.evidence_ids:
                prev.evidence_ids.append(e.evidence_ids[0])
        return list(seen.values())


def _count_by_type(events: List[TimelineEvent]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in events:
        counts[e.event_type] = counts.get(e.event_type, 0) + 1
    return dict(sorted(counts.items(), key=lambda i: -i[1]))