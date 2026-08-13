"""API request/response schemas (Pydantic)."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# --- auth --------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="")
    role: str = Field(default="INVESTIGATOR", pattern="^(ADMIN|INVESTIGATOR|SUPERVISOR)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


# --- cases -------------------------------------------------------------------


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="")


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(OPEN|CLOSED|ARCHIVED)$")


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    title: str
    description: str
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


class CaseListOut(BaseModel):
    total: int
    cases: List[CaseOut]


# --- evidence ----------------------------------------------------------------


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    case_id: str
    file_name: str
    mime_type: str
    size: int
    sha256: str
    source_type: str
    validation_status: str
    integrity_status: str
    review_status: str
    metadata_json: Dict[str, Any] = {}
    warnings_json: List[str] = []
    created_at: datetime


class EvidenceProcessingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    processor: str
    status: str
    output_text: str = ""
    output_json: Dict[str, Any] = {}
    error_message: str = ""
    duration_ms: int = 0
    created_at: datetime


class EvidenceDetailOut(EvidenceOut):
    processing: List[EvidenceProcessingOut] = []


# --- agents ------------------------------------------------------------------

AGENT_NAMES = [
    "agent_1_ingestion",
    "agent_2_evidence_analysis",
    "agent_3_entities",
    "agent_4_relationships",
    "agent_5_correlate",
    "agent_6_timeline",
    "agent_7_contradict",
    "agent_8_risk",
    "agent_9_insights",
    "agent_10_rag_qa",
    "agent_11_mentor_fir",
]


class AgentRunRequest(BaseModel):
    case_id: str
    question: Optional[str] = None  # used by agent_10
    revalidate: bool = False


class AgentResultEnvelope(BaseModel):
    agent_name: str
    case_id: str
    status: str
    evidence_ids: List[str] = []
    result: Dict[str, Any] = {}
    confidence: float = 0.0
    evidence_references: List[Dict[str, Any]] = []
    warnings: List[str] = []
    created_at: str
    agent_version: str = ""
    prompt_version: str = ""
    model_used: str = ""
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None


class PipelineRunRequest(BaseModel):
    case_id: str


class PipelineRunOut(BaseModel):
    case_id: str
    agent_status: Dict[str, str]
    errors: List[Dict[str, Any]]
    state: Dict[str, Any]


# --- reports -----------------------------------------------------------------


class ReportOut(BaseModel):
    case_id: str
    report_type: str
    content: Dict[str, Any]
    generated_at: str
    review_status: str


# --- audit -------------------------------------------------------------------


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_email: str
    action: str
    case_id: str
    target_id: str
    status: str
    metadata_json: Dict[str, Any] = {}
    created_at: datetime


# --- generic -----------------------------------------------------------------


class Message(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


TokenResponse.model_rebuild()