# test_my_agents.py
from core.state import InvestigationState
from agents.agent_1_ingestion import process as ingest
from agents.agent_2_entities import process as extract

# Dummy Input
initial_state: InvestigationState = {
    "case_id": "CASE-TEST-001",
    "raw_evidence": [
        {
            "original_name": "whatsapp_chat.txt",
            "text_content": "Hi John, call me at +1 234-567-8900 or email john.doe@example.com. Meet at office on 12/25/2025."
        }
    ],
    "validated_evidence": [],
    "ingestion_errors": [],
    "entities": [],
    "current_step": "",
    "error": None
}

print("🚀 Starting Test...\n")

# Run Agent 1
print("📂 Running Agent 1: Evidence Analysis...")
state_after_agent1 = ingest(initial_state)
merged_state = {**initial_state, **state_after_agent1}

print(f"   ✅ Validated {len(merged_state['validated_evidence'])} items")
if merged_state['ingestion_errors']:
    print(f"   ⚠️ Errors: {merged_state['ingestion_errors']}")

# Run Agent 2
print("\n🔍 Running Agent 2: Entity Extraction...")
state_after_agent2 = extract(merged_state)
merged_state = {**merged_state, **state_after_agent2}

print(f"   ✅ Extracted {len(merged_state['entities'])} entities")
for ent in merged_state['entities']:
    print(f"      - {ent['type']}: {ent['value']}")

print("\n🎉 Test Completed Successfully!")