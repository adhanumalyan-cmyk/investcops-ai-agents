"""
agents/agent_9_rag_qa.py

Agent 9 - Investigation GPT (RAG Q&A)

NOTE: originally assigned to teammate C — confirm with them before
merging this in, in case they've already built their own version.

Called ON-DEMAND (NOT part of the linear pipeline) whenever an
investigator asks a free-form question about the case.

Usage:
    updates = RAGQAAgent().process(state, question="Where was Rahul on the night of the 12th?")
    state.update(updates)

Output:
    {"qa_history": [... state["qa_history"] + one new entry ...]}
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import InvestigationState, log_agent_execution, add_evidence_reference
from core.base_agent import BaseAgent


class RAGQAAgent(BaseAgent):

    AGENT_NAME = "Agent 9 - Investigation GPT (RAG Q&A)"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_name=model_used)

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, state: InvestigationState, question: str) -> Dict[str, Any]:
        started_at = datetime.utcnow()
        question = (question or "").strip()

        qa_history: List[Dict[str, Any]] = list(state.get("qa_history", []))

        if not question:
            return {"qa_history": qa_history}

        context = self._build_context(state)

        if not context.strip():
            answer = "I don't have enough evidence in this case yet to answer that."
            qa_history.append({
                "question": question,
                "answer": answer,
                "evidence_ids": [],
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            })
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="partial", input_evidence=[],
                output_summary="No case context available to answer question.",
            )
            return {"qa_history": qa_history}

        try:
            schema = {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number"},
                },
                "required": ["answer"],
            }
            prompt = self._build_prompt(context, question)

            print("\n========== AGENT 9 PROMPT ==========")
            print(prompt)
            print("========== END AGENT 9 DEBUG ==========\n")

            result = self.call_llm(prompt, json_schema=schema)
            answer = str(result.get("answer", "")).strip() or \
                "I could not find a clear answer in the current evidence."

            known_evidence_ids = set(state.get("evidence_metadata", {}).keys())
            evidence_ids = [
                eid for eid in (result.get("evidence_ids", []) or []) if eid in known_evidence_ids
            ]

            try:
                confidence = float(result.get("confidence", 0.6))
            except (TypeError, ValueError):
                confidence = 0.6
            confidence = max(0.0, min(1.0, confidence))

            for eid in evidence_ids:
                add_evidence_reference(
                    state, finding=answer, evidence_id=eid, source="Investigation GPT Q&A",
                )

            qa_history.append({
                "question": question,
                "answer": answer,
                "evidence_ids": evidence_ids,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            })

            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="success", input_evidence=evidence_ids,
                output_summary=f"Answered investigator question ({len(answer)} chars).",
            )

            return {"qa_history": qa_history}

        except Exception as e:
            print(f"[Agent 9] Failed: {e}")
            answer = f"Sorry, I couldn't process that question right now ({e})."
            qa_history.append({
                "question": question,
                "answer": answer,
                "evidence_ids": [],
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            })
            log_agent_execution(
                state, agent_name=self.AGENT_NAME, model_used=self.model_name,
                started_at=started_at, status="failed", input_evidence=[],
                output_summary="Q&A failed.", error_message=str(e),
            )
            return {"qa_history": qa_history}

    # ==========================================================
    # CONTEXT BUILDER (the "R" in RAG — retrieval from state)
    # ==========================================================

    @staticmethod
    def _build_context(state: InvestigationState) -> str:
        entities = state.get("entities", {})
        relationships = state.get("relationships", [])
        timeline = state.get("timeline", [])
        contradictions = state.get("contradictions", [])
        correlations = state.get("correlations", [])
        insights = state.get("insights_summary", "")

        parts = []
        if insights:
            parts.append(f"CASE SUMMARY:\n{insights}")

        entity_lines = "\n".join(
            f"- [{etype}] {item.get('name')}"
            for etype, items in (entities or {}).items() for item in items
        )
        if entity_lines:
            parts.append(f"ENTITIES:\n{entity_lines}")

        rel_lines = "\n".join(
            f"- {r.get('subject')} {r.get('relationship')} {r.get('object')} "
            f"(evidence: {', '.join(r.get('source_documents', []) or r.get('evidence_ids', []))})"
            for r in relationships
        )
        if rel_lines:
            parts.append(f"RELATIONSHIPS:\n{rel_lines}")

        timeline_lines = "\n".join(
            f"- {ev.get('timestamp') or 'unknown time'}: {ev.get('description', '')} "
            f"(evidence: {', '.join(ev.get('evidence_ids', []))})"
            for ev in timeline
        )
        if timeline_lines:
            parts.append(f"TIMELINE:\n{timeline_lines}")

        contradiction_lines = "\n".join(
            f"- [{c.get('severity', 'medium')}] {c.get('description', '')} "
            f"(evidence: {', '.join(c.get('evidence_ids', []))})"
            for c in contradictions
        )
        if contradiction_lines:
            parts.append(f"CONTRADICTIONS:\n{contradiction_lines}")

        correlation_lines = "\n".join(
            f"- {c.get('correlation_type')}: {c.get('explanation', '')}" for c in correlations
        )
        if correlation_lines:
            parts.append(f"CORRELATIONS:\n{correlation_lines}")

        return "\n\n".join(parts)

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(context: str, question: str) -> str:
        return f"""
You are "Investigation GPT" for INVESTCOPS AI — a forensic Q&A
assistant that answers an investigator's questions using ONLY the
case evidence provided below. Do not use outside knowledge or
speculation.

CASE CONTEXT:
{context}

INVESTIGATOR'S QUESTION:
{question}

RULES:
1. Answer using ONLY the context above.
2. If the context does not contain the answer, say so clearly rather
   than guessing.
3. Cite the evidence_ids (e.g. "EVD001") that support your answer,
   if any are relevant and identifiable from the context.
4. Do not state conclusions of guilt or motive.
5. Return ONLY valid JSON.

Return exactly this structure:

{{
    "answer": "<your answer, grounded in the context above>",
    "evidence_ids": ["EVD001"],
    "confidence": 0.8
}}
"""