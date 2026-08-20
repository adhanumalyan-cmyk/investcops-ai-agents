"""
agents/agent_7_risk.py

Agent 7 - Risk Assessment

Input:
    state["contradictions"]
    state["entities"]
    state["timeline"]
    state["correlations"]

Output:
    {
        "risk_assessment": {
            "score": 78.0,
            "level": "HIGH",
            "factors": ["3 high-severity contradictions", "Weapon mentioned in EVD004"],
            "supporting_evidence_ids": ["EVD001", "EVD004"],
            "explanation": "..."
        }
    }
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
    flag_for_review,
)
from core.base_agent import BaseAgent

HIGH_RISK_THRESHOLD = 70
CRITICAL_RISK_THRESHOLD = 90


def _level_from_score(score: float) -> str:
    if score >= CRITICAL_RISK_THRESHOLD:
        return "CRITICAL"
    if score >= HIGH_RISK_THRESHOLD:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


class RiskAssessmentAgent(BaseAgent):

    AGENT_NAME = "Agent 7 - Risk Assessment"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_name=model_used)

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()

        contradictions: List[Dict[str, Any]] = state.get("contradictions", [])
        entities: Dict[str, List[Dict[str, Any]]] = state.get("entities", {})
        correlations: List[Dict[str, Any]] = state.get("correlations", [])
        timeline: List[Dict[str, Any]] = state.get("timeline", [])

        if not contradictions and not entities:
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="partial", input_evidence=[],
                output_summary="Insufficient data; defaulting risk score to 0.",
            )
            default_assessment = {
                "score": 0.0,
                "level": "LOW",
                "factors": ["Insufficient evidence to assess risk"],
                "supporting_evidence_ids": [],
                "explanation": "Not enough data was available for analysis.",
            }
            add_confidence_score(
                state, item_id="risk_assessment", category="risk",
                score=0.2, reason="Insufficient data.",
            )
            return {"risk_assessment": default_assessment}

        try:
            schema = {
                "type": "object",
                "properties": {
                    "score": {"type": "number"},
                    "factors": {"type": "array", "items": {"type": "string"}},
                    "supporting_evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "explanation": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["score", "factors", "explanation"],
            }

            prompt = self._build_prompt(contradictions, entities, correlations, timeline)

            print("\n========== AGENT 7 PROMPT ==========")
            print(prompt)
            print("========== END AGENT 7 DEBUG ==========\n")

            result = self.call_llm(prompt, json_schema=schema)

            try:
                score = float(result.get("score", 0))
            except (TypeError, ValueError):
                score = 0.0
            score = max(0.0, min(100.0, score))

            factors = result.get("factors", []) or []
            explanation = str(result.get("explanation", "")).strip()

            known_evidence_ids = set(state.get("evidence_metadata", {}).keys())
            supporting_raw = result.get("supporting_evidence_ids", []) or []
            supporting_evidence_ids = [eid for eid in supporting_raw if eid in known_evidence_ids]

            if not supporting_evidence_ids:
                # Fall back to evidence cited by high-severity contradictions,
                # so the score always has *some* traceable backing when possible.
                for c in contradictions:
                    if c.get("severity") == "high":
                        supporting_evidence_ids.extend(c.get("evidence_ids", []))
                supporting_evidence_ids = sorted(set(supporting_evidence_ids))

            try:
                confidence = float(result.get("confidence", 0.7))
            except (TypeError, ValueError):
                confidence = 0.7
            confidence = max(0.0, min(1.0, confidence))

            level = _level_from_score(score)

            risk_assessment = {
                "score": score,
                "level": level,
                "factors": [str(f) for f in factors],
                "supporting_evidence_ids": supporting_evidence_ids,
                "explanation": explanation,
            }

            add_confidence_score(
                state, item_id="risk_assessment", category="risk",
                score=confidence, reason=explanation,
            )

            if score >= HIGH_RISK_THRESHOLD:
                flag_for_review(
                    state, item_id="risk_assessment", category="risk_score",
                    notes=(
                        f"{level} risk ({score}/100). "
                        f"Factors: {', '.join(risk_assessment['factors']) if risk_assessment['factors'] else 'see explanation'}. "
                        f"{explanation}"
                    ),
                )

            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="success",
                input_evidence=[c.get("contradiction_id", "") for c in contradictions],
                output_summary=f"Computed risk score {score}/100 ({level}). {explanation}",
            )

            return {"risk_assessment": risk_assessment}

        except Exception as e:
            print(f"[Agent 7] Failed: {e}")
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="failed", input_evidence=[],
                output_summary="Risk assessment failed.", error_message=str(e),
            )
            fallback = {
                "score": 0.0,
                "level": "LOW",
                "factors": [],
                "supporting_evidence_ids": [],
                "explanation": f"Risk assessment failed: {e}",
            }
            return {"risk_assessment": fallback}

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(contradictions, entities, correlations, timeline) -> str:
        contradiction_summary = "\n".join(
            f"- [{c.get('severity', 'medium')}] {c.get('description', '')}" for c in contradictions
        ) or "No contradictions found."

        entity_summary = "\n".join(
            f"- [{etype}] {item.get('name')}"
            for etype, items in (entities or {}).items() for item in items
        ) or "No entities available."

        correlation_summary = "\n".join(
            f"- {c.get('correlation_type')}: {c.get('explanation', '')}" for c in correlations
        ) or "No cross-evidence correlations found."

        return f"""
You are a forensic risk-assessment assistant for INVESTCOPS AI.

Based on the contradictions, entities, and cross-evidence correlations
below, compute an overall CASE RISK SCORE from 0 (no concern) to 100
(extremely high risk, needs urgent officer attention).

Consider: number and severity of contradictions, presence of
weapons/devices tied to harm, repeat/known-offender indicators,
high-risk locations, urgency signals, strength of cross-evidence
correlation, and the volume of timeline activity ({len(timeline)} events recorded).

CONTRADICTIONS:
{contradiction_summary}

ENTITIES:
{entity_summary}

CORRELATIONS:
{correlation_summary}

IMPORTANT RULES:
1. Base the score ONLY on what's shown above — do not assume facts
   not present.
2. Only include an evidence_id in supporting_evidence_ids if you're
   confident it's correct.
3. Return ONLY valid JSON. No Markdown, no text outside JSON.

Return ONLY valid JSON:

{{
    "score": 75,
    "factors": ["3 high-severity contradictions", "Weapon mentioned in EVD004"],
    "supporting_evidence_ids": ["EVD001", "EVD004"],
    "explanation": "Short explanation of why this score was chosen.",
    "confidence": 0.85
}}
"""