"""
agents/agent_1_ingestion.py

Agent 1 - Evidence Ingestion

Responsibilities:
1. Read raw evidence files from case folder.
2. Calculate SHA-256 hash.
3. Create evidence metadata.
4. Normalize textual content.
5. Produce cleaned_documents for Agent 2.

Agent 1 does NOT perform investigation reasoning.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import hashlib
import json
import csv
import re
import os

from core.state import (
    InvestigationState,
    log_agent_execution,
)
from core.base_agent import BaseAgent


class EvidenceIngestionAgent(BaseAgent):

    AGENT_NAME = "Agent 1 - Evidence Ingestion"

    def __init__(self, model_name: str = "qwen3:8b"):
        super().__init__(
            agent_name=self.AGENT_NAME,
            model_name=model_name,
        )

    # ========================================================
    # MAIN PROCESS
    # ========================================================

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Process evidence files from the case folder.
        Reads files based on state["case_folder"].
        """
        started_at = datetime.utcnow()

        # ------------------------------------------------
        # 1. Determine case folder
        # ------------------------------------------------
        case_folder = state.get("case_folder")
        if not case_folder:
            # Fallback: Try to derive from case_id
            case_id = state.get("case_id", "TEST001")
            from intake.case_builder import CaseBuilder
            builder = CaseBuilder(case_id=case_id)
            case_folder = str(builder.case_dir)
            print(f"📁 Using fallback case folder: {case_folder}")
        
        case_dir = Path(case_folder)
        if not case_dir.exists():
            print(f"⚠️ Case folder not found: {case_dir}")
            return {"cleaned_documents": [], "evidence_metadata": {}}

        # ------------------------------------------------
        # 2. Build list of evidence files to process
        # ------------------------------------------------
        evidence_files = []
        # Walk through subdirectories
        for subdir in ["call_logs", "contacts", "sms", "notifications", "chat_exports", "media", "financial"]:
            sub_path = case_dir / subdir
            if sub_path.exists():
                for f in sub_path.iterdir():
                    if f.is_file():
                        # Skip hidden files and temp files
                        if f.name.startswith('.') or f.name.endswith('.tmp'):
                            continue
                        evidence_files.append({
                            "path": str(f),
                            "source": subdir,
                            "uploaded_by": "intake_system"
                        })

        # Also check root of case folder for device_info.json, manifest.json
        for f in case_dir.glob("*.json"):
            if f.name not in ["manifest.json", "device_info.json"]:
                continue
            evidence_files.append({
                "path": str(f),
                "source": "case_root",
                "uploaded_by": "intake_system"
            })

        if not evidence_files:
            print("⚠️ No evidence files found in case folder.")
            return {"cleaned_documents": [], "evidence_metadata": {}}

        print(f"📂 Found {len(evidence_files)} evidence files in {case_dir}")

        # ------------------------------------------------
        # 3. Process each file
        # ------------------------------------------------
        evidence_metadata: Dict[str, Dict[str, Any]] = {}
        cleaned_documents: List[Dict[str, Any]] = []
        failures = 0
        processed_ids = []

        for idx, evidence in enumerate(evidence_files):
            try:
                file_path = Path(evidence["path"])
                source = evidence.get("source", "Unknown")
                uploaded_by = evidence.get("uploaded_by", "system")

                # ------------------------------------------------
                # Validate file
                # ------------------------------------------------
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

                # ------------------------------------------------
                # Read bytes
                # ------------------------------------------------
                raw_bytes = file_path.read_bytes()
                file_size = len(raw_bytes)
                file_hash = hashlib.sha256(raw_bytes).hexdigest()

                # ------------------------------------------------
                # Evidence ID
                # ------------------------------------------------
                evidence_id = f"EVD{idx + 1:03d}"
                file_type = file_path.suffix.lower().replace(".", "") or "unknown"

                # ------------------------------------------------
                # Metadata
                # ------------------------------------------------
                evidence_metadata[evidence_id] = {
                    "evidence_id": evidence_id,
                    "file_name": file_path.name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "source": source,
                    "hash": file_hash,
                    "uploaded_by": uploaded_by,
                    "uploaded_at": datetime.utcnow().isoformat(),
                }

                # ------------------------------------------------
                # Extract text
                # ------------------------------------------------
                text = self._extract_text(file_path, raw_bytes)

                # ------------------------------------------------
                # Normalize text
                # ------------------------------------------------
                cleaned_text = self._clean_text(text)

                # Limit text size to prevent token overload (optional)
                if len(cleaned_text) > 50000:
                    cleaned_text = cleaned_text[:50000] + "\n... [TRUNCATED]"

                doc_id = f"DOC{idx + 1:03d}"

                cleaned_documents.append({
                    "doc_id": doc_id,
                    "evidence_id": evidence_id,
                    "file_name": file_path.name,
                    "file_type": file_type,
                    "source": source,
                    "cleaned_text": cleaned_text,
                })

                processed_ids.append(evidence_id)

                # Print progress
                print(f"   ✅ Processed: {file_path.name} ({len(cleaned_text)} chars)")

            except Exception as e:
                failures += 1
                print(f"   ❌ Failed: {evidence.get('path')} - {e}")

        # ========================================================
        # Determine execution status
        # ========================================================
        total = len(evidence_files)
        if failures == 0:
            status = "success"
        elif failures < total:
            status = "partial"
        else:
            status = "failed"

        # ========================================================
        # Audit log
        # ========================================================
        log_agent_execution(
            state=state,
            agent_name=self.AGENT_NAME,
            model_used="deterministic-python",
            started_at=started_at,
            status=status,
            input_evidence=processed_ids,
            output_summary=f"Processed {len(cleaned_documents)} of {total} evidence files.",
            error_message=f"{failures} file(s) failed." if failures else None,
        )

        # ========================================================
        # Return state updates
        # ========================================================
        return {
            "evidence_metadata": evidence_metadata,
            "cleaned_documents": cleaned_documents,
        }

    # ========================================================
    # TEXT EXTRACTION — SMART JSON EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_text(file_path: Path, raw_bytes: bytes) -> str:
        """Extract textual content from supported file types."""
        extension = file_path.suffix.lower()

        if extension == ".txt":
            return raw_bytes.decode("utf-8", errors="replace")

        if extension == ".json":
            data = json.loads(raw_bytes.decode("utf-8", errors="replace"))
            
            # --- SMART EXTRACTION (NOT FULL DUMP) ---
            if isinstance(data, list):
                extracted = []
                for i, item in enumerate(data[:500]):  # Limit to 500 entries
                    if isinstance(item, dict):
                        # SMS: extract address and body only
                        if "body" in item and "address" in item:
                            addr = item.get("address", "")
                            body = item.get("body", "")
                            extracted.append(f"[SMS] From/To: {addr} | Body: {body}")
                        # Call log: extract number, name, type
                        elif "number" in item:
                            number = item.get("number", "")
                            name = item.get("name", "")
                            call_type = item.get("type", "")
                            duration = item.get("duration", "")
                            extracted.append(f"[Call] Number: {number} | Name: {name} | Type: {call_type} | Duration: {duration}s")
                        # Contact: extract display_name and number
                        elif "display_name" in item and "data1" in item:
                            name = item.get("display_name", "")
                            number = item.get("data1", "")
                            extracted.append(f"[Contact] Name: {name} | Number: {number}")
                        # Generic: key=value pairs (skip ugly fields)
                        else:
                            parts = []
                            for k, v in item.items():
                                if isinstance(v, (str, int, float, bool)):
                                    if not k.startswith('_') and k not in ['proto', 'subject', 'service_center']:
                                        parts.append(f"{k}={v}")
                            if parts:
                                extracted.append(" | ".join(parts))
                if extracted:
                    total = len(data)
                    summary = "\n".join(extracted)
                    if total > 500:
                        summary += f"\n... ({total - 500} more items truncated)"
                    return summary
                
                # Fallback: compact JSON
                return json.dumps(data[:20], ensure_ascii=False, indent=2)

            elif isinstance(data, dict):
                # For dict (device_info), convert to key=value lines
                lines = [f"{k}: {v}" for k, v in data.items() if not k.startswith('_')]
                return "\n".join(lines) if lines else json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return json.dumps(data, ensure_ascii=False, indent=2)

        if extension == ".csv":
            text = raw_bytes.decode("utf-8", errors="replace")
            rows = csv.reader(text.splitlines())
            return "\n".join(" | ".join(row) for row in rows)

        # If unsupported, return empty string
        return ""

    # ========================================================
    # TEXT CLEANING
    # ========================================================

    @staticmethod
    def _clean_text(text: str) -> str:
        """Conservative text normalization for forensic integrity."""
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove null characters
        text = text.replace("\x00", "")

        # Collapse excessive spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Collapse >2 consecutive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()