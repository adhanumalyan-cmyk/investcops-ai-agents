"""
Shared investigation state.

Typed, validated, serializable state passed between the 11 investigation
agents. Sensitive/large binary evidence is never stored here -- only
references and processed artifacts.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AgentStatus(str, Enum):
    """Allowed agent execution statuses (section 8 of the spec)."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ValidationStatus(str, Enum):
    """Evidence validation status produced by Agent 1."""

    VALID = "VALID"
    INVALID = "INVALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ReviewStatus(str, Enum):
    """Human review status used across high-impact results (section 34)."""

    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    REQUIRES_MORE_EVIDENCE = "REQUIRES_MORE_EVIDENCE"


def utc_now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    """Generate a short unique identifier with a readable prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class MimeType(str, Enum):
    """Supported evidence MIME types (Agent 1)."""

    TEXT = "text/plain"
    JSON = "application/json"
    PDF = "application/pdf"
    JPEG = "image/jpeg"
    PNG = "image/png"
    MP4 = "video/mp4"
    WEBM = "video/webm"
    MP3 = "audio/mpeg"
    WAV = "audio/wav"
    M4A = "audio/mp4"
    APK = "application/vnd.android.package-archive"
    HTML = "text/html"
    CSV = "text/csv"
    ARCHIVE = "application/zip"


class SourceType(str, Enum):
    """Evidence source classification (Agent 1)."""

    CHAT_WHATSAPP = "chat_whatsapp"
    CHAT_TELEGRAM = "chat_telegram"
    CHAT_INSTAGRAM = "chat_instagram"
    EMAIL = "email"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    GPS = "gps"
    TRANSACTION = "transaction"
    DEVICE = "device"
    APK = "apk"
    CALL_LOG = "call_log"
    OTHER = "other"


class Provenance(BaseModel):
    """Evidence provenance for an AI finding (section 9)."""

    evidence_id: str = Field(description="Evidence record that produced this finding")
    source_reference: str = Field(default="", description="Locator inside the evidence")
    file_name: str = Field(default="")
    page: Optional[int] = None
    message_id: Optional[str] = None
    timestamp: Optional[str] = None
    excerpt_or_locator: str = Field(default="", description="Short excerpt or line number")
    agent_name: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def model_dump_compact(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class AgentResult(BaseModel):
    """Common structured output envelope for every agent (section 8)."""

    agent_name: str
    case_id: str
    status: AgentStatus = AgentStatus.COMPLETED
    evidence_ids: List[str] = Field(default_factory=list)
    result: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Derived, not fabricated")
    evidence_references: List[Provenance] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    agent_version: str = Field(default="")
    prompt_version: str = Field(default="")
    model_used: str = Field(default="deterministic")
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class EvidenceRecord(BaseModel):
    """Evidence item submitted for ingestion (Agent 1 input)."""

    evidence_id: str = Field(default_factory=lambda: new_id("E"))
    file_name: str
    mime_type: str = "application/octet-stream"
    size: int = Field(default=0, ge=0)
    sha256: str = Field(default="")
    source_type: SourceType = SourceType.OTHER
    validation_status: ValidationStatus = ValidationStatus.NEEDS_REVIEW
    integrity_status: str = "NOT_CHECKED"
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    storage_path: str = Field(default="", description="Internal storage reference, never a raw user path")
    uploaded_at: str = Field(default_factory=utc_now_iso)
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW


class EvidenceAnalysisResult(BaseModel):
    """Agent 2 output for one evidence item."""

    evidence_id: str
    summary: str = ""
    key_findings: List[str] = Field(default_factory=list)
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    indicators: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class Entity(BaseModel):
    """Entity extracted by Agent 3."""

    entity_id: str = Field(default_factory=lambda: new_id("ENT"))
    entity_type: str = "OTHER"
    value: str
    normalized_value: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_id: str = ""
    source_reference: str = ""
    frequency: int = Field(default=1, ge=1)
    first_seen: str = ""
    last_seen: str = ""


class Relationship(BaseModel):
    """Relationship identified by Agent 4."""

    relationship_id: str = Field(default_factory=lambda: new_id("REL"))
    source_entity_id: str = ""
    source_entity_value: str = ""
    source_entity_type: str = ""
    relation_type: str = "ASSOCIATED_WITH"
    target_entity_id: str = ""
    target_entity_value: str = ""
    target_entity_type: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    source_reference: str = ""
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW


class CorrelationMatch(BaseModel):
    """Agent 5 correlation between two entities across evidence."""

    correlation_id: str = Field(default_factory=lambda: new_id("CORR"))
    entity_a_id: str = ""
    entity_a_value: str = ""
    entity_b_id: str = ""
    entity_b_value: str = ""
    match_type: str = "possible_match"
    match_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    explanation: str = ""


class TimelineEvent(BaseModel):
    """Agent 6 timeline event."""

    event_id: str = Field(default_factory=lambda: new_id("EVT"))
    timestamp: str = ""  # ISO-8601 when parsed, else raw text
    timestamp_iso: Optional[str] = None
    event_type: str = "OTHER"
    description: str = ""
    entities: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    source_reference: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Contradiction(BaseModel):
    """Agent 7 contradiction between two claims/evidence."""

    contradiction_id: str = Field(default_factory=lambda: new_id("CON"))
    claim_a: str = ""
    claim_b: str = ""
    evidence_a: List[str] = Field(default_factory=list)
    evidence_b: List[str] = Field(default_factory=list)
    severity: str = "MEDIUM"  # LOW | MEDIUM | HIGH
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW


class RiskFactor(BaseModel):
    """One weighted, traceable factor contributing to the risk score."""

    factor: str
    weight: float
    score_contribution: float
    evidence_ids: List[str] = Field(default_factory=list)
    basis: str = ""


class RiskAssessment(BaseModel):
    """Agent 8 output. Deterministic, reproducible."""

    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_level: str = "UNASSESSED"  # LOW | MEDIUM | HIGH
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    calculation_trace: List[str] = Field(default_factory=list)


class FindingExplanation(BaseModel):
    """Agent 9 explanation of one finding."""

    what: str = ""
    why_it_matters: str = ""
    evidence_used: List[str] = Field(default_factory=list)
    entity_contribution: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty: str = ""
    limitations: List[str] = Field(default_factory=list)


class InsightsSummary(BaseModel):
    """Agent 9 output."""

    summary: str = ""
    finding_explanations: List[FindingExplanation] = Field(default_factory=list)
    evidence_contributions: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=utc_now_iso)


class QAExchange(BaseModel):
    """Agent 10 Q&A exchange. Never fabricated; grounded in case state."""

    question: str = ""
    answer: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)
    asked_at: str = Field(default_factory=utc_now_iso)


class MentorRecommendation(BaseModel):
    """Agent 11 mentor recommendation."""

    recommendation: str = ""
    reason: str = ""
    priority: str = "MEDIUM"  # LOW | MEDIUM | HIGH
    supporting_evidence: List[str] = Field(default_factory=list)
    expected_value: str = ""
    estimated_confidence_improvement: float = Field(default=0.0, ge=0.0, le=1.0)


class ReadinessAssessment(BaseModel):
    """Agent 11 evidence readiness assessment."""

    ready_for_review: bool = False
    readiness_score: float = Field(default=0.0, ge=0.0, le=100.0)
    available_evidence: int = 0
    missing_evidence: List[str] = Field(default_factory=list)
    unresolved_contradictions: int = 0
    chain_of_custody_ok: bool = False
    validation_ok: bool = False
    expert_validation_status: str = "NOT_REVIEWED"
    legal_admissibility_claim: str = (
        "This system does not determine legal admissibility. "
        "A qualified legal/forensic expert must review the evidence."
    )
    notes: List[str] = Field(default_factory=list)


class FIRDraft(BaseModel):
    """Agent 11 FIR draft. Human review required."""

    fir_number: str = ""
    case_id: str = ""
    complainant: str = ""
    accused: str = ""
    date_of_occurrence: str = ""
    place_of_occurrence: str = ""
    overview: str = ""
    facts: List[Dict[str, Any]] = Field(default_factory=list)  # {statement, evidence_ids, source_reference}
    evidence_summary: List[str] = Field(default_factory=list)
    legal_notes: List[str] = Field(default_factory=list)
    disclaimer: str = "AI-GENERATED DRAFT - HUMAN REVIEW REQUIRED - NOT A LEGAL DOCUMENT"
    generated_at: str = Field(default_factory=utc_now_iso)
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW


class InvestigationState(BaseModel):
    """
    Shared, typed, validated state for the investigation workflow.

    Only references and processed artifacts are stored -- never raw binaries.
    """

    case_id: str = ""
    case_title: str = ""
    case_description: str = ""

    # Evidence pipeline (Agent 1 -> Agent 2)
    evidence: List[EvidenceRecord] = Field(default_factory=list)
    validated_evidence: List[EvidenceRecord] = Field(default_factory=list)
    raw_texts: List[Dict[str, Any]] = Field(default_factory=list)
    cleaned_documents: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_analyses: List[EvidenceAnalysisResult] = Field(default_factory=list)

    # Entities and relationships (Agent 3 -> Agent 5)
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    correlated_entities: List[CorrelationMatch] = Field(default_factory=list)

    # Investigation outputs (Agents 6-9)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    risk_score: RiskAssessment = Field(default_factory=RiskAssessment)
    insights_summary: InsightsSummary = Field(default_factory=InsightsSummary)
    explanations: List[FindingExplanation] = Field(default_factory=list)

    # Q&A and mentoring (Agents 10-11)
    qa_history: List[QAExchange] = Field(default_factory=list)
    mentor_recommendations: List[MentorRecommendation] = Field(default_factory=list)
    readiness: ReadinessAssessment = Field(default_factory=ReadinessAssessment)
    fir_draft: FIRDraft = Field(default_factory=FIRDraft)

    # Tracking
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    agent_runs: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

    def to_serializable(self) -> Dict[str, Any]:
        """Serialize to JSON-safe dict (for persistence/API)."""
        return self.model_dump(mode="json")

    def touch(self) -> None:
        self.updated_at = utc_now_iso()

    def add_error(self, agent_name: str, message: str, detail: Dict[str, Any] | None = None) -> None:
        self.errors.append(
            {"agent_name": agent_name, "message": message, "detail": detail or {}, "at": utc_now_iso()}
        )
        self.touch()

    def add_warning(self, warning: str) -> None:
        if warning and warning not in self.warnings:
            self.warnings.append(warning)
            self.touch()

    def add_agent_run(self, run: Dict[str, Any]) -> None:
        self.agent_runs.append(run)
        self.touch()

    def record_result(self, result: AgentResult) -> None:
        self.agent_results[result.agent_name] = result.to_dict()
        self.touch()


def state_from_dict(data: Dict[str, Any]) -> InvestigationState:
    """Build a validated InvestigationState from a plain dict (API/service boundary)."""
    return InvestigationState.model_validate(data)