"""
agents/agent_10_mentor.py

Agent 10 - Investigation Mentor

NOTE: originally assigned to teammate B — confirm with them before
merging this in, in case they've already built their own version.

Input:
    Full state: entities, contradictions, timeline, risk_assessment,
    insights_summary.

Output:
    {"mentor_recommendations": ["<concrete next step>", ...]}

Purpose:
    Suggest concrete NEXT STEPS for the investigator based on gaps,
    contradictions, and risk signals currently in the case —
    "what should I look into next?"
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import InvestigationState, log_agent_execution
from core.base_agent import BaseAgent


class MentorAgent(BaseAgent):

    AGENT_NAME = "Agent 10 - Investigation Mentor"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_name=model_used)

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()

        entities = state.get("entities", {})
        contradictions = state.get("contradictions", [])
        timeline = state.get("timeline", [])
        risk_assessment = state.get("risk_assessment") or {}
        insights_summary = state.get("insights_summary", "")

        has_data = bool(entities or contradictions or timeline)
        if not has_data:
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="partial", input_evidence=[],
                output_summary="Insufficient data to generate recommendations.",
            )
            return {"mentor_recommendations": []}

        try:
            schema = {
                "type": "object",
                "properties": {
                    "recommendations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["recommendations"],
            }
            prompt = self._build_prompt(entities, contradictions, timeline, risk_assessment, insights_summary)

            print("\n========== AGENT 10 PROMPT ==========")
            print(prompt)
            print("========== END AGENT 10 DEBUG ==========\n")

            result = self.call_llm(prompt, json_schema=schema)
            recommendations = [
                str(r).strip() for r in (result.get("recommendations", []) or []) if str(r).strip()
            ]

            if not recommendations:
                raise ValueError("LLM returned no recommendations.")

            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="success",
                input_evidence=[c.get("contradiction_id", "") for c in contradictions],
                output_summary=f"Generated {len(recommendations)} recommendation(s).",
            )

            return {"mentor_recommendations": recommendations}

        except Exception as e:
            print(f"[Agent 10] Failed: {e}")
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="failed", input_evidence=[],
                output_summary="Mentor recommendation generation failed.", error_message=str(e),
            )
            return {"mentor_recommendations": []}

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(entities, contradictions, timeline, risk_assessment, insights_summary) -> str:
        entity_summary = "\n".join(
            f"- [{etype}] {item.get('name')}"
            for etype, items in (entities or {}).items() for item in items
        ) or "No entities recorded."

        contradiction_summary = "\n".join(
            f"- [{c.get('severity', 'medium')}] {c.get('description', '')}" for c in contradictions
        ) or "No contradictions recorded."

        timeline_summary = f"{len(timeline)} timeline event(s) recorded."

        risk_line = (
            f"Risk score: {risk_assessment.get('score', 'N/A')}/100 "
            f"({risk_assessment.get('level', 'UNKNOWN')})"
        )

        return f"""
You are an experienced investigation mentor for INVESTCOPS AI,
advising a (possibly junior) investigator on WHAT TO DO NEXT based on
the current state of the case. You are not deciding guilt — you are
suggesting concrete, actionable next investigative steps.

CASE SUMMARY:
{insights_summary or 'Not yet available.'}

ENTITIES:
{entity_summary}

CONTRADICTIONS:
{contradiction_summary}

{timeline_summary}
{risk_line}

Suggest 3-7 concrete next steps. Examples of good recommendations:
- "Obtain a court order for full call detail records of [device] for the period around [date]"
- "Verify [Person]'s alibi for [time] given the location contradiction in EVD003 vs EVD007"
- "Cross-check [Location] against CCTV footage requests, if available"
- "Interview [Person] regarding their relationship to [Person/Org]"

Each recommendation should be one clear, actionable sentence, grounded
in something specific from the case data above (not generic advice).
Do not state conclusions of guilt or make legal judgments.

Return ONLY valid JSON:

{{
    "recommendations": [
        "Obtain call detail records for device XXXX around 12 Aug 2024.",
        "Interview Rahul regarding the Chennai/Coimbatore location contradiction."
    ]
}}
"""