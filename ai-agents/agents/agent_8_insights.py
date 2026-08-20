"""
agents/agent_8_insights.py

Agent 8 - Investigation Insights Summary

NOTE: originally assigned to teammate A — confirm with them before
merging this in, in case they've already built their own version.

Input:
    Full state: entities, relationships, correlations, timeline,
    contradictions, risk_assessment.

Output:
    {"insights_summary": "<neutral, factual case summary text>"}

Purpose:
    Synthesize everything the pipeline has found so far into a short,
    human-readable summary an investigating officer can read in under
    a minute to understand where the case currently stands.
"""

from datetime import datetime
from typing import Any, Dict

from core.state import InvestigationState, log_agent_execution, flag_for_review
from core.base_agent import BaseAgent


class InsightsSummaryAgent(BaseAgent):

    AGENT_NAME = "Agent 8 - Investigation Insights Summary"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_name=model_used)

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()

        entities = state.get("entities", {})
        relationships = state.get("relationships", [])
        correlations = state.get("correlations", [])
        timeline = state.get("timeline", [])
        contradictions = state.get("contradictions", [])
        risk_assessment = state.get("risk_assessment") or {}

        has_data = bool(entities or timeline or contradictions)
        if not has_data:
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="partial", input_evidence=[],
                output_summary="Insufficient data to generate insights summary.",
            )
            return {"insights_summary": ""}

        try:
            schema = {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            }
            prompt = self._build_prompt(
                entities, relationships, correlations, timeline, contradictions, risk_assessment
            )

            print("\n========== AGENT 8 PROMPT ==========")
            print(prompt)
            print("========== END AGENT 8 DEBUG ==========\n")

            result = self.call_llm(prompt, json_schema=schema)
            summary = str(result.get("summary", "")).strip()

            if not summary:
                raise ValueError("LLM returned an empty summary.")

            level = risk_assessment.get("level", "LOW")
            if level in ("HIGH", "CRITICAL"):
                flag_for_review(
                    state, item_id="insights_summary", category="major_finding",
                    notes=f"Case summary generated at {level} risk level — recommend priority review.",
                )

            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="success",
                input_evidence=[c.get("contradiction_id", "") for c in contradictions],
                output_summary=f"Generated {len(summary)}-character insights summary.",
            )

            return {"insights_summary": summary}

        except Exception as e:
            print(f"[Agent 8] Failed: {e}")
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="failed", input_evidence=[],
                output_summary="Insights summary generation failed.", error_message=str(e),
            )
            return {"insights_summary": ""}

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(entities, relationships, correlations, timeline, contradictions, risk_assessment) -> str:
        entity_summary = "\n".join(
            f"- [{etype}] {item.get('name')}"
            for etype, items in (entities or {}).items() for item in items
        ) or "No entities recorded."

        relationship_summary = "\n".join(
            f"- {r.get('subject')} {r.get('relationship')} {r.get('object')}" for r in relationships
        ) or "No relationships recorded."

        correlation_summary = "\n".join(
            f"- {c.get('correlation_type')}: {c.get('explanation', '')}" for c in correlations
        ) or "No cross-evidence correlations recorded."

        timeline_summary = "\n".join(
            f"- {ev.get('timestamp') or 'unknown time'}: {ev.get('description', '')}" for ev in timeline
        ) or "No timeline recorded."

        contradiction_summary = "\n".join(
            f"- [{c.get('severity', 'medium')}] {c.get('description', '')}" for c in contradictions
        ) or "No contradictions recorded."

        risk_line = (
            f"Risk score: {risk_assessment.get('score', 'N/A')}/100 "
            f"({risk_assessment.get('level', 'UNKNOWN')})"
        )

        return f"""
You are a forensic investigation-summary assistant for INVESTCOPS AI.

Write a clear, neutral, factual summary of the investigation so far,
for an investigating officer to quickly understand the case state.
Base it ONLY on the information below — do not speculate about guilt,
motive, or outcome.

ENTITIES:
{entity_summary}

RELATIONSHIPS:
{relationship_summary}

CROSS-EVIDENCE CORRELATIONS:
{correlation_summary}

TIMELINE:
{timeline_summary}

CONTRADICTIONS:
{contradiction_summary}

{risk_line}

Write 1-3 short paragraphs covering: who is involved, what the
evidence shows happened (in chronological order), what connects the
evidence together, and what open questions or contradictions need
investigator attention. Do NOT state conclusions of guilt.

Return ONLY valid JSON:

{{
    "summary": "<the summary text>"
}}
"""