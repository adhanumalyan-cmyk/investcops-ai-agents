"""
Agent 10: Investigation GPT / RAG Q&A.

Retrieval over current case evidence (deterministic token-overlap scoring),
optional LLM synthesis with strict evidence-only instructions, citation
validation. When evidence is insufficient the answer explicitly states:
"Insufficient evidence available."
"""

import re
from typing import Any, Dict, List

from core.base_agent import BaseAgent
from core.llm import complete, llm_enabled
from core.state import InvestigationState, QAExchange

INSUFFICIENT_ANSWER = "Insufficient evidence available."


class Agent10RagQA(BaseAgent):
    name = "agent_10_rag_qa"
    description = "Investigation GPT / RAG Q&A"
    prompt_version = "10.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        question = (self._question or "").strip()
        if not question:
            self.logger.warning("Agent 10 called without a question; returning NEEDS_REVIEW.")
            raise RuntimeError("No question provided to Investigation GPT.")

        chunks = self._build_chunks(state)
        if not chunks:
            exchange = QAExchange(
                question=question,
                answer=INSUFFICIENT_ANSWER,
                evidence_ids=[],
                source_references=[],
                confidence=0.0,
                limitations=["No processed evidence text is available for the case."],
            )
            state.qa_history.append(exchange)
            return self._pack(state, exchange, [])

        scored = self._rank_chunks(question, chunks)
        context_parts = [f"[{s['evidence_id']}] {s['text']}" for s in scored[:10]]
        context = "\n".join(context_parts)
        context = context[: self.config.LLM_MAX_CONTEXT_CHARS]

        evidence_ids = list(dict.fromkeys(s["evidence_id"] for s in scored[:10]))
        source_references = [
            f"{s['evidence_id']} - {s['file_name']}" for s in scored[:10]
        ]

        if llm_enabled():
            answer, ok = self._llm_answer(question, context)
        else:
            answer, ok = self._deterministic_answer(question, scored, evidence_ids), True

        if not ok:
            answer = self._fallback(question, scored, evidence_ids)

        limitations = [
            "Answer is limited to the processed evidence available in this case.",
            "Grounded answers do not constitute legal advice or a legal determination.",
        ]
        if not llm_enabled():
            limitations.append("LLM synthesis not configured; answer assembled deterministically.")
        if answer == INSUFFICIENT_ANSWER:
            limitations.append("No matching evidence found for this question.")

        confidence = self._answer_confidence(question, scored, evidence_ids, llm_used=llm_enabled())
        exchange = QAExchange(
            question=question,
            answer=answer,
            evidence_ids=evidence_ids,
            source_references=source_references,
            confidence=confidence,
            limitations=limitations,
        )
        state.qa_history.append(exchange)
        return self._pack(state, exchange, evidence_ids)

    # --- retrieval -----------------------------------------------------------

    def _build_chunks(self, state: InvestigationState) -> List[dict]:
        docs = {d["evidence_id"]: d for d in state.cleaned_documents}
        chunks: List[dict] = []
        for ev in state.validated_evidence:
            text = (docs.get(ev.evidence_id, {}) or {}).get("text", "") or ""
            if not text:
                continue
            text = re.sub(r"\s+", " ", text)
            step = 900
            for i in range(0, max(1, len(text)), step):
                piece = text[i : i + step]
                if len(piece.strip()) < 40:
                    continue
                chunks.append(
                    {"evidence_id": ev.evidence_id, "file_name": ev.file_name, "text": piece}
                )
        return chunks

    def _rank_chunks(self, question: str, chunks: List[dict]) -> List[dict]:
        q_tokens = self._tokens(question)
        q_stems = {t[:6] for t in q_tokens}
        scored: List[tuple[float, int, dict]] = []
        for idx, chunk in enumerate(chunks):
            text = chunk["text"].lower()
            hit = sum(t in text for t in q_tokens)
            stem_hit = sum(s in text for s in q_stems)
            if hit or stem_hit:
                score = hit / max(1, len(q_tokens)) + min(stem_hit * 0.04, 0.4) + min(hit * 0.05, 0.3)
                scored.append((score, -idx, chunk))
        scored.sort(reverse=True)
        return [c for _, _, c in scored[:15]]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stops = {
            "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
            "what", "who", "when", "where", "why", "how", "is", "are", "was",
            "were", "did", "do", "does", "has", "have", "had", "i", "you", "we",
            "they", "he", "she", "it", "with", "about", "this", "that", "tell", "me",
        }
        return {w for w in re.findall(r"[a-z0-9]{3,}", text.lower()) if w not in stops}

    # --- answering paths ------------------------------------------------------

    def _llm_answer(self, question: str, context: str) -> tuple[str, bool]:
        if not context.strip():
            return INSUFFICIENT_ANSWER, True
        try:
            reply = complete(
                f"Evidence context:\n{context}\n\nQuestion: {question}\n\n"
                "Answer using ONLY the evidence context. Cite evidence IDs like [E-xxx] when used. "
                "If the context does not answer the question, reply exactly: Insufficient evidence available.",
                system=(
                    "Digital investigation assistant. Evidence-grounded answers only. "
                    "Never fabricate evidence, identities or citations. No legal determinations. Report uncertainty."
                ),
            )
        except Exception as exc:
            self.logger.warning("LLM Q&A unavailable: %s", exc)
            return "", False
        if not reply.strip():
            return INSUFFICIENT_ANSWER, True
        return reply.strip(), True

    def _deterministic_answer(
        self, question: str, scored: List[dict], evidence_ids: List[str]
    ) -> str:
        if not scored:
            return INSUFFICIENT_ANSWER
        top = scored[:3]
        parts = [
            "Deterministic retrieval (no LLM configured) - the following evidence is most relevant to your question:"
        ]
        for s in top:
            snippet = s["text"]
            if len(snippet) > 500:
                snippet = snippet[:500] + "..."
            parts.append(f"- [{s['evidence_id']}] {snippet}")
            evidence_ids.append(s["evidence_id"])
        return "\n".join(parts)

    def _fallback(self, question: str, scored: List[dict], evidence_ids: List[str]) -> str:
        if not scored:
            return INSUFFICIENT_ANSWER
        top = scored[0]["text"][:600]
        return (
            f"Question could not be answered through the LLM; evidence-based retrieval found: "
            f"[{scored[0]['evidence_id']}] {top}"
        )

    def _answer_confidence(
        self, question: str, scored: List[dict], evidence_ids: List[str], llm_used: bool
    ) -> float:
        if not scored:
            return 0.0
        q_tokens = self._tokens(question)
        top_text = scored[0]["text"].lower()
        hit = sum(t in top_text for t in q_tokens)
        stem_hit = sum(t[:6] in top_text for t in q_tokens)
        ratio = min((hit + stem_hit * 0.3) / max(1, len(q_tokens)), 1.0)
        base = 0.35 + 0.45 * ratio
        if llm_used:
            base = min(base + 0.1, 0.95)
        return round(min(base, 0.95), 3)

    def _pack(self, state: InvestigationState, exchange: QAExchange, evidence_ids: List[str]) -> Dict[str, Any]:
        return {
            "result": {
                "question": exchange.question,
                "answer": exchange.answer,
                "evidence_ids": exchange.evidence_ids,
                "source_references": exchange.source_references,
                "confidence": exchange.confidence,
                "limitations": exchange.limitations,
            },
            "state_fields": {"qa_history": state.qa_history},
            "confidence": exchange.confidence,
            "evidence_references": [
                self._provenance(
                    eid, source_reference=ref, confidence=exchange.confidence
                )
                for eid, ref in zip(exchange.evidence_ids, exchange.source_references)
            ],
            "warnings": (
                ["Question answered with insufficient grounding - review before use."]
                if exchange.answer == INSUFFICIENT_ANSWER
                else []
            ),
            "evidence_ids": exchange.evidence_ids,
        }

    # question is passed via instance attr set by the caller (bridge/backend)
    _question: str = ""