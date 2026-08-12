"""
app/schemas/__init__.py

Pydantic schemas used by the API layer.
"""

from typing import Optional

from pydantic import BaseModel


class FIRConvertRequest(BaseModel):
    text: Optional[str] = None
    content: Optional[str] = None
    system: Optional[str] = None
    mock: Optional[bool] = False


class FIRConvertResponse(BaseModel):
    fir: str
    provider: str
    model: str
    mock: bool
    note: Optional[str] = None


class NotarizeRequest(BaseModel):
    fileName: Optional[str] = "evidence.bin"
    fileSize: Optional[str] = "1.2 MB"
    hash: Optional[str] = ""
    officer: Optional[str] = "NoteNext AI Unit"
    badge: Optional[str] = "NN-042"
    caseId: Optional[str] = "NN-2026-0001"


class VerifyRequest(BaseModel):
    hash: str


class VerifyResponse(BaseModel):
    verified: bool
    record: Optional[dict] = None


class FieldExtractRequest(BaseModel):
    caseId: Optional[str] = "KPC-2026-8941"
    case_id: Optional[str] = None
