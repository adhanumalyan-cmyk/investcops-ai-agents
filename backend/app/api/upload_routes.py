"""
backend/app/api/upload_routes.py — Evidence upload + AI analysis trigger
"""

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Import existing AI pipeline
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AI_AGENTS_PATH = PROJECT_ROOT / "ai-agents"
sys.path.insert(0, str(AI_AGENTS_PATH))

from intake.case_builder import CaseBuilder
from orchestrator.graph_builder import build_case_pipeline
from core.state import get_initial_state


@router.post("/evidence")
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str = Form("TEST001"),
    investigator: str = Form("investigator"),
    category: str = Form("unknown"),
):
    """
    Upload evidence file → Save to case folder → Run AI pipeline → Return results
    """
    try:
        # 1. Read file content
        content = await file.read()
        
        # 2. Calculate SHA-256 of REAL content
        file_hash = hashlib.sha256(content).hexdigest()
        
        # 3. Save to case folder
        cases_root = AI_AGENTS_PATH / "cases"
        builder = CaseBuilder(case_id=case_id, cases_root=str(cases_root), investigator=investigator)
        
        # 4. Save file to appropriate subfolder
        ext = file.filename.split('.')[-1].lower()
        if ext in ['txt', 'json', 'csv']:
            dest_dir = builder.chat_exports_dir
        elif ext in ['jpg', 'png', 'jpeg', 'gif']:
            dest_dir = builder.media_dir
        else:
            dest_dir = builder.case_dir / "misc"
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_dir / file.filename
        with open(dest_path, "wb") as f:
            f.write(content)
        
        # 5. Register in manifest
        eid = builder._register_evidence(
            file_name=file.filename,
            file_type=ext or "unknown",
            source=category,
            content_hash=file_hash,
            file_size=len(content)
        )
        
        # 6. Add to raw_texts (if text file)
        if ext in ['txt', 'json', 'csv']:
            try:
                text_content = content.decode('utf-8', errors='replace')
                builder.raw_texts.append(f"[{eid}] File: {file.filename}\n{text_content[:5000]}")
            except:
                pass
        
        builder._save_manifest()
        
        # 7. Run AI pipeline
        initial_state = builder.build_initial_state()
        initial_state["case_folder"] = str(builder.case_dir.resolve())
        
        app = build_case_pipeline()
        result = app.invoke(initial_state)
        
        return {
            "success": True,
            "case_id": case_id,
            "evidence_id": eid,
            "file_name": file.filename,
            "hash": file_hash,
            "case_folder": str(builder.case_dir.resolve()),
            "results": {
                "entities": result.get("entities", {}),
                "contradictions": result.get("contradictions", []),
                "risk_score": result.get("risk_score", 0),
                "fir_draft": result.get("fir_draft", "")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))