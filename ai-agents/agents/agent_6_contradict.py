"""
agents/agent_6_contradict.py

Agent 6 - Contradiction Detection

Input : state["entities"], state["timeline"]
Output: {"contradictions": [{"statement_a": "", "statement_b": "", "explanation": ""}]}

Also, for every contradiction found:
  - add_confidence_score(category="contradiction")
  - add_evidence_reference(...) for BOTH statements involved
  - flag_for_review(category="contradiction")  (contradictions always need human sign-off)
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
    add_evidence_reference,
    flag_for_review,
)
from core.base_agent import BaseAgent


class ContradictionDetectionAgent(BaseAgent):
    """Cross-checks entity mentions and timeline events to surface
    conflicting statements/evidence that investigators need to resolve.
    """

    AGENT_NAME = "Agent 6 - Contradiction Detection"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_used=model_used)

    # ------------------------------------------------------------------
    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()
        entities: Dict[str, List[Dict[str, Any]]] = state.get("entities", {})
        timeline: List[Dict[str, str]] = state.get("timeline", [])

        if not entities and not timeline:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary="No entities or timeline found in state; skipping contradiction detection.",
            )
            return {"contradictions": []}

        try:
            schema = {
                "type": "object",
                "properties": {
                    "contradictions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement_a": {"type": "string"},
                                "statement_b": {"type": "string"},
                                "explanation": {"type": "string"},
                                "evidence_a_id": {"type": "string"},
                                "evidence_b_id": {"type": "string"},
                                "timestamp_a": {"type": "string"},
                                "timestamp_b": {"type": "string"},
                                "confidence": {"type": "number"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high"],
                                },
                            },
                            "required": ["statement_a", "statement_b", "explanation"],
                        },
                    }
                },
                "required": ["contradictions"],
            }
            prompt = self._build_prompt(entities, timeline)
            result = self.call_llm(prompt, json_schema=schema)
            raw_contradictions = result.get("contradictions", []) or []

            contradictions: List[Dict[str, str]] = []

            for idx, c in enumerate(raw_contradictions):
                statement_a = (c.get("statement_a") or "").strip()
                statement_b = (c.get("statement_b") or "").strip()
                explanation = (c.get("explanation") or "").strip()
                if not statement_a or not statement_b:
                    continue

                contradiction_id = f"CONTRA{idx + 1:03d}"
                severity = c.get("severity", "medium")
                confidence = float(c.get("confidence", 0.7))

                contradictions.append(
                    {
                        "contradiction_id": contradiction_id,
                        "statement_a": statement_a,
                        "statement_b": statement_b,
                        "explanation": explanation,
                        "severity": severity,
                    }
                )

                add_confidence_score(
                    state,
                    item_id=contradiction_id,
                    category="contradiction",
                    score=confidence,
                    reason=explanation,
                )

                add_evidence_reference(
                    state,
                    finding=statement_a,
                    evidence_id=c.get("evidence_a_id", "UNKNOWN"),
                    source="cross-evidence analysis",
                    timestamp=c.get("timestamp_a"),
                    excerpt=statement_a,
                )
                add_evidence_reference(
                    state,
                    finding=statement_b,
                    evidence_id=c.get("evidence_b_id", "UNKNOWN"),
                    source="cross-evidence analysis",
                    timestamp=c.get("timestamp_b"),
                    excerpt=statement_b,
                )

                flag_for_review(
                    state,
                    item_id=contradiction_id,
                    category="contradiction",
                    notes=f"Severity: {severity}. {explanation}",
                )

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="success",
                input_evidence=[e.get("timeline_id", "") for e in timeline] or ["entities_only"],
                output_summary=f"Detected {len(contradictions)} contradiction(s).",
            )

            return {"contradictions": contradictions}

        except Exception as e:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="failed",
                input_evidence=[],
                output_summary="Contradiction detection failed.",
                error_message=str(e),
            )
            return {"contradictions": []}

    # ------------------------------------------------------------------
    @staticmethod
    def _build_prompt(entities: Dict[str, List[Dict[str, Any]]], timeline: List[Dict[str, str]]) -> str:
        entity_summary = "\n".join(
            f"- [{etype}] {item.get('name')} (mentions: {', '.join(item.get('mentions', [])) or 'unknown'})"
            for etype, items in (entities or {}).items()
            for item in items
        ) or "No entities available."

        timeline_summary = "\n".join(
            f"- {ev.get('timestamp', 'unknown time')}: {ev.get('event', '')} "
            f"(source: {ev.get('evidence_id', 'unknown')})"
            for ev in timeline
        ) or "No timeline available."

        return f"""You are a forensic contradiction-detection assistant for INVESTCOPS AI.

Analyze the entities and timeline of events below. Identify any statements,
claims, locations, or timestamps that CONTRADICT one another (e.g. a person
claimed to be in two places at the same time, conflicting witness accounts,
mismatched timestamps for the same event).

Only report genuine contradictions, not just differences in detail level.
For each contradiction, cite which evidence each statement came from if
possible, and rate your confidence (0.0-1.0) and severity (low/medium/high).

Entities:
{entity_summary}

Timeline:
{timeline_summary}

Return ONLY valid JSON:
{{
  "contradictions": [
    {{
      "statement_a": "<statement 1>",
      "statement_b": "<statement 2>",
      "explanation": "<why these conflict>",
      "evidence_a_id": "<evidence id for statement 1, if known>",
      "evidence_b_id": "<evidence id for statement 2, if known>",
      "timestamp_a": "<timestamp, if known>",
      "timestamp_b": "<timestamp, if known>",
      "confidence": 0.8,
      "severity": "high"
    }}
  ]
}}
If none are found, return {{"contradictions": []}}."""