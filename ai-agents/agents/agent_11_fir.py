"""
agents/agent_11_fir.py

Agent 11 - FIR (First Information Report) Draft Generation

Input:
    Full state: entities, relationships, correlations, timeline,
    contradictions, risk_assessment, insights_summary, evidence_metadata.

Output:
    {"fir_draft": "<full FIR draft text>"}

FIR drafts are ALWAYS flagged for human review before use (legal
document that must be verified by an investigating officer). If the
case risk_assessment level is HIGH/CRITICAL, the review note is
escalated accordingly.
"""

from datetime import datetime
from typing import Any, Dict

from core.state import InvestigationState, log_agent_execution, flag_for_review
from core.base_agent import BaseAgent

HIGH_RISK_LEVELS = ("HIGH", "CRITICAL")


class FIRDraftAgent(BaseAgent):

    AGENT_NAME = "Agent 11 - FIR Draft Generation"

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
        insights_summary = state.get("insights_summary", "")
        evidence_metadata = state.get("evidence_metadata", {})

        has_minimum_data = bool(entities or timeline or insights_summary)
        if not has_minimum_data:
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="partial", input_evidence=[],
                output_summary="Insufficient investigation data to draft an FIR.",
            )
            return {"fir_draft": ""}

        try:
            schema = {
                "type": "object",
                "properties": {
                    "fir_draft": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["fir_draft"],
            }
            prompt = self._build_prompt(
                entities, relationships, correlations, timeline,
                contradictions, risk_assessment, insights_summary, evidence_metadata,
            )

            print("\n========== AGENT 11 PROMPT ==========")
            print(prompt)
            print("========== END AGENT 11 DEBUG ==========\n")

            result = self.call_llm(prompt, json_schema=schema)
            fir_draft = str(result.get("fir_draft", "")).strip()

            if not fir_draft:
                raise ValueError("LLM returned an empty FIR draft.")

            risk_score = risk_assessment.get("score", 0)
            risk_level = risk_assessment.get("level", "LOW")
            risk_note = (
                "HIGH/CRITICAL RISK CASE — urgent officer review required."
                if risk_level in HIGH_RISK_LEVELS
                else "Standard review required before filing."
            )

            # FIR drafts ALWAYS require human review before filing —
            # this is a legal document, never auto-filed.
            flag_for_review(
                state, item_id="fir_draft", category="fir_draft",
                notes=f"Auto-generated FIR draft. Risk: {risk_score}/100 ({risk_level}). {risk_note}",
            )

            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="success",
                input_evidence=list(evidence_metadata.keys()),
                output_summary=f"Generated FIR draft ({len(fir_draft)} chars). Risk: {risk_score} ({risk_level}).",
            )

            return {"fir_draft": fir_draft}

        except Exception as e:
            print(f"[Agent 11] Failed: {e}")
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="failed",
                input_evidence=list(evidence_metadata.keys()),
                output_summary="FIR draft generation failed.", error_message=str(e),
            )
            return {"fir_draft": ""}

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(entities, relationships, correlations, timeline, contradictions,
                       risk_assessment, insights_summary, evidence_metadata) -> str:
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

        evidence_summary = "\n".join(
            f"- {eid}: {meta.get('file_name', 'unknown')} "
            f"({meta.get('file_type', 'unknown')}, source: {meta.get('source', 'unknown')})"
            for eid, meta in (evidence_metadata or {}).items()
        ) or "No evidence metadata recorded."

        risk_line = (
            f"Risk score: {risk_assessment.get('score', 'N/A')}/100 "
            f"({risk_assessment.get('level', 'UNKNOWN')})"
        )

        return f"""
You are a legal drafting assistant for INVESTCOPS AI, helping an
investigating officer prepare a DRAFT First Information Report (FIR).
This is a DRAFT ONLY, to be reviewed, corrected, and filed by a
qualified officer. Use formal, neutral, factual language appropriate
for an Indian FIR format. Do NOT state conclusions of guilt — present
facts, entities, timeline, and flagged concerns objectively.

{risk_line}
Investigation summary: {insights_summary or 'Not yet available.'}

ENTITIES INVOLVED:
{entity_summary}

RELATIONSHIPS:
{relationship_summary}

CROSS-EVIDENCE CORRELATIONS:
{correlation_summary}

TIMELINE OF EVENTS:
{timeline_summary}

CONTRADICTIONS / INCONSISTENCIES:
{contradiction_summary}

EVIDENCE REVIEWED:
{evidence_summary}

Draft the FIR with these sections:
1. Header (Date, Police Station placeholder, District placeholder)
2. Complainant/Informant details (placeholder if unknown)
3. Details of the Offence (factual narrative built from the above)
4. Persons Involved (from entities)
5. Sequence of Events (from timeline)
6. Points Requiring Further Investigation (from contradictions)
7. Evidence Annexed (from evidence list)
8. Officer's Note (state this is an AI-assisted DRAFT requiring verification)

Return ONLY valid JSON:

{{
    "fir_draft": "<the full FIR draft text, well-formatted with section headers>",
    "confidence": 0.7
}}
"""