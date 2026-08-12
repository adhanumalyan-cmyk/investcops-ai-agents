"""
INVESTCOPS AI - Agent Test Suite
Tests Agent 1 (Evidence Ingestion) and Agent 2 (Entity Extraction)
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import agents
from agents.agent_1_ingestion import EvidenceIngestionAgent
from agents.agent_2_entities import EntityExtractionAgent


def test_agents():
    """Main test function for both agents"""
    print("=" * 60)
    print("INVESTCOPS AI - AGENT TEST")
    print("=" * 60)

    # Create initial state
    state = {
        "case_id": "CASE-001",
        "case_name": "Test Case",
        "raw_texts": [],
        "evidence_metadata": {},
        "cleaned_documents": [],
        "entities": {},
        "entity_count": 0,
        "confidence_scores": [],
        "evidence_references": [],
        "agent_execution_metadata": []
    }

    # Add sample investigation evidence
    state["raw_texts"] = [
        """
        WhatsApp Conversation

        11 August 2026 - 10:32 PM

        Rajesh Kumar contacted Suresh through WhatsApp.

        Rajesh's phone number is +91-9876543210.
        His email is rajesh.kumar@gmail.com.

        Suresh's email is suresh@yahoo.com.

        Rajesh said they would meet at Anna Nagar Cafe.

        Rajesh also mentioned his Instagram account
        @rajesh_kumar.

        The meeting was related to a Toyota car.
        """
    ]

    state["evidence_metadata"] = {
        "EVD001": {
            "evidence_id": "EVD001",
            "file_name": "sample_chat.txt",
            "file_type": "txt",
            "file_size": 500,
            "source": "WhatsApp export",
            "hash": "dummy-sha256-for-testing",
            "uploaded_by": "test-investigator",
            "uploaded_at": "2026-08-11T22:00:00",
        }
    }

    print("\nInitial State")
    print("-" * 60)
    print("Evidence:", len(state["evidence_metadata"]))
    print("Raw texts:", len(state["raw_texts"]))

    # ---------------------------------------------------------
    # Agent 1 - Evidence Ingestion
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("AGENT 1 - EVIDENCE ANALYSIS")
    print("=" * 60)

    agent1 = EvidenceIngestionAgent()
    result1 = agent1.process(state)
    state.update(result1)

    print("\nAgent 1 Output:")
    print("Documents:", len(state["cleaned_documents"]))

    for document in state["cleaned_documents"]:
        print("\nEvidence ID:", document.get("evidence_id", "N/A"))
        print("File:", document.get("file_name", "N/A"))
        print("Type:", document.get("file_type", "N/A"))
        print("Route:", document.get("processing_route", "N/A"))
        print("Validation:", document.get("validation_status", "N/A"))

    # ---------------------------------------------------------
    # Agent 2 - Entity Extraction
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("AGENT 2 - ENTITY EXTRACTION")
    print("=" * 60)

    agent2 = EntityExtractionAgent()
    result2 = agent2.process(state)
    state.update(result2)

    print("\nAgent 2 Output:")

    entities = state.get("entities", {})
    total_entities = 0

    if entities:
        for category, entity_list in entities.items():
            print(f"\n{category}:")

            if entity_list:
                for entity in entity_list:
                    print(
                        f"  - {entity.get('value', 'N/A')} "
                        f"(Evidence: {entity.get('evidence_id', 'N/A')})"
                    )
                    total_entities += 1
            else:
                print("  (none)")
    else:
        print("No entities extracted")

    print("\nTotal entities:", total_entities)

    # ---------------------------------------------------------
    # Confidence scores
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("CONFIDENCE SCORES")
    print("=" * 60)

    confidence_scores = state.get("confidence_scores", [])
    if confidence_scores:
        for score in confidence_scores:
            print(
                f"{score.get('item_id', 'N/A')} -> "
                f"{score.get('score', 0)} "
                f"({score.get('category', 'N/A')})"
            )
    else:
        print("No confidence scores available")

    # ---------------------------------------------------------
    # Evidence references
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("EVIDENCE REFERENCES")
    print("=" * 60)

    evidence_refs = state.get("evidence_references", [])
    if evidence_refs:
        for reference in evidence_refs:
            print(
                f"{reference.get('finding', 'N/A')} "
                f"-> {reference.get('evidence_id', 'N/A')}"
            )
    else:
        print("No evidence references available")

    # ---------------------------------------------------------
    # Execution history
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("AGENT EXECUTION HISTORY")
    print("=" * 60)

    execution_history = state.get("agent_execution_metadata", [])
    if execution_history:
        for execution in execution_history:
            print(
                f"{execution.get('agent_name', 'N/A')} | "
                f"{execution.get('status', 'N/A')} | "
                f"{execution.get('execution_time_seconds', 0):.4f}s"
            )
    else:
        print("No execution history available")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\n✅ All agents tested successfully!")


if __name__ == "__main__":
    test_agents()