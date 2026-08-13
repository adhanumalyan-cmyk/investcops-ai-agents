"""
Agent 4: Relationship Analysis.

Evidence-grounded: relationships are derived from co-occurrence within chat
lines/messages and email header structure. Types: CALLED, MESSAGED, EMAILED,
CONTACTED, LOCATED_AT, USED, OWNED, WORKS_AT, ASSOCIATED_WITH, CONNECTED_TO.
"""

import re
from typing import Any, Dict, List, Tuple

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.extract import chat_messages, extract_emails, sentence_split
from core.state import Entity, InvestigationState, Relationship, ReviewStatus

CALLED_RE = re.compile(r"\b(?:called|phoned|dialed|rang|on call|call(?:ed)? to|talked to)\b", re.I)
MESSAGED_RE = re.compile(r"\b(?:message(?:d|s)?|sent to|replied to|forwarded to|DM(?:'d)? to)\b", re.I)
EMAILED_RE = re.compile(r"\b(?:email(?:ed)? to|sent via email|mail to)\b", re.I)
VISITED_RE = re.compile(r"\b(?:visited|went to|reached|travelled to|at)\b", re.I)
USED_RE = re.compile(r"\b(?:uses?|using|used|logged in with)\b", re.I)
WORKS_RE = re.compile(r"\b(?:works at|employed at|job at|worked at)\b", re.I)


