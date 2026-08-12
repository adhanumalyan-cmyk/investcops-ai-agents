# agents/agent_1_ingestion.py

"""
AGENT 1: EVIDENCE INGESTION & CLEANING

Purpose:
- Validate uploaded evidence
- Detect file type and structure
- Clean and normalize text
- Route evidence to appropriate processing pipeline
"""

import re
import hashlib
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_agent import BaseAgent


class EvidenceIngestionAgent(BaseAgent):
    """Agent for validating and ingesting evidence"""
    
    def __init__(self, model_used: str = "qwen3:8b"):
        # Use the correct parameter name: model_used
        super().__init__(agent_name="Agent 1 - Evidence Analysis", model_used=model_used)
        
        # File signatures for detection
        self.file_signatures = {
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'\xff\xd8\xff': 'image/jpeg',
            b'GIF8': 'image/gif',
            b'%PDF': 'application/pdf',
            b'PK\x03\x04': 'application/zip',
        }
        
        # Extension to type mapping
        self.ext_map = {
            'txt': 'text',
            'json': 'json',
            'csv': 'csv',
            'pdf': 'pdf',
            'png': 'image',
            'jpg': 'image',
            'jpeg': 'image',
            'gif': 'image',
            'mp3': 'audio',
            'wav': 'audio',
            'mp4': 'video',
            'apk': 'apk',
            'eml': 'email',
            'gpx': 'gps',
        }
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw texts and clean them into structured documents
        """
        print(f"\n🔍 [{self.agent_name}] Starting...")
        
        # Get raw texts from state
        raw_texts = state.get("raw_texts", [])
        evidence_metadata = state.get("evidence_metadata", {})
        
        if not raw_texts:
            print("   ℹ️ No raw texts found")
            return {"cleaned_documents": []}
        
        print(f"   📥 Processing {len(raw_texts)} raw texts")
        
        cleaned_documents = []
        
        # Process each raw text
        for idx, raw_text in enumerate(raw_texts):
            # Get evidence ID from metadata or generate one
            ev_id = f"EVD{idx+1:03d}"
            
            # Get metadata for this evidence
            meta = evidence_metadata.get(ev_id, {})
            file_name = meta.get("file_name", f"document_{idx+1}.txt")
            file_type = meta.get("file_type", self._detect_file_type(file_name))
            
            # Clean the text
            cleaned_text = self._clean_text(raw_text)
            
            # Determine processing route
            route = self._determine_route(file_type, cleaned_text)
            
            # Create cleaned document
            cleaned_doc = {
                "doc_id": f"DOC{idx+1:03d}",
                "evidence_id": ev_id,
                "file_name": file_name,
                "file_type": file_type,
                "original_text": raw_text,
                "cleaned_text": cleaned_text,
                "processing_route": route,
                "validation_status": "valid",
                "metadata": meta
            }
            
            cleaned_documents.append(cleaned_doc)
            print(f"   ✅ Processed: {file_name} -> {route}")
        
        # Update state
        state["cleaned_documents"] = cleaned_documents
        
        return {
            "cleaned_documents": cleaned_documents
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Keep important characters for entity extraction
        # Keep: letters, numbers, @, ., -, +, (, ), [, ], {, }, :, ;, ", ', /, %, $, ₹, !, ?
        text = re.sub(r'[^\w\s@.\-+()\[\]{}:;"\'/%$₹!?]', ' ', text)
        
        # Normalize newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def _detect_file_type(self, file_name: str) -> str:
        """Detect file type from extension"""
        ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
        return self.ext_map.get(ext, 'unknown')
    
    def _determine_route(self, file_type: str, text: str) -> str:
        """Determine processing route based on content"""
        if file_type == 'json':
            return 'json_analysis'
        elif file_type == 'csv':
            return 'tabular_analysis'
        elif file_type == 'image':
            return 'image_analysis'
        elif file_type == 'audio':
            return 'audio_analysis'
        elif file_type == 'video':
            return 'video_analysis'
        elif file_type == 'apk':
            return 'apk_analysis'
        elif file_type == 'email':
            return 'email_analysis'
        elif file_type == 'gps':
            return 'gps_analysis'
        else:
            # Check content for keywords
            if text and ('whatsapp' in text.lower() or 'telegram' in text.lower() or 'instagram' in text.lower()):
                return 'chat_analysis'
            return 'text_analysis'