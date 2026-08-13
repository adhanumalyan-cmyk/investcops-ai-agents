"""
Agent 8: Risk Assessment.

Hybrid deterministic + AI design: the score is computed by weighted,
reproducible rules over actual case signals (indicators, contradictions,
financial content, harassment). The LLM may only add interpretation text;
it can never insert an arbitrary score.
"""

from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.extract import MONEY_RE, indicator_hits
from core.state import InvestigationState, RiskAssessment, RiskFactor

# Weight table: category -> (weight, max_contribution)
_WEIGHTS = {
    "threat": 25.0,
    "harassment": 20.0,
    "financial_fraud": 22.0,
    "coercion": 20.0,
    "identity_theft": 18.0,
    "drugs": 15.0,
}


class Agent8Risk(BaseAgent):
    name = "agent_8_risk"
    description = "Risk Assessment"
    prompt_version = "8.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        if not state.validated_evidence:
            raise InsufficientEvidenceError("Cannot assess risk without validated evidence.")

        factors: List[RiskFactor] = []
        trace: List[str] = []
        evidence_ids: List[str] = []

        # 1) Indicator categories found in evidence text.
        cat_scores: Dict[str, float] = {}
        docs = {d["evidence_id"]: d for d in state.cleaned_documents}
        for ev in state.validated_evidence:
            text = (docs.get(ev.evidence_id, {}) or {}).get("text", "") or ""
            for cat, kw in indicator_hits(text):
                cat_scores[cat] = cat_scores.get(cat, 0.0) + _WEIGHTS.get(cat, 5.0) * 0.15
                evidence_ids.append(ev.evidence_id)
        for cat, score in sorted(cat_scores.items()):
            capped = min(score, _WEIGHTS.get(cat, 20.0))
            factors.append(
                RiskFactor(
                    factor=f"indicator:{cat}",
                    weight=_WEIGHTS.get(cat, 10.0),
                    score_contribution=round(capped, 2),
                    evidence_ids=list(dict.fromkeys(evidence_ids)),
                    basis=f"Keyword signals for '{cat}' found in evidence text.",
                )
            )
            trace.append(f"+{capped:.1f} from {cat} indicators")

        # 2) Verified/derived contradictions add risk (they are unresolved leads).
        if state.contradictions:
            high = sum(1 for c in state.contradictions if c.severity == "HIGH")
            medium = sum(1 for c in state.contradictions if c.severity == "MEDIUM")
            contribution = min(high * 8.0 + medium * 4.0, 25.0)
            factors.append(
                RiskFactor(
                    factor="unresolved_contradictions",
                    weight=25.0,
                    score_contribution=round(contribution, 2),
                    evidence_ids=[c.evidence_id for c in state.contradictions if c.evidence_id],
                    basis=f"{high} HIGH + {medium} MEDIUM severity contradictions unreviewed.",
                )
            )
            trace.append(f"+{contribution:.1f} from unresolved contradictions")

        # 3) Financial magnitude content raises financial-fraud signal strength.
        money_hits = 0
        for ev in state.validated_evidence:
            text = (docs.get(ev.evidence_id, {}) or {}).get("text", "") or ""
            money_hits += len(MONEY_RE.findall(text))
        if money_hits:
            contribution = min(money_hits * 1.5, 10.0)
            factors.append(
                RiskFactor(
                    factor="financial_transfer_content",
                    weight=10.0,
                    score_contribution=round(contribution, 2),
                    evidence_ids=list(dict.fromkeys(evidence_ids)),
                    basis=f"{money_hits} monetary references in evidence.",
                )
            )
            trace.append(f"+{contribution:.1f} from financial content")

        # 4) Evidence completeness reduces uncertainty (never raises the score).
        valid_ratio = (
            sum(1 for v in state.validated_evidence if v.validation_status.value == "VALID")
            / len(state.validated_evidence)
            if state.validated_evidence
            else 0.0
        )
        trace.append(f"validation completeness={valid_ratio:.0%} (uncertainty factor)")

        total = round(min(sum(f.score_contribution for f in factors), 100.0), 1)
        level = "LOW" if total < 34 else ("MEDIUM" if total < 67 else "HIGH")
        confidence = round(0.5 + 0.4 * valid_ratio + 0.1 * bool(state.contradictions), 3)

        assessment = RiskAssessment(
            risk_score=total,
            risk_level=level,
            risk_factors=factors,
            supporting_evidence=list(dict.fromkeys(evidence_ids)),
            confidence=confidence,
            calculation_trace=trace,
        )
        return {
            "result": assessment.model_dump(),
            "state_fields": {"risk_score": assessment},
            "confidence": confidence,
            "evidence_references": [
                self._provenance(
                    eid,
                    excerpt_or_locator=trace[0] if trace else "risk rule",
                    confidence=confidence,
                )
                for eid in list(dict.fromkeys(evidence_ids))[:50]
            ],
            "warnings": (
                []
                if total or factors
                else ["No risk signals detected; score is 0. This is a low-signal outcome, not an error."]
            ),
            "evidence_ids": list(dict.fromkeys(evidence_ids)),
        }