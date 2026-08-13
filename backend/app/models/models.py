"""
ORM models: users, cases, evidence, agents, results, audit.

JSON columns use a portable JSON type (works on SQLite + PostgreSQL).
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, utcnow

JSONType = JSON().with_variant(JSON, "sqlite")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="INVESTIGATOR")  # ADMIN | INVESTIGATOR | SUPERVISOR
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    cases: Mapped[list["Case"]] = relationship(back_populates="owner")


class Case(TimestampMixin, Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # OPEN | CLOSED | ARCHIVED
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    owner: Mapped["User"] = relationship(back_populates="cases")
    evidence_items: Mapped[list["Evidence"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        primaryjoin="foreign(Evidence.case_id) == Case.case_id",
    )


class Evidence(TimestampMixin, Base):
    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("case_id", "sha256", name="uq_evidence_case_sha256"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(128), default="")
    source_type: Mapped[str] = mapped_column(String(64), default="OTHER")
    validation_status: Mapped[str] = mapped_column(String(32), default="NEEDS_REVIEW")
    integrity_status: Mapped[str] = mapped_column(String(32), default="NOT_CHECKED")
    storage_key: Mapped[str] = mapped_column(String(512), default="")
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    warnings_json: Mapped[list] = mapped_column(JSONType, default=list)
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING_REVIEW")
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)

    case: Mapped["Case"] = relationship(
        back_populates="evidence_items",
        primaryjoin="foreign(Evidence.case_id) == Case.case_id",
    )
    processing: Mapped[list["EvidenceProcessing"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")


class EvidenceProcessing(TimestampMixin, Base):
    __tablename__ = "evidence_processing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.evidence_id"), index=True, nullable=False)
    processor: Mapped[str] = mapped_column(String(64), nullable=False)  # ocr | transcription | apk | metadata | text
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    output_text: Mapped[str] = mapped_column(Text, default="")
    output_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    evidence: Mapped["Evidence"] = relationship(back_populates="processing")


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    input_evidence_ids: Mapped[list] = mapped_column(JSONType, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[str] = mapped_column(String(128), default="deterministic")
    prompt_version: Mapped[str] = mapped_column(String(32), default="")
    agent_version: Mapped[str] = mapped_column(String(32), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    warnings_json: Mapped[list] = mapped_column(JSONType, default=list)
    error_message: Mapped[str] = mapped_column(Text, default="")


class AgentResultRecord(TimestampMixin, Base):
    """Persisted structured agent output envelope (section 8 envelope)."""

    __tablename__ = "agent_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    envelope_json: Mapped[dict] = mapped_column(JSONType, default=dict)


class EntityRecord(TimestampMixin, Base):
    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint("case_id", "entity_id", name="uq_entity_case_entity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), default="OTHER")
    value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_ids_json: Mapped[list] = mapped_column(JSONType, default=list)
    source_reference: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING_REVIEW")


class RelationshipRecord(TimestampMixin, Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    relationship_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String(64), default="")
    source_entity_value: Mapped[str] = mapped_column(Text, default="")
    source_entity_type: Mapped[str] = mapped_column(String(32), default="")
    relation_type: Mapped[str] = mapped_column(String(64), default="ASSOCIATED_WITH")
    target_entity_id: Mapped[str] = mapped_column(String(64), default="")
    target_entity_value: Mapped[str] = mapped_column(Text, default="")
    target_entity_type: Mapped[str] = mapped_column(String(32), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    supporting_evidence_ids_json: Mapped[list] = mapped_column(JSONType, default=list)
    source_reference: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING_REVIEW")


class TimelineEventRecord(TimestampMixin, Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), default="")
    timestamp_iso: Mapped[str | None] = mapped_column(String(64), default=None)
    event_type: Mapped[str] = mapped_column(String(64), default="OTHER")
    description: Mapped[str] = mapped_column(Text, default="")
    entities_json: Mapped[list] = mapped_column(JSONType, default=list)
    evidence_ids_json: Mapped[list] = mapped_column(JSONType, default=list)
    source_reference: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)


class ContradictionRecord(TimestampMixin, Base):
    __tablename__ = "contradictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    contradiction_id: Mapped[str] = mapped_column(String(64), nullable=False)
    claim_a: Mapped[str] = mapped_column(Text, default="")
    claim_b: Mapped[str] = mapped_column(Text, default="")
    evidence_a_json: Mapped[list] = mapped_column(JSONType, default=list)
    evidence_b_json: Mapped[list] = mapped_column(JSONType, default=list)
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING_REVIEW")


class RiskAssessmentRecord(TimestampMixin, Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(16), default="UNASSESSED")
    payload_json: Mapped[dict] = mapped_column(JSONType, default=dict)


class MentorRecommendationRecord(TimestampMixin, Base):
    __tablename__ = "mentor_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    supporting_evidence_json: Mapped[list] = mapped_column(JSONType, default=list)
    expected_value: Mapped[str] = mapped_column(Text, default="")
    estimated_confidence_improvement: Mapped[float] = mapped_column(Float, default=0.0)


class QAHistoryRecord(TimestampMixin, Base):
    __tablename__ = "qa_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, default="")
    evidence_ids_json: Mapped[list] = mapped_column(JSONType, default=list)
    source_references_json: Mapped[list] = mapped_column(JSONType, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    limitations_json: Mapped[list] = mapped_column(JSONType, default=list)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)


class ReportRecord(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), default="INVESTIGATION")  # INVESTIGATION | FIR
    content_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    generated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING_REVIEW")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    user_email: Mapped[str] = mapped_column(String(255), default="")
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    case_id: Mapped[str] = mapped_column(String(64), index=True, default="")
    target_id: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(32), default="OK")
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)