# agents/agent_2_entities.py
import re
import os
from typing import Dict, Any, List
from core.state import InvestigationState  # <-- Changed from ..core to core

# Rest of the code same...
PATTERNS = {
    "phone": r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "username": r'@[a-zA-Z0-9_]+',
    "date": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
}

def extract_entities_from_text(text: str, source_id: str) -> List[Dict]:
    entities = []
    for entity_type, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        for match in matches:
            entities.append({
                "type": entity_type,
                "value": match,
                "source_id": source_id,
                "confidence": 0.85
            })
    return entities

def process(state: InvestigationState) -> Dict[str, Any]:
    validated = state.get("validated_evidence", [])
    all_entities = []

    for item in validated:
        source_id = item.get("hash", "unknown")
        content = ""

        if "text_content" in item and item["text_content"]:
            content = item["text_content"]
        elif item.get("file_path") and os.path.exists(item["file_path"]):
            try:
                with open(item["file_path"], "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                pass

        if content:
            entities = extract_entities_from_text(content, source_id)
            all_entities.extend(entities)

    return {
        "entities": all_entities,
        "current_step": "entity_extraction_done"
    }