# agents/agent_1_ingestion.py
import hashlib
import os
from typing import Dict, Any, List
from core.state import InvestigationState  # <-- Changed from ..core to core

# Rest of the code same...

def detect_file_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
        '.txt': 'text', '.json': 'json', '.csv': 'csv', '.pdf': 'pdf',
        '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
        '.mp3': 'audio', '.wav': 'audio', '.mp4': 'video',
        '.apk': 'apk', '.zip': 'archive'
    }
    return mapping.get(ext, 'unknown')

def compute_hash_from_content(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def compute_hash_from_file(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def process(state: InvestigationState) -> Dict[str, Any]:
    raw = state.get("raw_evidence", [])
    validated = []
    errors = []

    for item in raw:
        file_path = item.get("file_path")
        text_content = item.get("text_content", "")
        original_name = item.get("original_name", "unknown")

        if file_path and os.path.exists(file_path):
            try:
                file_hash = compute_hash_from_file(file_path)
                file_type = detect_file_type(file_path)
                size = os.path.getsize(file_path)
                validated.append({
                    "file_path": file_path,
                    "hash": file_hash,
                    "size": size,
                    "type": file_type,
                    "original_name": original_name,
                    "status": "validated"
                })
            except Exception as e:
                errors.append(f"Hash failed for {file_path}: {str(e)}")
        
        elif text_content:
            file_hash = compute_hash_from_content(text_content)
            validated.append({
                "file_path": None,
                "hash": file_hash,
                "size": len(text_content),
                "type": "text",
                "original_name": original_name,
                "status": "validated",
                "text_content": text_content
            })
        else:
            errors.append(f"Invalid evidence item: {item}")

    return {
        "validated_evidence": validated,
        "ingestion_errors": errors,
        "current_step": "evidence_analysis_done"
    }