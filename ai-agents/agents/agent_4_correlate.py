"""
agents/agent_4_correlate.py

Agent 4 - Cross-Evidence Correlation

Input:
    state["cleaned_documents"]
    state["entities"]
    state["relationships"]

Output:
    {
        "correlations": [
            {
                "evidence_ids": ["EVD001", "EVD002"],
                "shared_entity_ids": ["Rahul", "Gandhipuram"],
                "correlation_type": "multi_entity_match",
                "explanation": "...",
                "confidence": 0.95
            }
        ]
    }

Purpose:
    Identify meaningful connections between different evidence
    documents.

Important:
    This agent must NOT invent correlations.

    A correlation must be supported by evidence that appears
    across multiple documents.
"""

from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
)

from core.base_agent import BaseAgent


# 👇 CLASS NAME FIXED: CorrelationAgent
class CorrelationAgent(BaseAgent):
    """
    Agent 4 identifies correlations across multiple evidence
    documents.

    Input:
        cleaned_documents
        entities
        relationships

    Output:
        correlations
    """

    AGENT_NAME = "Agent 4 - Cross-Evidence Correlation"

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
        # Get cleaned documents
        # ------------------------------------------------------

        cleaned_documents: List[Dict[str, Any]] = state.get(
            "cleaned_documents",
            []
        )

        # ------------------------------------------------------
        # Get entities
        #
        # Agent 2 currently stores entities as:
        #
        # {
        #     "people": [...],
        #     "locations": [...],
        #     "orgs": [...],
        #     "devices": [...]
        # }
        # ------------------------------------------------------

        entities: Dict[str, List[Dict[str, Any]]] = state.get(
            "entities",
            {}
        )

        # ------------------------------------------------------
        # Get relationships from Agent 3
        # ------------------------------------------------------

        relationships: List[Dict[str, Any]] = state.get(
            "relationships",
            []
        )

        # ------------------------------------------------------
        # Empty result
        # ------------------------------------------------------

        empty_correlations: List[Dict[str, Any]] = []

        # ======================================================
        # VALIDATE DOCUMENTS
        # ======================================================

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
                "correlations": empty_correlations
            }

        # ======================================================
        # VALIDATE ENTITIES
        # ======================================================

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
                "correlations": empty_correlations
            }

        # ======================================================
        # BUILD ENTITY → DOCUMENT MAP
        #
        # Example:
        #
        # Rahul
        #     → DOC001
        #     → DOC002
        #
        # Gandhipuram
        #     → DOC001
        #     → DOC002
        # ======================================================

        entity_documents: Dict[str, Set[str]] = {}

        entity_display_names: Dict[str, str] = {}

        entity_types: Dict[str, str] = {}

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

                if not name:
                    continue

                normalized_name = name.lower()

                mentions = entity.get(
                    "mentions",
                    []
                )

                if not isinstance(mentions, list):
                    mentions = []

                if normalized_name not in entity_documents:

                    entity_documents[normalized_name] = set()

                for doc_id in mentions:

                    if doc_id:

                        entity_documents[
                            normalized_name
                        ].add(str(doc_id))

                entity_display_names[
                    normalized_name
                ] = name

                entity_types[
                    normalized_name
                ] = str(entity_type)

        # ======================================================
        # FIND SHARED ENTITIES
        #
        # An entity is cross-evidence relevant if it appears
        # in at least TWO different documents.
        # ======================================================

        shared_entities: Dict[str, Set[str]] = {}

        for entity_name, doc_ids in entity_documents.items():

            if len(doc_ids) >= 2:

                shared_entities[
                    entity_name
                ] = doc_ids

        # ======================================================
        # IF NO SHARED ENTITIES
        # ======================================================

        if not shared_entities:

            doc_ids = [
                document.get(
                    "doc_id",
                    f"DOC{i + 1:03d}"
                )
                for i, document in enumerate(
                    cleaned_documents
                )
            ]

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_name,
                started_at=started_at,
                status="success",
                input_evidence=doc_ids,
                output_summary=(
                    "No cross-evidence correlations found."
                ),
            )

            return {
                "correlations": empty_correlations
            }

        # ======================================================
        # CREATE DOCUMENT PAIRS
        #
        # Example:
        #
        # DOC001 + DOC002
        # ======================================================

        pair_entities: Dict[
            Tuple[str, str],
            List[str]
        ] = {}

        for entity_name, doc_ids in shared_entities.items():

            sorted_docs = sorted(doc_ids)

            for i in range(len(sorted_docs)):

                for j in range(i + 1, len(sorted_docs)):

                    pair = (
                        sorted_docs[i],
                        sorted_docs[j],
                    )

                    if pair not in pair_entities:

                        pair_entities[pair] = []

                    pair_entities[pair].append(
                        entity_name
                    )

        # ======================================================
        # BUILD CORRELATIONS
        # ======================================================

        correlations: List[Dict[str, Any]] = []

        for pair, entity_names in pair_entities.items():

            # --------------------------------------------------
            # Convert normalized names back to display names
            # --------------------------------------------------

            display_entities = []

            for entity_name in entity_names:

                display_name = entity_display_names.get(
                    entity_name,
                    entity_name,
                )

                display_entities.append(
                    display_name
                )

            # --------------------------------------------------
            # Remove duplicates
            # --------------------------------------------------

            display_entities = list(
                dict.fromkeys(
                    display_entities
                )
            )

            # --------------------------------------------------
            # Determine correlation type
            # --------------------------------------------------

            if len(display_entities) >= 2:

                correlation_type = (
                    "multi_entity_match"
                )

            else:

                entity_name = (
                    display_entities[0]
                    if display_entities
                    else ""
                )

                entity_type = entity_types.get(
                    entity_name.lower(),
                    "other",
                )

                if entity_type in {
                    "people",
                    "person",
                }:

                    correlation_type = (
                        "shared_person"
                    )

                elif entity_type in {
                    "locations",
                    "location",
                }:

                    correlation_type = (
                        "shared_location"
                    )

                elif entity_type in {
                    "devices",
                    "device",
                    "phone",
                    "account",
                    "ip_address",
                }:

                    correlation_type = (
                        "shared_device"
                    )

                else:

                    correlation_type = (
                        "shared_entity"
                    )

            # --------------------------------------------------
            # Confidence
            #
            # More shared entities = stronger correlation.
            #
            # 1 shared entity  -> 0.85
            # 2 shared entity  -> 0.95
            # 3+               -> 0.98
            # --------------------------------------------------

            entity_count = len(
                display_entities
            )

            if entity_count >= 3:

                confidence = 0.98

            elif entity_count == 2:

                confidence = 0.95

            else:

                confidence = 0.85

            # --------------------------------------------------
            # Explanation
            # --------------------------------------------------

            entity_text = ", ".join(
                display_entities
            )

            explanation = (
                f"The entities "
                f"{entity_text} "
                f"appear across evidence documents "
                f"{pair[0]} and {pair[1]}."
            )

            # --------------------------------------------------
            # Build correlation record
            # --------------------------------------------------

            correlation = {
                "evidence_ids": list(pair),
                "shared_entity_ids": display_entities,
                "correlation_type": correlation_type,
                "explanation": explanation,
                "confidence": confidence,
            }

            correlations.append(
                correlation
            )

            # --------------------------------------------------
            # Save confidence score
            # --------------------------------------------------

            correlation_id = (
                f"correlation:"
                f"{pair[0]}:"
                f"{pair[1]}"
            )

            add_confidence_score(
                state,
                item_id=correlation_id,
                category="correlation",
                score=confidence,
                reason=(
                    f"Supported by "
                    f"{len(display_entities)} "
                    f"shared entity/entities "
                    f"across 2 evidence documents."
                ),
            )

        # ======================================================
        # EXECUTION LOG
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

        log_agent_execution(
            state,
            agent_name=self.AGENT_NAME,
            model_used=self.model_name,
            started_at=started_at,
            status="success",
            input_evidence=doc_ids,
            output_summary=(
                f"Found "
                f"{len(correlations)} "
                f"cross-evidence correlation(s)."
            ),
        )

        # ======================================================
        # RETURN
        # ======================================================

        return {
            "correlations": correlations
        }