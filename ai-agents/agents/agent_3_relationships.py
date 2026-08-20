"""
agents/agent_3_relationships.py

Agent 3 - Relationship Extraction

Input:
    state["cleaned_documents"]
    state["entities"]

Output:
    {
        "relationships": [
            {
                "subject": "Rahul",
                "relationship": "located_at",
                "object": "Gandhipuram",
                "source_documents": ["DOC001"],
                "confidence": 0.95
            }
        ]
    }

Purpose:
    Extract relationships explicitly supported by investigation evidence.

Important:
    This agent must NOT invent relationships.
    Every relationship must be supported by the evidence text.
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
)

from core.base_agent import BaseAgent


class RelationshipExtractionAgent(BaseAgent):
    """
    Agent 3 extracts relationships between entities found by Agent 2.

    Input:
        cleaned_documents
        entities

    Output:
        relationships
    """

    AGENT_NAME = "Agent 3 - Relationship Extraction"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(
            agent_name=self.AGENT_NAME,
            model_name=model_used,
        )

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(
        self,
        state: InvestigationState,
    ) -> Dict[str, Any]:

        started_at = datetime.utcnow()

        # ------------------------------------------------------
        # Get cleaned documents from Agent 1
        # ------------------------------------------------------

        cleaned_documents: List[Dict[str, Any]] = state.get(
            "cleaned_documents",
            []
        )

        # ------------------------------------------------------
        # Get entities from Agent 2
        # ------------------------------------------------------

        entities: Dict[str, List[Dict[str, Any]]] = state.get(
            "entities",
            {}
        )

        # ------------------------------------------------------
        # Empty result
        # ------------------------------------------------------

        empty_relationships: List[Dict[str, Any]] = []

        # ------------------------------------------------------
        # Validate input
        # ------------------------------------------------------

        if not cleaned_documents:

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_name,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary=(
                    "No cleaned_documents found in state."
                ),
            )

            return {
                "relationships": empty_relationships
            }

        if not entities:

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_name,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary=(
                    "No entities found in state."
                ),
            )

            return {
                "relationships": empty_relationships
            }

        # ======================================================
        # Build a simple list of known entity names
        # ======================================================

        known_entities: List[str] = []

        for entity_type, entity_list in entities.items():

            if not isinstance(entity_list, list):
                continue

            for entity in entity_list:

                if not isinstance(entity, dict):
                    continue

                name = entity.get("name")

                if not name:
                    continue

                name = str(name).strip()

                if name and name.lower() not in {
                    existing.lower()
                    for existing in known_entities
                }:
                    known_entities.append(name)

        # ------------------------------------------------------
        # If there are no entities, there is nothing to connect
        # ------------------------------------------------------

        if not known_entities:

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_name,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary=(
                    "No valid entities available for relationship extraction."
                ),
            )

            return {
                "relationships": empty_relationships
            }

        # ======================================================
        # Store relationships temporarily
        #
        # Key:
        # subject + relationship + object
        # ======================================================

        merged: Dict[str, Dict[str, Any]] = {}

        failures = 0

        # ======================================================
        # PROCESS EACH DOCUMENT
        # ======================================================

        for index, document in enumerate(cleaned_documents):

            doc_id = document.get(
                "doc_id",
                f"DOC{index + 1:03d}"
            )

            text = document.get(
                "cleaned_text",
                ""
            )

            if not isinstance(text, str):
                text = str(text)

            if not text.strip():
                continue

            try:

                # --------------------------------------------------
                # JSON schema expected from Qwen
                # --------------------------------------------------

                schema = {
                    "type": "object",
                    "properties": {
                        "relationships": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "subject": {
                                        "type": "string"
                                    },
                                    "relationship": {
                                        "type": "string"
                                    },
                                    "object": {
                                        "type": "string"
                                    },
                                    "confidence": {
                                        "type": "number"
                                    }
                                },
                                "required": [
                                    "subject",
                                    "relationship",
                                    "object",
                                    "confidence"
                                ]
                            }
                        }
                    },
                    "required": [
                        "relationships"
                    ]
                }

                # --------------------------------------------------
                # Build prompt
                # --------------------------------------------------

                prompt = self._build_prompt(
                    text=text,
                    known_entities=known_entities,
                )

                # --------------------------------------------------
                # Call Qwen through BaseAgent
                # --------------------------------------------------

                result = self.call_llm(
                    prompt,
                    json_schema=schema,
                )

                # --------------------------------------------------
                # Read relationships
                # --------------------------------------------------

                document_relationships = result.get(
                    "relationships",
                    []
                ) or []

                if not isinstance(
                    document_relationships,
                    list
                ):
                    raise ValueError(
                        "LLM returned invalid relationships format."
                    )

                # --------------------------------------------------
                # Process every relationship
                # --------------------------------------------------

                for item in document_relationships:

                    if not isinstance(item, dict):
                        continue

                    subject = str(
                        item.get("subject", "")
                    ).strip()

                    relationship = str(
                        item.get("relationship", "")
                    ).strip()

                    object_name = str(
                        item.get("object", "")
                    ).strip()

                    if (
                        not subject
                        or not relationship
                        or not object_name
                    ):
                        continue

                    # ------------------------------------------------
                    # Confidence
                    # ------------------------------------------------

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

                    confidence = max(
                        0.0,
                        min(
                            1.0,
                            confidence
                        )
                    )

                    # ------------------------------------------------
                    # Normalize relationship
                    # ------------------------------------------------

                    relationship = (
                        relationship
                        .lower()
                        .strip()
                        .replace(" ", "_")
                    )

                    # ------------------------------------------------
                    # Merge duplicate relationships
                    # ------------------------------------------------

                    key = (
                        f"{subject.lower()}|"
                        f"{relationship}|"
                        f"{object_name.lower()}"
                    )

                    if key not in merged:

                        merged[key] = {
                            "subject": subject,
                            "relationship": relationship,
                            "object": object_name,
                            "source_documents": [],
                            "confidences": [],
                        }

                    if doc_id not in merged[key][
                        "source_documents"
                    ]:

                        merged[key][
                            "source_documents"
                        ].append(doc_id)

                    merged[key][
                        "confidences"
                    ].append(confidence)

            except Exception as error:

                failures += 1

                print(
                    f"[Agent 3] Failed processing "
                    f"{doc_id}: {error}"
                )

        # ======================================================
        # BUILD FINAL RELATIONSHIP OUTPUT
        # ======================================================

        relationships: List[Dict[str, Any]] = []

        for key, data in merged.items():

            confidences = data["confidences"]

            if confidences:

                average_confidence = round(
                    sum(confidences)
                    / len(confidences),
                    2
                )

            else:

                average_confidence = 0.0

            relationship_record = {
                "subject": data["subject"],
                "relationship": data["relationship"],
                "object": data["object"],
                "source_documents": sorted(
                    set(data["source_documents"])
                ),
                "confidence": average_confidence,
            }

            relationships.append(
                relationship_record
            )

            # --------------------------------------------------
            # Save confidence score
            # --------------------------------------------------

            add_confidence_score(
                state,
                item_id=(
                    f"relationship:"
                    f"{data['subject']}:"
                    f"{data['relationship']}:"
                    f"{data['object']}"
                ),
                category="relationship",
                score=average_confidence,
                reason=(
                    f"Supported by "
                    f"{len(data['source_documents'])} "
                    f"document(s)."
                ),
            )

        # ======================================================
        # DETERMINE STATUS
        # ======================================================

        total_documents = len(
            cleaned_documents
        )

        if failures == 0:

            status = "success"

        elif failures < total_documents:

            status = "partial"

        else:

            status = "failed"

        # ======================================================
        # DOCUMENT IDs
        # ======================================================

        doc_ids = [
            document.get(
                "doc_id",
                f"DOC{i + 1:03d}"
            )
            for i, document in enumerate(
                cleaned_documents
            )
        ]

        # ======================================================
        # EXECUTION LOG
        # ======================================================

        log_agent_execution(
            state,
            agent_name=self.AGENT_NAME,
            model_used=self.model_name,
            started_at=started_at,
            status=status,
            input_evidence=doc_ids,
            output_summary=(
                f"Extracted "
                f"{len(relationships)} unique "
                f"relationships from "
                f"{total_documents - failures}/"
                f"{total_documents} documents."
            ),
            error_message=(
                f"{failures} document(s) failed "
                f"relationship extraction."
                if failures
                else None
            ),
        )

        # ======================================================
        # RETURN RESULT
        # ======================================================

        return {
            "relationships": relationships
        }

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(
        text: str,
        known_entities: List[str],
    ) -> str:

        entity_text = ", ".join(
            known_entities
        )

        return f"""
You are a forensic relationship extraction assistant
for INVESTCOPS AI.

Your task is to identify relationships that are
EXPLICITLY supported by the investigation evidence.

Known entities extracted by Agent 2:

{entity_text}

Investigation evidence:

{text}

Identify relationships only when the relationship is
supported by the evidence.

For every relationship provide:

- subject
- relationship
- object
- confidence between 0.0 and 1.0

IMPORTANT RULES:

1. Do NOT invent relationships.

2. Do NOT infer relationships that are not supported
   by the evidence.

3. Do NOT create relationships merely because two
   entities appear in the same document.

4. Use only entities supported by the evidence.

5. Keep the relationship short and descriptive.

6. Examples of acceptable relationship names:

   located_at
   mentioned
   contacted
   called
   sent_message_to
   received_message_from
   belongs_to
   associated_with

7. If there are no clearly supported relationships,
   return an empty list.

8. Return ONLY valid JSON.

9. Do not use Markdown.

10. Do not include explanations outside JSON.

Return exactly this structure:

{{
    "relationships": [
        {{
            "subject": "Rahul",
            "relationship": "located_at",
            "object": "Gandhipuram",
            "confidence": 0.95
        }}
    ]
}}
"""