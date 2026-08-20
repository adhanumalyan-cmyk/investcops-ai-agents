

"""
agents/agent_2_entities.py

Agent 2 - Entity Extraction

Input:
    state["cleaned_documents"]

Output:
    {
        "entities": {
            "people": [...],
            "locations": [...],
            "orgs": [...],
            "devices": [...]
        }
    }
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
)

from core.base_agent import BaseAgent


# ==========================================================
# ENTITY CATEGORIES
# ==========================================================

ENTITY_TYPES = [
    "people",
    "locations",
    "orgs",
    "devices",
]


# ==========================================================
# AGENT 2
# ==========================================================

class EntityExtractionAgent(BaseAgent):
    """
    Extracts people, locations, organizations, and devices
    from cleaned evidence documents.

    Agent 2 receives the standardized text produced by Agent 1
    and uses the LLM to identify entities.
    """

    AGENT_NAME = "Agent 2 - Entity Extraction"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(
            agent_name=self.AGENT_NAME,
            model_name=model_used,
        )

    # ======================================================
    # MAIN PROCESS
    # ======================================================

    def process(
        self,
        state: InvestigationState,
    ) -> Dict[str, Any]:

        started_at = datetime.utcnow()

        # --------------------------------------------------
        # Get documents produced by Agent 1
        # --------------------------------------------------

        cleaned_documents: List[Dict[str, str]] = state.get(
            "cleaned_documents",
            []
        )

        # Empty output structure
        empty_entities = {
            entity_type: []
            for entity_type in ENTITY_TYPES
        }

        # --------------------------------------------------
        # No documents available
        # --------------------------------------------------

        if not cleaned_documents:

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_name,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary="No cleaned_documents found in state.",
            )

            return {
                "entities": empty_entities
            }

        # --------------------------------------------------
        # Dictionary used to merge duplicate entities
        #
        # Example:
        #
        # Rahul appears in DOC001 and DOC002.
        #
        # We keep one Rahul entity and store both mentions.
        # --------------------------------------------------

        merged: Dict[
            str,
            Dict[str, Dict[str, Any]]
        ] = {
            entity_type: {}
            for entity_type in ENTITY_TYPES
        }

        failures = 0

        # --------------------------------------------------
        # Collect document IDs
        # --------------------------------------------------

        doc_ids = [
            document.get(
                "doc_id",
                f"DOC{i + 1:03d}"
            )
            for i, document in enumerate(cleaned_documents)
        ]

        # ==================================================
        # PROCESS EACH DOCUMENT
        # ==================================================

        for document in cleaned_documents:

            doc_id = document.get(
                "doc_id",
                "UNKNOWN"
            )

            text = document.get(
                "cleaned_text",
                ""
            )

            # Skip empty documents
            if not text.strip():
                continue

            try:

                # --------------------------------------------------
                # JSON schema expected from Qwen
                # --------------------------------------------------

                schema = {
                    "type": "object",
                    "properties": {
                        entity_type: {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    },
                                    "confidence": {
                                        "type": "number"
                                    },
                                },
                                "required": [
                                    "name",
                                    "confidence"
                                ],
                            },
                        }
                        for entity_type in ENTITY_TYPES
                    },
                    "required": ENTITY_TYPES,
                }

                # --------------------------------------------------
                # Build extraction prompt
                # --------------------------------------------------

                prompt = self._build_prompt(text)

                # --------------------------------------------------
                # DEBUG
                # --------------------------------------------------

                print(
                    "\n========== AGENT 2 PROMPT =========="
                )
                print(prompt)

                print(
                    "\n========== AGENT 2 SCHEMA =========="
                )
                print(schema)

                print(
                    "========== END AGENT 2 DEBUG ==========\n"
                )

                # --------------------------------------------------
                # Send prompt to Qwen through BaseAgent
                # --------------------------------------------------

                result = self.call_llm(
                    prompt,
                    json_schema=schema,
                )

                # --------------------------------------------------
                # Process returned entities
                # --------------------------------------------------

                for entity_type in ENTITY_TYPES:

                    items = result.get(
                        entity_type,
                        []
                    ) or []

                    # Safety check
                    if not isinstance(items, list):
                        continue

                    for item in items:

                        if not isinstance(item, dict):
                            continue

                        name = (
                            item.get("name") or ""
                        ).strip()

                        if not name:
                            continue

                        # Case-insensitive duplicate detection
                        key = name.lower()

                        # --------------------------------------------------
                        # Read confidence
                        # --------------------------------------------------

                        try:

                            confidence = float(
                                item.get(
                                    "confidence",
                                    0.7
                                )
                            )

                        except (
                            TypeError,
                            ValueError
                        ):

                            confidence = 0.7

                        # Keep confidence between 0 and 1
                        confidence = max(
                            0.0,
                            min(
                                1.0,
                                confidence
                            )
                        )

                        # --------------------------------------------------
                        # First occurrence of entity
                        # --------------------------------------------------

                        if key not in merged[entity_type]:

                            merged[entity_type][key] = {
                                "name": name,
                                "type": entity_type,
                                "mentions": [],
                                "confidences": [],
                            }

                        # --------------------------------------------------
                        # Record document mention
                        # --------------------------------------------------

                        merged[entity_type][key][
                            "mentions"
                        ].append(doc_id)

                        merged[entity_type][key][
                            "confidences"
                        ].append(confidence)

            except Exception as error:

                failures += 1

                print(
                    f"[Agent 2] Failed processing "
                    f"{doc_id}: {error}"
                )

        # ==================================================
        # BUILD FINAL ENTITY OUTPUT
        # ==================================================

        entities: Dict[
            str,
            List[Dict[str, Any]]
        ] = {
            entity_type: []
            for entity_type in ENTITY_TYPES
        }

        for entity_type in ENTITY_TYPES:

            for key, data in merged[entity_type].items():

                confidences = data["confidences"]

                # --------------------------------------------------
                # Calculate average confidence
                # --------------------------------------------------

                if confidences:

                    average_confidence = round(
                        sum(confidences)
                        / len(confidences),
                        2
                    )

                else:

                    average_confidence = 0.0

                # --------------------------------------------------
                # Create final entity record
                # --------------------------------------------------

                entity_record = {
                    "name": data["name"],
                    "type": entity_type,
                    "mentions": sorted(
                        set(data["mentions"])
                    ),
                }

                entities[entity_type].append(
                    entity_record
                )

                # --------------------------------------------------
                # Save confidence information
                # --------------------------------------------------

                add_confidence_score(
                    state,
                    item_id=(
                        f"{entity_type}:"
                        f"{data['name']}"
                    ),
                    category="entity",
                    score=average_confidence,
                    reason=(
                        f"Averaged over "
                        f"{len(confidences)} "
                        f"mention(s)."
                    ),
                )

        # ==================================================
        # DETERMINE EXECUTION STATUS
        # ==================================================

        total_documents = len(
            cleaned_documents
        )

        if failures == 0:

            status = "success"

        elif failures < total_documents:

            status = "partial"

        else:

            status = "failed"

        # ==================================================
        # COUNT ENTITIES
        # ==================================================

        total_entities = sum(
            len(values)
            for values in entities.values()
        )

        # ==================================================
        # EXECUTION LOG
        # ==================================================

        log_agent_execution(
            state,
            agent_name=self.AGENT_NAME,
            model_used=self.model_name,
            started_at=started_at,
            status=status,
            input_evidence=doc_ids,
            output_summary=(
                f"Extracted "
                f"{total_entities} unique entities "
                f"from "
                f"{total_documents - failures}/"
                f"{total_documents} documents."
            ),
            error_message=(
                f"{failures} document(s) failed "
                f"entity extraction."
                if failures
                else None
            ),
        )

        # --------------------------------------------------
        # Return Agent 2 output
        # --------------------------------------------------

        return {
            "entities": entities
        }

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(
        text: str,
    ) -> str:

        return f"""
You are a forensic entity extraction assistant for INVESTCOPS AI.

Your task is to extract ONLY entities that are explicitly present
in the investigation evidence.

Identify these four categories:

1. people
   Names of people.

2. locations
   Places, cities, addresses, landmarks, or other locations.

3. orgs
   Organizations, companies, institutions, agencies, or groups.

4. devices
   Phone numbers, IMEI numbers, IP addresses, laptops, phones,
   vehicles, applications, usernames, or online accounts.

For every entity provide:

- name
- confidence between 0.0 and 1.0

IMPORTANT RULES:

- Extract only information explicitly supported by the evidence.
- Do not invent entities.
- Do not infer entities that are not present.
- Do not create relationships.
- Do not create events.
- Do not create conclusions.
- If a category has no entities, return an empty list.
- Return ONLY valid JSON.
- Do not use Markdown.
- Do not include explanations outside the JSON.

INVESTIGATION EVIDENCE:

{text}

RETURN EXACTLY THIS JSON STRUCTURE:

{{
    "people": [
        {{
            "name": "Rahul",
            "confidence": 0.95
        }}
    ],
    "locations": [
        {{
            "name": "Gandhipuram",
            "confidence": 0.95
        }}
    ],
    "orgs": [],
    "devices": []
}}
"""