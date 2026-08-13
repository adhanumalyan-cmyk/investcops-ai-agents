"""
Agent 11: Investigation Mentor + Evidence Readiness + FIR Draft.

Mentor: next steps derived from actual case gaps.
Readiness: evidence completeness, validation state, unresolved contradictions,
chain of custody check. Never claims legal admissibility.
FIR: structured human-reviewable draft where factual claims link to evidence.
"""

from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.state import (
    FIRDraft,
    InvestigationState,
    MentorRecommendation,
    ReadinessAssessment,
    ReviewStatus,
)

EXPECTED_EVIDENCE_TYPES = {
    "chat_whatsapp": "WhatsApp chat export",
    "chat_telegram": "Telegram chat export",
    "email": "Email export",
    "call_log": "Call Detail Records (CDR)",
    "gps": "GPS / location data",
    "transaction": "Bank / transaction statements",
    "image": "Photographic evidence",
    "video": "Video footage",
    "audio": "Audio recordings",
}


class Agent11MentorFIR(BaseAgent):
    name = "agent_11_mentor_fir"
    description = "Investigation Mentor + Evidence Readiness + FIR Draft"
    prompt_version = "11.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        if not state.validated_evidence:
            raise InsufficientEvidenceError("Cannot mentor a case with no validated evidence.")

        recommendations = self._mentor(state)
        readiness = self._readiness(state)
        fir = self._fir_draft(state)

        result = {
            "recommendations": [r.model_dump() for r in recommendations],
            "readiness": readiness.model_dump(),
            "fir_draft": fir.model_dump(),
        }
        confidence = 0.0
        n = 0
        for r in recommendations:
            confidence += r.estimated_confidence_improvement
            n += 1
        if n:
            confidence /= n
        confidence = round(confidence + readiness.readiness_score / 100 * 0.2, 3)

        return {
            "result": result,
            "state_fields": {
                "mentor_recommendations": recommendations,
                "readiness": readiness,
                "fir_draft": fir,
            },
            "confidence": confidence,
            "evidence_references": [],
            "warnings": [
                "FIR draft is AI-generated and requires mandatory human review before any use.",
            ],
            "evidence_ids": [e.evidence_id for e in state.validated_evidence],
        }

    # --- mentor ---------------------------------------------------------------

    def _mentor(self, state: InvestigationState) -> List[MentorRecommendation]:
        recs: List[MentorRecommendation] = []
        present_types = {v.source_type for v in state.validated_evidence}
        missing = [
            (t, label)
            for t, label in EXPECTED_EVIDENCE_TYPES.items()
            if t not in present_types
        ]
        missing = missing[:5]
        if missing:
            labels = ", ".join(label for _, label in missing)
            recs.append(
                MentorRecommendation(
                    recommendation=f"Collect additional evidence types: {labels}",
                    reason="The current case lacks these source classes, which limits corroboration of findings.",
                    priority="HIGH" if not present_types else "MEDIUM",
                    supporting_evidence=[
                        f"present sources: {', '.join(sorted(present_types)) or 'none'}"
                    ],
                    expected_value="Cross-source corroboration and stronger grounding for conclusions.",
                    estimated_confidence_improvement=0.3,
                )
            )

        if state.contradictions:
            recs.append(
                MentorRecommendation(
                    recommendation=f"Resolve {len(state.contradictions)} flagged contradiction(s) before conclusions",
                    reason="Unresolved contradictions undermine the reliability of derived findings.",
                    priority="HIGH",
                    supporting_evidence=[c.evidence_id for c in state.contradictions if c.evidence_id][:8],
                    expected_value="Cleaner conclusions and defensible statements.",
                    estimated_confidence_improvement=0.25,
                )
            )

        has_relationships = bool(state.relationships)
        if not has_relationships and len(state.entities) >= 2:
            recs.append(
                MentorRecommendation(
                    recommendation="Run relationship analysis after entity expansion",
                    reason="Connections between identified entities are not yet established.",
                    priority="MEDIUM",
                    supporting_evidence=[e.evidence_id for e in state.entities[:5] if e.evidence_id],
                    expected_value="Network view of the case.",
                    estimated_confidence_improvement=0.15,
                )
            )

        pending_review = sum(
            1 for c in state.correlated_entities if c.review_status == ReviewStatus.PENDING_REVIEW
        )
        if pending_review:
            recs.append(
                MentorRecommendation(
                    recommendation=f"Review {pending_review} cross-evidence correlation(s) (possible matches)",
                    reason="Possible matches require human confirmation before they can be used.",
                    priority="MEDIUM",
                    supporting_evidence=[c.supporting_evidence[0] for c in state.correlated_entities[:5] if c.supporting_evidence],
                    expected_value="Confirmed identities and fewer false leads.",
                    estimated_confidence_improvement=0.2,
                )
            )

        if state.risk_score.risk_level == "HIGH":
            recs.append(
                MentorRecommendation(
                    recommendation="Escalate to supervisor review given HIGH risk assessment",
                    reason="High risk flags urgent investigator attention and oversight.",
                    priority="HIGH",
                    supporting_evidence=list(state.risk_score.supporting_evidence[:10]),
                    expected_value="Procedural oversight and faster resource allocation.",
                    estimated_confidence_improvement=0.1,
                )
            )

        if not recs:
            recs.append(
                MentorRecommendation(
                    recommendation="Perform manual verification pass over all derived findings",
                    reason="Pipeline has no critical gaps; remaining work is human verification.",
                    priority="LOW",
                    supporting_evidence=[e.evidence_id for e in state.validated_evidence[:10]],
                    expected_value="Verified, reviewable case file.",
                    estimated_confidence_improvement=0.15,
                )
            )
        return recs

    # --- readiness ------------------------------------------------------------

    def _readiness(self, state: InvestigationState) -> ReadinessAssessment:
        evidence = state.validated_evidence
        total = len(evidence)
        valid = sum(1 for v in evidence if v.validation_status.value == "VALID")
        hashed = sum(1 for v in evidence if v.sha256)
        chain_ok = hashed == total and total > 0 and all(v.uploaded_at for v in evidence)
        validation_ok = valid == total and total > 0

        unresolved = len(state.contradictions)
        present_types = {v.source_type for v in evidence}
        missing = [
            label for t, label in EXPECTED_EVIDENCE_TYPES.items() if t not in present_types
        ][:5]

        score = 0.0
        if total:
            score += 30 * (valid / total)
            score += 20 * (1 if chain_ok else 0.5 if hashed else 0)
            score += 20 * (1 if unresolved == 0 else max(0.0, 1 - unresolved * 0.15))
            score += 15 * min(1.0, len(present_types) / max(1, len(EXPECTED_EVIDENCE_TYPES) - 2))
            score += 15 * (1 if validation_ok else 0.5)
            score = round(min(score, 100), 1)

        notes: List[str] = []
        if not chain_ok:
            notes.append("Chain of custody requirements are not fully satisfied (missing hash or upload metadata).")
        if unresolved:
            notes.append(f"{unresolved} unresolved contradiction(s) remain - resolve before any formal statement.")
        if missing:
            notes.append(f"Missing evidence classes: {', '.join(missing)}.")
        notes.append(
            "Readiness refers to analytical completeness of this tool, NOT legal admissibility."
        )

        return ReadinessAssessment(
            ready_for_review=chain_ok and validation_ok and unresolved == 0 and score >= 70,
            readiness_score=score,
            available_evidence=total,
            missing_evidence=missing,
            unresolved_contradictions=unresolved,
            chain_of_custody_ok=chain_ok,
            validation_ok=validation_ok,
            expert_validation_status="NOT_REVIEWED",
            notes=notes,
        )

    # --- FIR ------------------------------------------------------------------

    def _fir_draft(self, state: InvestigationState) -> FIRDraft:
        facts: List[Dict[str, Any]] = []
        for ev in state.timeline[:15]:
            facts.append(
                {
                    "statement": f"[{ev.timestamp}] {ev.description}",
                    "evidence_ids": ev.evidence_ids,
                    "source_reference": ev.source_reference,
                }
            )
        for con in state.contradictions[:5]:
            facts.append(
                {
                    "statement": f"Flagged conflict: {con.claim_a[:120]} vs {con.claim_b[:120]}",
                    "evidence_ids": con.evidence_a + con.evidence_b,
                    "source_reference": f"contradiction {con.contradiction_id}",
                }
            )
        for factor in state.risk_score.risk_factors[:5]:
            facts.append(
                {
                    "statement": f"Risk signal: {factor.factor} (contributed {factor.score_contribution}/100)",
                    "evidence_ids": factor.evidence_ids,
                    "source_reference": "risk assessment",
                }
            )

        locations = sorted(
            {e.normalized_value for e in state.entities if e.entity_type == "LOCATION"}
        )
        persons = sorted(
            {e.normalized_value for e in state.entities if e.entity_type == "PERSON"}
        )

        occ_time = state.timeline[0].timestamp if state.timeline else "Not established from evidence"
        place = ", ".join(locations[:3]) or "Not established from evidence"

        overview = (
            f"Case {state.case_id} - {state.case_title or 'Untitled case'}. "
            f"Derived from {len(state.validated_evidence)} validated evidence item(s). "
            f"Indicators present: {', '.join(sorted({f.factor for f in state.risk_score.risk_factors})) or 'none recorded'}. "
            "DRAFT ONLY - requires mandatory human review."
        )

        return FIRDraft(
            case_id=state.case_id,
            complainant=state.case_description.split("complainant:")[-1].split("\n")[0].strip()
            if "complainant:" in state.case_description.lower() else "Not specified in case metadata",
            accused=", ".join(persons[:5]) or "Not established from evidence",
            date_of_occurrence=occ_time,
            place_of_occurrence=place,
            overview=overview,
            facts=facts,
            evidence_summary=[f"{e.evidence_id} - {e.file_name} ({e.source_type.value})" for e in state.validated_evidence[:30]],
            legal_notes=[
                "Draft based on AI analysis of processed evidence only.",
                "Fictional-test-language guard: names/numbers/details must be verified against official records.",
                "This draft is not a substitute for a certified law-enforcement FIR.",
            ],
            review_status=ReviewStatus.PENDING_REVIEW,
        )