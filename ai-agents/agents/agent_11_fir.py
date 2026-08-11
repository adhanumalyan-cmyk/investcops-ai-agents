"""
agents/agent_11_fir.py

Agent 11 - FIR (First Information Report) Draft Generation

Input : full state (entities, timeline, contradictions, risk_score,
         insights_summary, evidence_metadata, correlated_entities, etc.)
Output: {"fir_draft": "Full legal document text"}

FIR drafts are ALWAYS flagged for human review before use (legal document
that must be verified by an investigating officer). If the case risk_score
is high, the review note is escalated accordingly.
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


class FIRDraftAgent(BaseAgent):
    """Generates a structured First Information Report (FIR) draft in
    legal format, synthesizing the entire investigation state. This is a
    DRAFT ONLY and always requires human (investigating officer) review
    before filing.
    """

    AGENT_NAME = "Agent 11 - FIR Draft Generation"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_used=model_used)

    # ------------------------------------------------------------------
    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()

        entities: Dict[str, List[Dict[str, Any]]] = state.get("entities", {})
        timeline: List[Dict[str, str]] = state.get("timeline", [])
        contradictions: List[Dict[str, str]] = state.get("contradictions", [])
        risk_score: int = state.get("risk_score", 0)
        insights_summary: str = state.get("insights_summary", "")
        correlated_entities: Dict[str, List[str]] = state.get("correlated_entities", {})
        evidence_metadata: Dict[str, Any] = state.get("evidence_metadata", {})

        has_minimum_data = bool(entities or timeline or insights_summary)

        if not has_minimum_data:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="partial",
                input_evidence=[],
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
                entities=entities,
                timeline=timeline,
                contradictions=contradictions,
                risk_score=risk_score,
                insights_summary=insights_summary,
                correlated_entities=correlated_entities,
                evidence_metadata=evidence_metadata,
            )
            result = self.call_llm(prompt, json_schema=schema)

            fir_draft = (result.get("fir_draft") or "").strip()
            confidence = float(result.get("confidence", 0.65))

            if not fir_draft:
                raise ValueError("LLM returned an empty FIR draft.")

            add_confidence_score(
                state,
                item_id="fir_draft",
                category="risk",  # FIR quality is tied to overall case confidence
                score=confidence,
                reason="Confidence in the completeness/accuracy of the generated FIR draft.",
            )

            # FIR drafts ALWAYS require human review before filing.
            risk_note = (
                "HIGH RISK CASE — urgent officer review required."
                if risk_score >= HIGH_RISK_THRESHOLD
                else "Standard review required before filing."
            )
            flag_for_review(
                state,
                item_id="fir_draft",
                category="fir_draft",
                notes=f"Auto-generated FIR draft. Risk score: {risk_score}/100. {risk_note}",
            )

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="success",
                input_evidence=list(evidence_metadata.keys()),
                output_summary=f"Generated FIR draft ({len(fir_draft)} chars). Risk score: {risk_score}.",
            )

            return {"fir_draft": fir_draft}

        except Exception as e:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="failed",
                input_evidence=list(evidence_metadata.keys()),
                output_summary="FIR draft generation failed.",
                error_message=str(e),
            )
            return {"fir_draft": ""}

    # ------------------------------------------------------------------
    @staticmethod
    def _build_prompt(
        entities: Dict[str, List[Dict[str, Any]]],
        timeline: List[Dict[str, str]],
        contradictions: List[Dict[str, str]],
        risk_score: int,
        insights_summary: str,
        correlated_entities: Dict[str, List[str]],
        evidence_metadata: Dict[str, Any],
    ) -> str:
        entity_summary = "\n".join(
            f"- [{etype}] {item.get('name')}"
            for etype, items in (entities or {}).items()
            for item in items
        ) or "No entities recorded."

        timeline_summary = "\n".join(
            f"- {ev.get('timestamp', 'unknown time')}: {ev.get('event', '')}"
            for ev in timeline
        ) or "No timeline recorded."

        contradiction_summary = "\n".join(
            f"- [{c.get('severity', 'medium')}] {c.get('explanation', '')}"
            for c in contradictions
        ) or "No contradictions recorded."

        correlation_summary = "\n".join(
            f"- {name}: appears in {', '.join(docs)}"
            for name, docs in (correlated_entities or {}).items()
        ) or "No cross-evidence correlation recorded."

        evidence_summary = "\n".join(
            f"- {eid}: {meta.get('file_name', 'unknown')} ({meta.get('file_type', 'unknown')}, source: {meta.get('source', 'unknown')})"
            for eid, meta in (evidence_metadata or {}).items()
        ) or "No evidence metadata recorded."

        return f"""You are a legal drafting assistant for INVESTCOPS AI, helping an
investigating officer prepare a DRAFT First Information Report (FIR) based
on digital investigation findings. This is a DRAFT ONLY, to be reviewed,
corrected, and filed by a qualified officer. Use formal, neutral,
factual language appropriate for an Indian FIR format. Do NOT state
conclusions of guilt — present facts, entities, timeline, and flagged
concerns objectively.

Case risk score: {risk_score}/100
Investigation summary: {insights_summary or 'Not yet available.'}

Entities involved:
{entity_summary}

Cross-evidence correlation:
{correlation_summary}

Timeline of events:
{timeline_summary}

Contradictions / inconsistencies found:
{contradiction_summary}

Evidence reviewed:
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
}}"""