# core/state.py
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict

class InvestigationState(TypedDict):
    # ---------- INPUT: Agent 1 ku dhaan --------------------
    case_id: str
    raw_evidence: List[Dict[str, Any]]

    # ---------- OUTPUT: Agent 1 (Evidence Analysis) ---------
    validated_evidence: List[Dict[str, Any]]
    ingestion_errors: List[str]

    # ---------- OUTPUT: Agent 2 (Entity Extraction) ---------
    entities: List[Dict[str, Any]]

    # ---------- Extra (Optional) ----------------------------
    current_step: str
    error: Optional[str]