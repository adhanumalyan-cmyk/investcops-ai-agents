# agents/agent_2_entities.py

"""
AGENT 2: ENTITY EXTRACTION AGENT

Purpose:
- Extract entities from cleaned documents using regex patterns
- Identify: people, phone numbers, emails, usernames, locations, dates, etc.
- Store entities in state for correlation
"""

import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state import InvestigationState
from core.base_agent import BaseAgent


class EntityExtractionAgent(BaseAgent):
    """Agent for extracting entities from evidence using regex patterns"""
    
    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name="Agent 2 - Entity Extraction", model_used=model_used)
        
        # ============================================================
        # REGEX PATTERNS FOR ENTITY EXTRACTION
        # ============================================================
        
        # Phone numbers - Indian format
        self.phone_pattern = re.compile(
            r'(?:(?:\+|0{0,2})91[\s-]?)?'  # Country code
            r'(?:\(?\d{3}\)?[\s-]?)?'       # Area code
            r'(?:\d{3}[\s-]?\d{4})'         # Main number
            r'|'
            r'(?:\+?\d{1,3}[\s-]?)?'        # International
            r'(?:\(?\d{2,3}\)?[\s-]?)?'     # Area code
            r'(?:\d{3,4}[\s-]?\d{4})',      # Main number
            re.IGNORECASE
        )
        
        # Email addresses
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            re.IGNORECASE
        )
        
        # Usernames (@ mentions)
        self.username_pattern = re.compile(
            r'@[a-zA-Z0-9_]+',
            re.IGNORECASE
        )
        
        # URLs
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )
        
        # IP Addresses
        self.ip_pattern = re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        )
        
        # Dates - multiple formats
        self.date_pattern = re.compile(
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'  # DD/MM/YYYY
            r'|'
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}\b'  # DD MMM YYYY
            r'|'
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{2,4}\b'  # MMM DD, YYYY
            r'|'
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',  # DD Month YYYY
            re.IGNORECASE
        )
        
        # Person names - simple patterns
        self.person_pattern = re.compile(
            r'(?:Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Mr|Ms|Mrs|Dr|Prof)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            re.IGNORECASE
        )
        
        # Location - "in/at/near" followed by capitalized words
        self.location_pattern = re.compile(
            r'(?:in|at|near|from|to|located at|address:|office:)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
            re.IGNORECASE
        )
        
        # Vehicle numbers (Indian)
        self.vehicle_pattern = re.compile(
            r'\b[A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,2}\s?[0-9]{4}\b',
            re.IGNORECASE
        )
        
        # Device mentions
        self.device_pattern = re.compile(
            r'\b(?:iPhone|Android|Samsung|OnePlus|Xiaomi|Oppo|Vivo|Google Pixel|MacBook|Dell|HP|Lenovo|ASUS)\s?[A-Z0-9]*\b',
            re.IGNORECASE
        )
    
    # ============================================================
    # PROCESS METHOD
    # ============================================================
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from cleaned documents in the state
        """
        print(f"\n🔍 [{self.agent_name}] Starting...")
        
        # Get cleaned documents from state
        cleaned_docs = state.get("cleaned_documents", [])
        
        if not cleaned_docs:
            print("   ℹ️ No cleaned documents found")
            return {"entities": {}, "entity_count": 0}
        
        print(f"   📥 Processing {len(cleaned_docs)} documents for entities")
        
        # Initialize entity categories
        entities = {
            "people": [],
            "phone_numbers": [],
            "emails": [],
            "usernames": [],
            "urls": [],
            "ip_addresses": [],
            "dates": [],
            "locations": [],
            "vehicles": [],
            "devices": [],
            "organizations": [],
            "accounts": []
        }
        
        # Process each document
        for doc in cleaned_docs:
            doc_id = doc.get("doc_id", "unknown")
            text = doc.get("cleaned_text", doc.get("original_text", ""))
            
            if not text:
                continue
            
            # Extract entities
            doc_entities = self._extract_entities_from_text(text, doc_id)
            
            # Add to categories
            for category, entity_list in doc_entities.items():
                if category in entities:
                    entities[category].extend(entity_list)
        
        # Remove duplicates within each category
        for category in entities:
            entities[category] = self._deduplicate_entities(entities[category])
        
        # Calculate total entities
        total_entities = sum(len(v) for v in entities.values())
        
        # Update state
        state["entities"] = entities
        state["entity_count"] = total_entities
        
        print(f"   📊 Total entities extracted: {total_entities}")
        
        # Print summary
        for category, entity_list in entities.items():
            if entity_list:
                print(f"      {category}: {len(entity_list)}")
        
        return {
            "entities": entities,
            "entity_count": total_entities
        }
    
    # ============================================================
    # ENTITY EXTRACTION METHODS
    # ============================================================
    
    def _extract_entities_from_text(self, text: str, doc_id: str) -> Dict[str, List[Dict]]:
        """Extract entities from text using regex patterns"""
        
        entities = {
            "people": [],
            "phone_numbers": [],
            "emails": [],
            "usernames": [],
            "urls": [],
            "ip_addresses": [],
            "dates": [],
            "locations": [],
            "vehicles": [],
            "devices": [],
            "organizations": [],
            "accounts": []
        }
        
        if not text:
            return entities
        
        # Track seen values to avoid duplicates
        seen = set()
        
        # 1. Extract Phone Numbers
        for match in self.phone_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["phone_numbers"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.9,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 2. Extract Emails
        for match in self.email_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["emails"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.95,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 3. Extract Usernames
        for match in self.username_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["usernames"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.85,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 4. Extract URLs
        for match in self.url_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["urls"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.9,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 5. Extract IP Addresses
        for match in self.ip_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["ip_addresses"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.85,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 6. Extract Dates
        for match in self.date_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["dates"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.8,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 7. Extract Person Names
        for match in self.person_pattern.finditer(text):
            value = match.group(1).strip() if match.groups() else match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["people"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.7,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 8. Extract Locations
        for match in self.location_pattern.finditer(text):
            value = match.group(1).strip() if match.groups() else match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["locations"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.65,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 9. Extract Vehicles
        for match in self.vehicle_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["vehicles"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.75,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # 10. Extract Devices
        for match in self.device_pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                entities["devices"].append({
                    "value": value,
                    "evidence_id": doc_id,
                    "confidence": 0.7,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        return entities
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities based on value"""
        seen = set()
        unique = []
        for entity in entities:
            value = entity.get("value", "").lower()
            if value and value not in seen:
                seen.add(value)
                unique.append(entity)
        return unique
    
    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get context around an entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]