"""
Agent 5: Cross-Evidence Correlation.

Connects entities that appear across multiple evidence sources. Deliberately
conservative: never assumes identity; produces possible_match with
match_confidence + review_status = PENDING_REVIEW.
"""

from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.state import CorrelationMatch, Entity, InvestigationState, ReviewStatus


class Agent5Correlate(BaseAgent):
    name = "agent_5_correlate"
    description = "Cross-Evidence Correlation"
    prompt_version = "5.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        entities = state.entities
        if len(entities) < 2:
            raise InsufficientEvidenceError("Need at least two entities to correlate.")

        matches: List[CorrelationMatch] = []
        by_signature: dict[str, List[Entity]] = {}

        for e in entities:
            sig = self._signature(e)
            by_signature.setdefault(sig, []).append(e)

        # Exact-value matches across >=2 evidence sources.
        for sig, group in by_signature.items():
            if not sig:
                continue
            evidence_ids = sorted({e.evidence_id for e in group})
            if len(evidence_ids) >= 2:
                e0 = group[0]
                matches.append(
                    CorrelationMatch(
                        entity_a_id=e0.entity_id,
                        entity_a_value=e0.normalized_value,
                        entity_b_id=",".join(e.entity_id for e in group[1:]),
                        entity_b_value=e0.normalized_value,
                        match_type=self._match_type(e0.entity_type),
                        match_confidence=self._confidence(e0.entity_type),
                        supporting_evidence=evidence_ids,
                        review_status=ReviewStatus.PENDING_REVIEW,
                        explanation=(
                            f"Identifier {e0.normalized_value} ({e0.entity_type}) appears in "
                            f"{len(evidence_ids)} evidence sources: {', '.join(evidence_ids)}. "
                            "This is a possible match for the same person/account/device - investigator verification required."
                        ),
                    )
                )

        # Cross-type linkage: same value text under different types (e.g., person vs username spelling).
        by_value: dict[str, List[Entity]] = {}
        for e in entities:
            key = e.normalized_value.lower().lstrip("@")
            if key:
                by_value.setdefault(key, []).append(e)
        for value, group in by_value.items():
            types = {e.entity_type for e in group}
            if len(types) >= 2:
                e0 = group[0]
                matches.append(
                    CorrelationMatch(
                        entity_a_id=e0.entity_id,
                        entity_a_value=e0.normalized_value,
                        entity_b_id=",".join(e.entity_id for e in group[1:]),
                        entity_b_value=e0.normalized_value,
                        match_type="possible_match",
                        match_confidence=0.55,
                        supporting_evidence=sorted({e.evidence_id for e in group}),
                        review_status=ReviewStatus.PENDING_REVIEW,
                        explanation=(
                            f"Entity text '{value}' surfaces under multiple types {sorted(types)}. "
                            "May indicate the same person/account; manual review required."
                        ),
                    )
                )

        deduped = self._dedupe(matches)
        patterns = self._patterns(deduped)
        confidence = round(
            sum(m.match_confidence for m in deduped) / len(deduped), 3
        ) if deduped else 0.0

        return {
            "result": {
                "correlation_count": len(deduped),
                "patterns": patterns,
                "matches": [
                    {
                        "correlation_id": m.correlation_id,
                        "value": m.entity_a_value,
                        "match_type": m.match_type,
                        "match_confidence": m.match_confidence,
                        "evidence": m.supporting_evidence,
                    }
                    for m in deduped
                ],
            },
            "state_fields": {"correlated_entities": deduped},
            "confidence": confidence,
            "evidence_references": [
                self._provenance(
                    m.supporting_evidence[0],
                    source_reference=m.explanation[:160],
                    excerpt_or_locator=f"{m.entity_a_value} across {len(m.supporting_evidence)} sources",
                    confidence=m.match_confidence,
                )
                for m in deduped
            ],
            "warnings": (
                []
                if deduped
                else ["No cross-evidence correlations identified."]
            ),
            "evidence_ids": sorted({eid for m in deduped for eid in m.supporting_evidence}),
        }

    @staticmethod
    def _signature(e: Entity) -> str:
        if e.entity_type in ("PHONE", "EMAIL", "USERNAME", "IP", "URL", "ACCOUNT", "VEHICLE", "DEVICE"):
            return f"{e.entity_type}:{e.normalized_value.lower()}"
        return ""

    @staticmethod
    def _match_type(etype: str) -> str:
        return {
            "PHONE": "same_phone",
            "EMAIL": "same_email",
            "USERNAME": "same_username",
            "IP": "same_ip",
            "ACCOUNT": "same_account",
            "DEVICE": "same_device",
            "VEHICLE": "same_vehicle",
            "URL": "same_url",
        }.get(etype, "possible_match")

    @staticmethod
    def _confidence(etype: str) -> float:
        return {
            "PHONE": 0.92, "EMAIL": 0.95, "ACCOUNT": 0.9, "IP": 0.88,
            "DEVICE": 0.85, "VEHICLE": 0.8, "URL": 0.8, "USERNAME": 0.75,
        }.get(etype, 0.6)

    def _dedupe(self, matches: List[CorrelationMatch]) -> List[CorrelationMatch]:
        seen: dict[tuple[str, str, str], CorrelationMatch] = {}
        for m in matches:
            key = (m.entity_a_value.lower(), m.match_type, m.entity_b_value.lower())
            prev = seen.get(key)
            if prev is None:
                seen[key] = m
            else:
                for eid in m.supporting_evidence:
                    if eid not in prev.supporting_evidence:
                        prev.supporting_evidence.append(eid)
                prev.supporting_evidence = sorted(set(prev.supporting_evidence))
        return list(seen.values())

    @staticmethod
    def _patterns(matches: List[CorrelationMatch]) -> List[str]:
        if not matches:
            return []
        n = len(matches)
        types = {m.match_type for m in matches}
        best = sorted(matches, key=lambda m: -m.match_confidence)[0]
        return [
            f"{sum(len(m.supporting_evidence) for m in matches)} cross-evidence links found across {n} correlations",
            f"Most confident: {best.match_type} ({best.entity_a_value}) with {best.match_confidence:.0%} confidence",
            f"Link types observed: {', '.join(sorted(types))}",
        ]