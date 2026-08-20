"""
quick_test.py — Fast test with test_data/ folder
"""

import sys
import os
import json
import shutil
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intake.adb_fetch import sha256_of_text
from agents.agent_1_ingestion import EvidenceIngestionAgent
from agents.agent_2_entities import EntityExtractionAgent

TEST_DATA_DIR = Path(__file__).parent / "test_data"
CASES_ROOT = Path(__file__).parent / "cases"

# --- Prepare case folder with test_data files ---
def prepare_case_folder(case_id: str = "QUICK_TEST"):
    case_dir = CASES_ROOT / f"CASE_{case_id}"
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy test files to appropriate subdirectories
    # WhatsApp/Telegram/Instagram -> chat_exports/
    chat_dir = case_dir / "chat_exports"
    chat_dir.mkdir(exist_ok=True)
    for fname in ["whatsapp_chat.txt", "telegram_chat.txt", "instagram_dm.txt"]:
        src = TEST_DATA_DIR / fname
        if src.exists():
            shutil.copy2(src, chat_dir / fname)
    
    # call_log.json -> call_logs/
    call_dir = case_dir / "call_logs"
    call_dir.mkdir(exist_ok=True)
    src = TEST_DATA_DIR / "call_log.json"
    if src.exists():
        shutil.copy2(src, call_dir / "call_log.json")
    
    return case_dir

# --- Build state with all required keys ---
def build_state(case_id: str = "QUICK_TEST"):
    case_dir = prepare_case_folder(case_id)
    
    state = {
        "case_id": case_id,
        "case_folder": str(case_dir),
        "raw_texts": [],  # Will be filled by Agent 1 from files
        "evidence_metadata": {},
        "cleaned_documents": [],
        "entities": {},
        "relationships": [],
        "correlations": [],
        "timeline": [],
        "contradictions": [],
        "risk_assessment": None,
        "insights_summary": "",
        "qa_history": [],
        "mentor_recommendations": [],
        "fir_draft": "",
        "confidence_scores": [],
        "evidence_references": [],
        "agent_execution_metadata": [],  # 👈 ADDED
        "human_review_status": [],
    }
    return state

# --- Main test ---
def main():
    print("=" * 60)
    print("🔍 QUICK TEST: Agent 1 + Agent 2 (Using test_data/)")
    print("=" * 60)
    
    # Build state with case folder
    state = build_state("QUICK_TEST")
    print(f"📂 Case folder: {state['case_folder']}")
    
    # Agent 1
    print("\n🧹 AGENT 1: Evidence Ingestion")
    agent1 = EvidenceIngestionAgent()
    result1 = agent1.process(state)
    state.update(result1)
    print(f"   ✅ Cleaned {len(state.get('cleaned_documents', []))} documents")
    
    if not state.get("cleaned_documents"):
        print("⚠️ No documents cleaned. Check if test_data files exist and are placed correctly.")
        return
    
    # Agent 2
    print("\n🔍 AGENT 2: Entity Extraction")
    agent2 = EntityExtractionAgent()
    try:
        result2 = agent2.process(state)
        state.update(result2)
    except Exception as e:
        print(f"❌ Agent 2 failed: {e}")
        return
    
    print("\n📊 RESULTS:")
    entities = state.get("entities", {})
    if entities:
        for cat, items in entities.items():
            names = [item.get("name", "N/A") for item in items[:5]]
            print(f"   {cat}: {len(items)} items → {names[:3]}")
    else:
        print("   No entities extracted.")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()