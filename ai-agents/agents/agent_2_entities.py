"""
agents/agent_2_entities.py

Agent 2 - Entity Extraction

Input : state["cleaned_documents"]   (List[Dict[str, str]])
Output: {"entities": {"people": [...], "locations": [...], "orgs": [...], "devices": [...]}}
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
)
from core.base_agent import BaseAgent

ENTITY_TYPES = ["people", "locations", "orgs", "devices"]


class EntityExtractionAgent(BaseAgent):
    """Extracts people, locations, organizations, and devices from cleaned
    evidence documents and merges duplicate mentions across documents.
    """

    AGENT_NAME = "Agent 2 - Entity Extraction"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_used=model_used)

    # ------------------------------------------------------------------
    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()
        cleaned_documents: List[Dict[str, str]] = state.get("cleaned_documents", [])

        empty_entities = {t: [] for t in ENTITY_TYPES}

        if not cleaned_documents:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary="No cleaned_documents found in state.",
            )
            return {"entities": empty_entities}

        # merged[type][name_lower] = {"name":, "type":, "mentions": [doc_id,...], "confidences": [..]}
        merged: Dict[str, Dict[str, Dict[str, Any]]] = {t: {} for t in ENTITY_TYPES}
        failures = 0
        doc_ids = [d.get("doc_id", f"DOC{i+1:03d}") for i, d in enumerate(cleaned_documents)]

        for doc in cleaned_documents:
            doc_id = doc.get("doc_id", "UNKNOWN")
            text = doc.get("cleaned_text", "")
            if not text.strip():
                continue
            try:
                schema = {
                    "type": "object",
                    "properties": {
                        t: {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "confidence": {"type": "number"},
                                },
                                "required": ["name"],
                            },
                        }
                        for t in ENTITY_TYPES
                    },
                }
                prompt = self._build_prompt(text)
                result = self.call_llm(prompt, json_schema=schema)

                for etype in ENTITY_TYPES:
                    for item in result.get(etype, []) or []:
                        name = (item.get("name") or "").strip()
                        if not name:
                            continue
                        key = name.lower()
                        conf = float(item.get("confidence", 0.7))
                        if key not in merged[etype]:
                            merged[etype][key] = {
                                "name": name,
                                "type": etype,
                                "mentions": [],
                                "confidences": [],
                            }
                        merged[etype][key]["mentions"].append(doc_id)
                        merged[etype][key]["confidences"].append(conf)

            except Exception as e:
                failures += 1
                # skip this doc's extraction, continue with others
                _ = e  # keep for potential logging/debug

        entities: Dict[str, List[Dict[str, Any]]] = {t: [] for t in ENTITY_TYPES}
        for etype in ENTITY_TYPES:
            for key, data in merged[etype].items():
                avg_conf = round(sum(data["confidences"]) / len(data["confidences"]), 2)
                entity_record = {
                    "name": data["name"],
                    "type": etype,
                    "mentions": sorted(set(data["mentions"])),
                }
                entities[etype].append(entity_record)

                add_confidence_score(
                    state,
                    item_id=f"{etype}:{data['name']}",
                    category="entity",
                    score=avg_conf,
                    reason=f"Averaged over {len(data['confidences'])} mention(s).",
                )

        total_docs = len(cleaned_documents)
        if failures == 0:
            status = "success"
        elif failures < total_docs:
            status = "partial"
        else:
            status = "failed"

        total_entities = sum(len(v) for v in entities.values())
        log_agent_execution(
            state,
            agent_name=self.AGENT_NAME,
            model_used=self.model_used,
            started_at=started_at,
            status=status,
            input_evidence=doc_ids,
            output_summary=f"Extracted {total_entities} unique entities from {total_docs - failures}/{total_docs} documents.",
            error_message=f"{failures} document(s) failed entity extraction." if failures else None,
        )

        return {"entities": entities}

    # ------------------------------------------------------------------
    @staticmethod
    def _build_prompt(text: str) -> str:
        return f"""You are a forensic entity extraction assistant for INVESTCOPS AI.

Extract all named entities from the evidence text below, grouped into:
- people (person names)
- locations (places, addresses, cities)
- orgs (organizations, companies, institutions)
- devices (phones, IMEI numbers, laptops, vehicles, IPs, apps/accounts)

For each entity, give a confidence score between 0.0 and 1.0 reflecting how
certain you are that it was correctly identified and typed.

Evidence text:
\"\"\"{text}\"\"\"

Return ONLY valid JSON:
{{
  "people": [{{"name": "<name>", "confidence": 0.9}}],
  "locations": [{{"name": "<name>", "confidence": 0.8}}],
  "orgs": [{{"name": "<name>", "confidence": 0.8}}],
  "devices": [{{"name": "<name>", "confidence": 0.8}}]
}}
If a category has no entities, return an empty list for it."""