"""
Agent 7: Contradiction Detection.

Derived contradictions are investigative leads, never proof of guilt.
Deterministic conflict detection plus optional LLM statement comparison.
"""

import re
from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.state import Contradiction, InvestigationState, ReviewStatus

_OPPOSITES = [
    ("yes", "no"),
    ("did not", "did"),
    ("never", "always"),
    ("wasn't", "was"),
    ("was not", "was"),
    ("not at home", "at home"),
    ("not there", "was there"),
]


class Agent7Contradict(BaseAgent):
    name = "agent_7_contradict"
    description = "Contradiction Detection"
    prompt_version = "7.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        contradictions: List[Contradiction] = []
        docs = {d["evidence_id"]: d for d in state.cleaned_documents}

        if not state.validated_evidence:
            raise InsufficientEvidenceError("No validated evidence available.")

        contradictions.extend(self._statement_contradictions(state, docs))
        contradictions.extend(self._contact_conflicts(state))

        deduped = self._dedupe(contradictions)
        result = {
            "contradiction_count": len(deduped),
            "by_severity": _by_severity(deduped),
            "contradictions": [
                {
                    "contradiction_id": c.contradiction_id,
                    "claim_a": c.claim_a,
                    "claim_b": c.claim_b,
                    "severity": c.severity,
                    "confidence": c.confidence,
                    "explanation": c.explanation,
                }
                for c in deduped
            ],
        }
        confidence = round(sum(c.confidence for c in deduped) / len(deduped), 3) if deduped else 0.0

        refs = []
        for c in deduped:
            for eid in (c.evidence_a + c.evidence_b)[:2]:
                refs.append(
                    self._provenance(
                        eid,
                        excerpt_or_locator=f"{c.claim_a[:100]} vs {c.claim_b[:100]}",
                        confidence=c.confidence,
                    )
                )

        return {
            "result": result,
            "state_fields": {"contradictions": deduped},
            "confidence": confidence,
            "evidence_references": refs,
            "warnings": (
                ["No contradictions detected."]
                if not deduped
                else ["Contradictions are leads for investigation, not proof of guilt."]
            ),
            "evidence_ids": sorted({eid for c in deduped for eid in c.evidence_a + c.evidence_b}),
        }

    # --- deterministic checks -------------------------------------------------

    def _statement_contradictions(
        self, state: InvestigationState, docs: dict
    ) -> List[Contradiction]:
        contradictions: List[Contradiction] = []
        statements: List[dict] = []
        for ev in state.validated_evidence:
            text = (docs.get(ev.evidence_id, {}) or {}).get("text", "")
            for line in text.splitlines()[:200]:
                line = line.strip()
                if len(line) < 15 or line.startswith(("---", "===", "From:", "To:", "Date:", "Subject:")):
                    continue
                statements.append({"evidence_id": ev.evidence_id, "text": line})

        # Sequential contradiction pairs within the same evidence source.
        for i in range(len(statements)):
            for j in range(i + 1, min(i + 8, len(statements))):
                a, b = statements[i], statements[j]
                if self._are_opposed(a["text"], b["text"]):
                    contradictions.append(
                        Contradiction(
                            claim_a=a["text"][:240],
                            claim_b=b["text"][:240],
                            evidence_a=[a["evidence_id"]],
                            evidence_b=[b["evidence_id"]],
                            severity="MEDIUM",
                            confidence=0.6,
                            explanation=(
                                f"Statements from evidence {a['evidence_id']} appear to conflict on the same subject. "
                                "This is a lead; a human investigator must verify the actual meaning."
                            ),
                            review_status=ReviewStatus.PENDING_REVIEW,
                        )
                    )

        # Same-subject conflicts across different evidence sources (topic + negation overlap).
        for ev_a in state.validated_evidence:
            text_a = (docs.get(ev_a.evidence_id, {}) or {}).get("text", "")
            for ev_b in state.validated_evidence:
                if ev_a.evidence_id >= ev_b.evidence_id:
                    continue
                text_b = (docs.get(ev_b.evidence_id, {}) or {}).get("text", "")
                topics = self._shared_topics(text_a, text_b)
                for topic in topics:
                    sentences_a = [s for s in re.split(r"(?<=[.!?])\s+", text_a) if topic in s.lower()][:3]
                    sentences_b = [s for s in re.split(r"(?<=[.!?])\s+", text_b) if topic in s.lower()][:3]
                    for sa in sentences_a[:1]:
                        for sb in sentences_b[:1]:
                            if self._are_opposed(sa, sb):
                                contradictions.append(
                                    Contradiction(
                                        claim_a=sa[:240],
                                        claim_b=sb[:240],
                                        evidence_a=[ev_a.evidence_id],
                                        evidence_b=[ev_b.evidence_id],
                                        severity="HIGH",
                                        confidence=0.65,
                                        explanation=(
                                            f"Same topic '{topic}' asserted in evidence {ev_a.evidence_id} "
                                            f"and opposed in {ev_b.evidence_id}. Cross-source conflict - high priority lead."
                                        ),
                                        review_status=ReviewStatus.PENDING_REVIEW,
                                    )
                                )
        return contradictions

    def _contact_conflicts(self, state: InvestigationState) -> List[Contradiction]:
        """Same person name mapped to multiple different phone/email values."""
        conflicts: List[Contradiction] = []
        persons = [e for e in state.entities if e.entity_type == "PERSON"]
        contacts = [
            e for e in state.entities if e.entity_type in ("PHONE", "EMAIL", "USERNAME")
        ]
        for person in persons:
            low = person.normalized_value.lower()
            matched = [c for c in contacts if low in c.source_reference.lower() or c.value.lower().find(low) >= 0]
            phones = [c.normalized_value for c in matched if c.entity_type == "PHONE"]
            emails = [c.normalized_value for c in matched if c.entity_type == "EMAIL"]
            unique_phones = list(dict.fromkeys(phones))
            if len(unique_phones) >= 2:
                conflicts.append(
                    Contradiction(
                        claim_a=f"{person.normalized_value} is associated with phone {unique_phones[0]}",
                        claim_b=f"{person.normalized_value} is associated with phone {unique_phones[1]}",
                        evidence_a=[c.evidence_id for c in matched if c.entity_type == "PHONE"][:2],
                        evidence_b=[c.evidence_id for c in matched if c.entity_type == "PHONE"][2:4] or [c.evidence_id for c in matched if c.entity_type == "PHONE"][:1],
                        severity="LOW",
                        confidence=0.5,
                        explanation="Multiple distinct phone numbers co-occur with the same person name in the evidence. Could indicate different lines or an identity discrepancy.",
                        review_status=ReviewStatus.PENDING_REVIEW,
                    )
                )
        return conflicts

    # --- helpers ---------------------------------------------------------------

    def _are_opposed(self, sa: str, sb: str) -> bool:
        la, lb = sa.lower(), sb.lower()
        a = la.replace("i ", " ").replace("we ", " ")
        b = lb.replace("i ", " ").replace("we ", " ")
        if a[:60] == b[:60] or a[60:120] == b[60:120]:
            return False
        core_a = a.split(":")[-1][:80] if ":" in a else a[:80]
        core_b = b.split(":")[-1][:80] if ":" in b else b[:80]
        if len(core_a) < 20 or len(core_b) < 20:
            return False
        for first, second in _OPPOSITES:
            if first in core_a and second in core_b:
                overlap = set(core_a.split()) & set(core_b.split())
                if len(overlap) >= 2:
                    return True
            if second in core_a and first in core_b:
                overlap = set(core_a.split()) & set(core_b.split())
                if len(overlap) >= 2:
                    return True
        return False

    @staticmethod
    def _shared_topics(text_a: str, text_b: str) -> List[str]:
        topics: List[str] = []
        stops = {"the", "and", "that", "this", "with", "from", "have", "will", "your", "you", "was", "were", "are", "but", "not", "for"}
        words_a = {w for w in re.findall(r"[a-z]{4,}", text_a.lower()) if w not in stops}
        words_b = {w for w in re.findall(r"[a-z]{4,}", text_b.lower()) if w not in stops}
        for w in sorted(words_a & words_b):
            if text_a.lower().count(w) >= 1 and text_b.lower().count(w) >= 1:
                topics.append(w)
        return topics[:4]

    @staticmethod
    def _dedupe(items: List[Contradiction]) -> List[Contradiction]:
        seen: set[tuple] = set()
        out: List[Contradiction] = []
        for c in items:
            key = (c.claim_a[:60], c.claim_b[:60])
            if key not in seen:
                seen.add(key)
                out.append(c)
        return out


def _by_severity(items: List[Contradiction]) -> dict[str, int]:
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for c in items:
        counts[c.severity] = counts.get(c.severity, 0) + 1
    return counts