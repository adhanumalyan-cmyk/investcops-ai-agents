"""
Agent 9: Explainability & Insights.

Explains every major derived result: what was found, why it matters, which
evidence/entities contributed, confidence, uncertainty, limitations. The UI
renders these explanations next to their findings.
"""

from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.state import FindingExplanation, InsightsSummary, InvestigationState


class Agent9Insights(BaseAgent):
    name = "agent_9_insights"
    description = "Explainability & Insights"
    prompt_version = "9.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        if not state.validated_evidence and not state.entities:
            raise InsufficientEvidenceError("No case content yet; run earlier agents first.")

        explanations: List[FindingExplanation] = []
        evidence_contributions: List[str] = []

        # 1) Risk explanation.
        if state.risk_score.risk_factors:
            top = state.risk_score.risk_factors[0]
            explanations.append(
                FindingExplanation(
                    what=f"Assessment evaluates at {state.risk_score.risk_score:.0f}/100 ({state.risk_score.risk_level})",
                    why_it_matters="Priority guide: higher scores indicate stronger signals and more urgent investigator attention.",
                    evidence_used=top.evidence_ids,
                    entity_contribution=[],
                    confidence=state.risk_score.confidence,
                    uncertainty="Score is rule-based; severity labels require human judgment.",
                    limitations=[f"Top contributing factor: {top.factor} (contributed {top.score_contribution})."],
                )
            )
            for eid in top.evidence_ids:
                evidence_contributions.append(eid)

        # 2) Contradiction explanations.
        for c in state.contradictions[:10]:
            explanations.append(
                FindingExplanation(
                    what=f"Contradiction: '{c.claim_a[:80]}' vs '{c.claim_b[:80]}'",
                    why_it_matters="Conflicting information is a lead: verify statements, obtain corroboration.",
                    evidence_used=c.evidence_a + c.evidence_b,
                    entity_contribution=[],
                    confidence=c.confidence,
                    uncertainty=c.explanation,
                    limitations=[f"Severity classification: {c.severity}. Not proof of guilt."],
                )
            )
            evidence_contributions.extend(c.evidence_a + c.evidence_b)

        # 3) Correlation explanations.
        for m in state.correlated_entities[:10]:
            explanations.append(
                FindingExplanation(
                    what=f"Cross-evidence link: {m.entity_a_value} ({m.match_type})",
                    why_it_matters="Same identifier surfacing in multiple sources can tie activities together; verify before relying on it.",
                    evidence_used=m.supporting_evidence,
                    entity_contribution=[m.entity_a_value, m.entity_b_value],
                    confidence=m.match_confidence,
                    uncertainty=m.explanation,
                    limitations=["Possible match only - identity must be confirmed by an investigator."],
                )
            )
            evidence_contributions.extend(m.supporting_evidence)

        # 4) Entity contribution summary.
        summary_notes = [
            f"{len(state.validated_evidence)} evidence item(s) validated out of {len(state.evidence)} submitted",
            f"{len(state.entities)} entities extracted across {len({e.normalized_value for e in state.entities})} unique identifiers",
            f"{len(state.relationships)} relationships, {len(state.timeline)} timeline events, {len(state.contradictions)} contradiction(s) flagged",
            f"Risk assessment: {state.risk_score.risk_score:.0f}/100 ({state.risk_score.risk_level})",
        ]

        confidence_vals = []
        result_records = []
        for agent_name in (
            "agent_1_ingestion",
            "agent_2_evidence_analysis",
            "agent_3_entities",
            "agent_4_relationships",
            "agent_5_correlate",
            "agent_6_timeline",
            "agent_7_contradict",
            "agent_8_risk",
        ):
            env = state.agent_results.get(agent_name)
            if env:
                result_records.append(env)
                confidence_vals.append(float(env.get("confidence", 0.0)))
        overall = round(
            sum(confidence_vals) / len(confidence_vals), 3
        ) if confidence_vals else 0.0

        insights = InsightsSummary(
            summary="; ".join(summary_notes),
            finding_explanations=explanations,
            evidence_contributions=list(dict.fromkeys(evidence_contributions))[:50],
            confidence=overall,
            limitations=[
                "Explanations are generated deterministically from derived results.",
                "Every finding requires human verification before any investigative action.",
            ],
        )
        return {
            "result": {
                "summary": insights.summary,
                "finding_explanations": [e.model_dump() for e in insights.finding_explanations],
                "evidence_contributions": insights.evidence_contributions,
                "confidence": insights.confidence,
                "limitations": insights.limitations,
            },
            "state_fields": {"insights_summary": insights, "explanations": explanations},
            "confidence": overall,
            "evidence_references": [
                self._provenance(eid, excerpt_or_locator="contributed to insights", confidence=overall)
                for eid in list(dict.fromkeys(evidence_contributions))[:50]
            ],
            "warnings": [],
            "evidence_ids": list(dict.fromkeys(evidence_contributions))[:50],
        }