class Agent4Relationships(BaseAgent):
    name = "agent_4_relationships"
    description = "Relationship Analysis"
    prompt_version = "4.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        entities = state.entities
        if not entities:
            raise InsufficientEvidenceError("No entities available; run entity extraction first.")

        rels: List[Relationship] = []
        rows = self._extract_rows(state)

        for row in rows:
            rels.extend(self._row_relationships(state, row))

        # Same-evidence co-occurrence relationships between entity pairs.
        rels.extend(self._cooccurrence_relationships(state, rows))

        deduped = self._dedupe(rels)
        result = {
            "relationship_count": len(deduped),
            "by_type": _count_by_type(deduped),
            "top_relationships": [
                {
                    "relationship_id": r.relationship_id,
                    "source": r.source_entity_value,
                    "type": r.relation_type,
                    "target": r.target_entity_value,
                    "confidence": r.confidence,
                }
                for r in sorted(deduped, key=lambda x: -x.confidence)[:25]
            ],
        }
        confidence = round(
            sum(r.confidence for r in deduped) / len(deduped), 3
        ) if deduped else 0.0
        warnings = (
            ["No relationships identified from current entities."]
            if not deduped
            else []
        )
        return {
            "result": result,
            "state_fields": {"relationships": deduped},
            "confidence": confidence,
            "evidence_references": [
                self._provenance(
                    r.supporting_evidence_ids[0],
                    source_reference=r.source_reference,
                    excerpt_or_locator=f"{r.source_entity_value} {r.relation_type} {r.target_entity_value}",
                    confidence=r.confidence,
                )
                for r in deduped[:50]
                if r.supporting_evidence_ids
            ],
            "warnings": warnings,
            "evidence_ids": sorted({r.supporting_evidence_ids[0] for r in deduped if r.supporting_evidence_ids}),
        }

    # --- row building --------------------------------------------------------

    def _extract_rows(self, state: InvestigationState) -> List[dict]:
        """Rows = chat messages + plain sentences, each with evidence + location."""
        rows: List[dict] = []
        docs = {d["evidence_id"]: d for d in state.cleaned_documents}
        for ev in state.validated_evidence:
            text = docs.get(ev.evidence_id, {}).get("text", "")
            if not text:
                continue
            for ts, sender, msg, _t in chat_messages(text):
                rows.append(
                    {
                        "evidence_id": ev.evidence_id,
                        "file_name": ev.file_name,
                        "text": f"{sender}: {msg}",
                        "sender": sender.strip(),
                        "reference": f"{ev.evidence_id}:{sender.strip()}",
                    }
                )
            for unit in sentence_split(text):
                rows.append(
                    {
                        "evidence_id": ev.evidence_id,
                        "file_name": ev.file_name,
                        "text": unit,
                        "sender": "",
                        "reference": f"{ev.evidence_id}:{unit[:40]}",
                    }
                )
        # email headers
        for ev in state.validated_evidence:
            text = docs.get(ev.evidence_id, {}).get("text", "") or ""
            froms = re.findall(r"^From:\s*(.+)$", text, re.M)
            tos = re.findall(r"^To:\s*(.+)$", text, re.M)
            for f in froms[:1]:
                for t in tos[:3]:
                    for fe in extract_emails(f):
                        for te in extract_emails(t):
                            rows.append(
                                {
                                    "evidence_id": ev.evidence_id,
                                    "file_name": ev.file_name,
                                    "text": f"{fe} emailed {te}",
                                    "sender": fe,
                                    "reference": f"{ev.evidence_id}:email-header",
                                }
                            )
        return rows

    # --- relationship derivation ----------------------------------------------

    def _row_relationships(self, state: InvestigationState, row: dict) -> List[Relationship]:
        rels: List[Relationship] = []
        ents = self._row_entities(state, row["text"])
        if len(ents) < 2:
            return rels
        low = row["text"].lower()
        is_email_row = "email-header" in row["reference"]

        if is_email_row:
            rtype = "EMAILED"
        elif CALLED_RE.search(low):
            rtype = "CALLED"
        elif MESSAGED_RE.search(low) or ":" in row["text"][:200] and row["sender"]:
            rtype = "MESSAGED"
        elif EMAILED_RE.search(low):
            rtype = "EMAILED"
        elif VISITED_RE.search(low):
            rtype = "VISITED" if any(e.entity_type == "LOCATION" for e in ents) else "CONTACTED"
        elif USED_RE.search(low):
            rtype = "USED"
        elif WORKS_RE.search(low):
            rtype = "WORKS_AT"
        else:
            rtype = "ASSOCIATED_WITH"

        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                a, b = ents[i], ents[j]
                rels.append(
                    self._make_relationship(a, b, rtype, row, 0.7)
                )
        return rels

    def _row_entities(self, state: InvestigationState, text: str) -> List[Entity]:
        """Entities from current state that appear in this row text."""
        out: List[Entity] = []
        low = text.lower()
        for e in state.entities:
            key = e.normalized_value.lower().lstrip("@")
            if key and key in low:
                out.append(e)
        return out[:6]

    def _cooccurrence_relationships(self, state: InvestigationState, rows: List[dict]) -> List[Relationship]:
        """Same sender-row co-occurrence across evidence: CONTACTED/CONNECTED_TO."""
        rels: List[Relationship] = []
        evidence_senders: dict[str, dict] = {}
        for row in rows:
            if row["sender"]:
                evidence_senders.setdefault(row["evidence_id"], set()).add(row["sender"])
        senders = sorted({s for vals in evidence_senders.values() for s in vals})
        if len(senders) >= 2:
            rels.append(
                Relationship(
                    source_entity_id="",
                    source_entity_value=senders[0],
                    source_entity_type="USERNAME",
                    relation_type="CONNECTED_TO",
                    target_entity_id="",
                    target_entity_value=senders[1],
                    target_entity_type="USERNAME",
                    confidence=0.6,
                    supporting_evidence_ids=[eid for eid, s in evidence_senders.items() if senders[0] in s or senders[1] in s][:5],
                    source_reference="cross-evidence sender overlap",
                )
            )
        return rels

    def _make_relationship(
        self, a: Entity, b: Entity, rtype: str, row: dict, base_conf: float
    ) -> Relationship:
        conf = base_conf
        if rtype == "ASSOCIATED_WITH":
            conf = 0.5
        if a.entity_type == "LOCATION" or b.entity_type == "LOCATION":
            rtype = "LOCATED_AT" if a.entity_type == "LOCATION" or b.entity_type == "LOCATION" else rtype
            conf = max(conf, 0.55)
        if rtype == "USED" and a.entity_type in ("DEVICE", "IP") and b.entity_type in ("PERSON", "USERNAME"):
            conf = 0.8
        return Relationship(
            source_entity_id=a.entity_id,
            source_entity_value=a.normalized_value,
            source_entity_type=a.entity_type,
            relation_type=rtype,
            target_entity_id=b.entity_id,
            target_entity_value=b.normalized_value,
            target_entity_type=b.entity_type,
            confidence=round(conf, 2),
            supporting_evidence_ids=[row["evidence_id"]],
            source_reference=row["reference"],
            review_status=ReviewStatus.PENDING_REVIEW,
        )

    def _dedupe(self, rels: List[Relationship]) -> List[Relationship]:
        merged: dict[Tuple[str, str, str], Relationship] = {}
        for r in rels:
            key = (r.source_entity_value.lower(), r.relation_type, r.target_entity_value.lower())
            prev = merged.get(key)
            if prev is None:
                merged[key] = r.model_copy(deep=True)
                continue
            prev.confidence = round(max(prev.confidence, r.confidence), 2)
            if r.supporting_evidence_ids and r.supporting_evidence_ids[0] not in prev.supporting_evidence_ids:
                prev.supporting_evidence_ids.append(r.supporting_evidence_ids[0])
        return list(merged.values())


def _count_by_type(rels: List[Relationship]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rels:
        counts[r.relation_type] = counts.get(r.relation_type, 0) + 1
    return dict(sorted(counts.items(), key=lambda i: -i[1]))