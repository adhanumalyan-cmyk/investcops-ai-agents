"""
agents/agent_1_ingestion.py

Agent 1 - Evidence Ingestion & Cleaning

Input : state["raw_texts"]        (List[str])
Output: {"cleaned_documents": [...]}

Assumed BaseAgent interface (core/base_agent.py):
    class BaseAgent:
        def __init__(self, agent_name: str, model_used: str = "qwen3:8b"): ...
        def call_llm(self, prompt: str, json_schema: dict | None = None) -> dict: ...
            # Calls Ollama (qwen3:8b), enforces json_schema if given,
            # returns a parsed dict, raises Exception on failure.
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import InvestigationState, log_agent_execution
from core.base_agent import BaseAgent


class IngestionAgent(BaseAgent):
    """Cleans and normalizes raw extracted text (OCR noise, transcripts,
    chat exports, etc.) into structured, analyzable documents.
    """

    AGENT_NAME = "Agent 1 - Evidence Ingestion & Cleaning"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_used=model_used)

    # ------------------------------------------------------------------
    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()
        raw_texts: List[str] = state.get("raw_texts", [])

        if not raw_texts:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary="No raw_texts found in state; nothing to clean.",
            )
            return {"cleaned_documents": []}

        cleaned_documents: List[Dict[str, str]] = []
        failures = 0
        doc_ids = [f"DOC{idx + 1:03d}" for idx in range(len(raw_texts))]

        for doc_id, text in zip(doc_ids, raw_texts):
            try:
                if not text or not text.strip():
                    raise ValueError("Empty raw text")

                schema = {
                    "type": "object",
                    "properties": {
                        "cleaned_text": {"type": "string"},
                        "language": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": ["cleaned_text"],
                }
                prompt = self._build_prompt(text)
                result = self.call_llm(prompt, json_schema=schema)

                cleaned_documents.append(
                    {
                        "doc_id": doc_id,
                        "original_text": text,
                        "cleaned_text": (result.get("cleaned_text") or text).strip(),
                        "language": result.get("language", "unknown"),
                        "notes": result.get("notes", ""),
                    }
                )
            except Exception as e:
                failures += 1
                # Fallback: keep the raw text untouched so downstream
                # agents still have something to work with.
                cleaned_documents.append(
                    {
                        "doc_id": doc_id,
                        "original_text": text,
                        "cleaned_text": text,
                        "language": "unknown",
                        "notes": f"cleaning_failed: {e}",
                    }
                )

        if failures == 0:
            status = "success"
        elif failures < len(raw_texts):
            status = "partial"
        else:
            status = "failed"

        log_agent_execution(
            state,
            agent_name=self.AGENT_NAME,
            model_used=self.model_used,
            started_at=started_at,
            status=status,
            input_evidence=doc_ids,
            output_summary=f"Cleaned {len(raw_texts) - failures}/{len(raw_texts)} documents.",
            error_message=f"{failures} document(s) failed cleaning and used raw fallback." if failures else None,
        )

        return {"cleaned_documents": cleaned_documents}

    # ------------------------------------------------------------------
    @staticmethod
    def _build_prompt(text: str) -> str:
        return f"""You are a forensic evidence cleaning assistant for INVESTCOPS AI.

Clean and normalize the following raw extracted text (it may come from OCR,
audio transcription, or a chat export and can contain noise, broken
formatting, or artifacts). Do NOT invent, remove, or alter any factual
content, names, numbers, or dates — only fix formatting, spacing, and
obvious OCR/transcription noise.

Raw text:
\"\"\"{text}\"\"\"

Return ONLY valid JSON:
{{
  "cleaned_text": "<the cleaned, normalized text>",
  "language": "<detected language, e.g. 'en', 'ta', 'hi'>",
  "notes": "<any short note on what was cleaned, or empty string>"
}}"""