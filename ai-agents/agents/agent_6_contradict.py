"""
agents/agent_6_contradict.py

Agent 6 - Contradiction Detection

Input:
    state["entities"]
    state["timeline"]
    state["relationships"]   (used if available, for richer detection)

Output:
    {
        "contradictions": [
            {
                "contradiction_id": "CONTRA001",
                "description": "Rahul is reported in Chennai and Coimbatore at the same time.",
                "evidence_ids": ["EVD001", "EVD004"],
                "conflicting_values": ["Chennai", "Coimbatore"],
                "severity": "high",
                "confidence": 0.85
            }
        ]
    }

Purpose:
    Detect genuine inconsistencies across evidence — conflicting
    locations, conflicting timestamps for what should be the same
    event, contradictory statements attributed to the same person.

Important:
    A contradiction does NOT mean someone lied — it flags evidence that
    needs investigator review. This agent must NOT invent contradictions
    that are not clearly supported by the evidence, and must NOT cite
    an evidence_id it cannot verify exists.
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

    AGENT_NAME = "Agent 6 - Contradiction Detection"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_name=model_used)

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()

        entities: Dict[str, List[Dict[str, Any]]] = state.get("entities", {})
        timeline: List[Dict[str, Any]] = state.get("timeline", [])
        relationships: List[Dict[str, Any]] = state.get("relationships", [])

        empty_contradictions: List[Dict[str, Any]] = []

        if not entities and not timeline:
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="partial", input_evidence=[],
                output_summary="No entities or timeline found in state; skipping contradiction detection.",
            )
            return {"contradictions": empty_contradictions}

        # Build the set of evidence IDs we can actually verify, so we
        # never let a hallucinated evidence ID anchor a contradiction.
        known_evidence_ids = set(state.get("evidence_metadata", {}).keys())
        for event in timeline:
            for eid in event.get("evidence_ids", []) or []:
                known_evidence_ids.add(eid)

        try:
            schema = {
                "type": "object",
                "properties": {
                    "contradictions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "evidence_ids": {"type": "array", "items": {"type": "string"}},
                                "conflicting_values": {"type": "array", "items": {"type": "string"}},
                                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                                "confidence": {"type": "number"},
                            },
                            "required": ["description", "conflicting_values", "severity", "confidence"],
                        },
                    }
                },
                "required": ["contradictions"],
            }

            prompt = self._build_prompt(entities, timeline, relationships)

            print("\n========== AGENT 6 PROMPT ==========")
            print(prompt)
            print("========== END AGENT 6 DEBUG ==========\n")

            result = self.call_llm(prompt, json_schema=schema)
            raw_contradictions = result.get("contradictions", []) or []
            if not isinstance(raw_contradictions, list):
                raise ValueError("LLM returned invalid contradictions format.")

            contradictions: List[Dict[str, Any]] = []

            for idx, item in enumerate(raw_contradictions):
                if not isinstance(item, dict):
                    continue

                description = str(item.get("description", "")).strip()
                conflicting_values = item.get("conflicting_values", []) or []
                if not description or not conflicting_values:
                    continue

                evidence_ids_raw = item.get("evidence_ids", []) or []
                verified_evidence_ids = [eid for eid in evidence_ids_raw if eid in known_evidence_ids]

                severity = item.get("severity", "medium")
                if severity not in ("low", "medium", "high"):
                    severity = "medium"

                try:
                    confidence = float(item.get("confidence", 0.7))
                except (TypeError, ValueError):
                    confidence = 0.7
                confidence = max(0.0, min(1.0, confidence))

                # Down-weight confidence if the LLM cited evidence we
                # couldn't verify — an unverifiable link is weaker proof.
                if evidence_ids_raw and not verified_evidence_ids:
                    confidence = round(confidence * 0.5, 2)

                contradiction_id = f"CONTRA{idx + 1:03d}"

                contradictions.append({
                    "contradiction_id": contradiction_id,
                    "description": description,
                    "evidence_ids": verified_evidence_ids,
                    "conflicting_values": [str(v) for v in conflicting_values],
                    "severity": severity,
                    "confidence": confidence,
                })

                add_confidence_score(
                    state, item_id=contradiction_id, category="contradiction",
                    score=confidence, reason=description,
                )

                for eid in verified_evidence_ids:
                    add_evidence_reference(
                        state, finding=description, evidence_id=eid,
                        source="cross-evidence contradiction analysis",
                    )

                # Every contradiction requires human sign-off.
                flag_for_review(
                    state, item_id=contradiction_id, category="contradiction",
                    notes=f"Severity: {severity}. {description}",
                )

            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="success",
                input_evidence=sorted(known_evidence_ids),
                output_summary=f"Detected {len(contradictions)} contradiction(s).",
            )

            return {"contradictions": contradictions}

        except Exception as e:
            print(f"[Agent 6] Failed: {e}")
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="failed", input_evidence=[],
                output_summary="Contradiction detection failed.", error_message=str(e),
            )
            return {"contradictions": empty_contradictions}

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(entities, timeline, relationships) -> str:
        entity_summary = "\n".join(
            f"- [{etype}] {item.get('name')} (mentions: {', '.join(item.get('mentions', [])) or 'unknown'})"
            for etype, items in (entities or {}).items() for item in items
        ) or "No entities available."

        timeline_summary = "\n".join(
            f"- {ev.get('timestamp') or 'unknown time'}: {ev.get('description', '')} "
            f"(evidence: {', '.join(ev.get('evidence_ids', [])) or 'unknown'})"
            for ev in timeline
        ) or "No timeline available."

        relationship_summary = "\n".join(
            f"- {r.get('subject')} {r.get('relationship')} {r.get('object')} "
            f"(evidence: {', '.join(r.get('source_documents', []) or r.get('evidence_ids', []))})"
            for r in relationships
        ) or "No relationships available."

        return f"""
You are a forensic contradiction-detection assistant for INVESTCOPS AI.

Analyze the entities, timeline, and relationships below. Identify
statements, locations, or timestamps that GENUINELY CONTRADICT one
another — e.g. a person reported in two different locations at
overlapping times, conflicting timestamps for what should be the same
event, or contradictory relationship claims.

Only report contradictions clearly supported by the evidence. Do NOT
report simple differences in detail level as contradictions.

For every contradiction, cite the evidence_ids involved (evidence IDs
look like "EVD001") ONLY when you can determine them from the timeline
entries above, list the specific conflicting values, and give a
severity (low/medium/high) and confidence (0.0-1.0).

ENTITIES:
{entity_summary}

TIMELINE:
{timeline_summary}

RELATIONSHIPS:
{relationship_summary}

IMPORTANT RULES:
1. Do NOT invent contradictions not supported by the evidence.
2. Do NOT cite an evidence_id you are not confident about — omit it
   rather than guess.
3. If none are found, return an empty list.
4. Return ONLY valid JSON. No Markdown, no explanations outside JSON.

RETURN EXACTLY THIS JSON STRUCTURE:

{{
    "contradictions": [
        {{
            "description": "Rahul is reported in Chennai and Coimbatore at the same time.",
            "evidence_ids": ["EVD001", "EVD004"],
            "conflicting_values": ["Chennai", "Coimbatore"],
            "severity": "high",
            "confidence": 0.85
        }}
    ]
}}
"""