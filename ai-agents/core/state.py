##state

"""
core/state.py

Shared LangGraph state for INVESTCOPS AI.

Agent pipeline:

Agent 1 -> Evidence Ingestion
Agent 2 -> Entity Extraction
Agent 3 -> Relationship Extraction
Agent 4 -> Cross-Evidence Correlation
Agent 5 -> Timeline Reconstruction
Agent 6 -> Contradiction Detection

The InvestigationState is the shared contract between all agents.
"""

from typing import TypedDict, List, Dict, Optional, Any, Literal
from datetime import datetime


# ============================================================
# TYPE DEFINITIONS
# ============================================================

EntityType = Literal[
    "person",
    "location",
    "organization",
    "device",
    "phone",
    "email",
    "account",
    "vehicle",
    "ip_address",
    "other",
]


# ============================================================
# EVIDENCE
# ============================================================

class EvidenceMetadata(TypedDict):
    """Metadata belonging to one piece of uploaded evidence."""

    evidence_id: str
    file_name: str
    file_type: str
    file_size: int
    source: str
    hash: str
    uploaded_by: str
    uploaded_at: str


class CleanedDocument(TypedDict):
    """
    Normalized document produced by Agent 1.

    Agent 2 consumes these documents.
    """

    evidence_id: str
    doc_id: str
    file_name: str
    file_type: str
    source: str
    cleaned_text: str


# ============================================================
# ENTITIES
# ============================================================

class Entity(TypedDict):
    """
    Entity extracted from evidence by Agent 2.
    """

    entity_id: str
    name: str
    entity_type: EntityType
    evidence_ids: List[str]
    mentions: List[str]
    confidence: float


# ============================================================
# RELATIONSHIPS
# ============================================================

class Relationship(TypedDict):
    """
    Relationship between two entities.

    Produced primarily by Agent 3.
    """

    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str

    # Evidence supporting the relationship
    evidence_ids: List[str]

    # Example:
    # "Rahul appears to use phone 9876543210 in two evidence sources."
    explanation: str

    confidence: float


# ============================================================
# CROSS-EVIDENCE CORRELATION
# ============================================================

class EvidenceCorrelation(TypedDict):
    """
    Connection discovered between multiple evidence records.

    Produced by Agent 4.
    """

    correlation_id: str

    # Evidence records involved in the correlation
    evidence_ids: List[str]

    # Entities shared between those evidence records
    shared_entity_ids: List[str]

    # Human-readable type:
    # "shared_phone", "shared_person", "shared_location",
    # "shared_device", "multi_entity_match", etc.
    correlation_type: str

    explanation: str

    confidence: float


# ============================================================
# TIMELINE
# ============================================================

class TimelineEvent(TypedDict):
    """
    One chronological event reconstructed from evidence.

    Produced by Agent 5.
    """

    event_id: str

    # ISO timestamp if available.
    # None when evidence does not provide a reliable timestamp.
    timestamp: Optional[str]

    event_type: str
    description: str

    evidence_ids: List[str]
    entity_ids: List[str]

    confidence: float


# ============================================================
# CONTRADICTIONS
# ============================================================

class Contradiction(TypedDict):
    """
    Potential inconsistency detected across evidence.

    Produced by Agent 6.

    IMPORTANT:
    A contradiction does not automatically mean somebody lied.
    It indicates evidence requiring investigator review.
    """

    contradiction_id: str

    description: str

    evidence_ids: List[str]

    # Example:
    # ["Chennai", "Coimbatore"]
    conflicting_values: List[str]

    severity: Literal["low", "medium", "high"]

    confidence: float


# ============================================================
# RISK
# ============================================================

class RiskAssessment(TypedDict):
    """
    Investigation/evidence risk assessment.

    Intended for Agent 7.
    """

    score: float
    level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    factors: List[str]

    supporting_evidence_ids: List[str]

    explanation: str


# ============================================================
# CONFIDENCE
# ============================================================

class ConfidenceScore(TypedDict):
    """
    Generic confidence record for AI-generated results.
    """

    item_id: str

    category: Literal[
        "entity",
        "relationship",
        "correlation",
        "timeline",
        "contradiction",
        "risk",
    ]

    score: float

    reason: Optional[str]


# ============================================================
# EVIDENCE REFERENCES
# ============================================================

class EvidenceReference(TypedDict):
    """
    Connects an AI finding back to its supporting evidence.
    """

    finding: str
    evidence_id: str
    source: str
    timestamp: Optional[str]
    excerpt: Optional[str]


# ============================================================
# AGENT EXECUTION LOG
# ============================================================

class AgentExecutionMetadata(TypedDict):
    """
    Audit/debug information for every agent execution.
    """

    agent_name: str
    model_used: str
    started_at: str
    execution_time_seconds: float

    status: Literal[
        "success",
        "failed",
        "partial",
    ]

    input_evidence: List[str]

    output_summary: Optional[str]

    error_message: Optional[str]


# ============================================================
# HUMAN REVIEW
# ============================================================

class HumanReviewStatus(TypedDict):
    """
    Human-review state for sensitive AI outputs.
    """

    item_id: str

    category: Literal[
        "contradiction",
        "risk_score",
        "correlated_entity",
        "fir_draft",
        "major_finding",
    ]

    status: Literal[
        "pending_review",
        "verified",
        "rejected",
    ]

    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    notes: Optional[str]


# ============================================================
# MAIN INVESTIGATION STATE
# ============================================================

class InvestigationState(TypedDict):
    """
    Shared state passed through the LangGraph investigation pipeline.

    Flow:

    Agent 1
        ↓
    cleaned_documents
        ↓
    Agent 2
        ↓
    entities
        ↓
    Agent 3
        ↓
    relationships
        ↓
    Agent 4
        ↓
    correlations
        ↓
    Agent 5
        ↓
    timeline
        ↓
    Agent 6
        ↓
    contradictions
    """

    # --------------------------------------------------------
    # Agent 1 - Evidence Ingestion
    # --------------------------------------------------------

    raw_texts: List[str]

    evidence_metadata: Dict[str, EvidenceMetadata]

    cleaned_documents: List[CleanedDocument]

    # --------------------------------------------------------
    # Agent 2 - Entity Extraction
    # --------------------------------------------------------

    entities: Dict[str, List[Dict[str, Any]]]

    # --------------------------------------------------------
    # Agent 3 - Relationship Extraction
    # --------------------------------------------------------

    relationships: List[Relationship]

    # --------------------------------------------------------
    # Agent 4 - Cross-Evidence Correlation
    # --------------------------------------------------------

    correlations: List[EvidenceCorrelation]

    # --------------------------------------------------------
    # Agent 5 - Timeline Reconstruction
    # --------------------------------------------------------

    timeline: List[TimelineEvent]

    # --------------------------------------------------------
    # Agent 6 - Contradiction Detection
    # --------------------------------------------------------

    contradictions: List[Contradiction]

    # --------------------------------------------------------
    # Agent 7 - Risk Assessment
    # --------------------------------------------------------

    risk_assessment: Optional[RiskAssessment]

    # --------------------------------------------------------
    # Later agents / future pipeline
    # --------------------------------------------------------

    insights_summary: str

    qa_history: List[Dict[str, Any]]

    mentor_recommendations: List[str]

    fir_draft: str

    # --------------------------------------------------------
    # Shared supporting information
    # --------------------------------------------------------

    confidence_scores: List[ConfidenceScore]

    evidence_references: List[EvidenceReference]

    agent_execution_metadata: List[AgentExecutionMetadata]

    human_review_status: List[HumanReviewStatus]


# ============================================================
# INITIAL STATE
# ============================================================

def get_initial_state() -> InvestigationState:
    """
    Create a fresh InvestigationState.

    This can be used when starting a new LangGraph investigation.
    """

    return InvestigationState(
        raw_texts=[],
        evidence_metadata={},
        cleaned_documents=[],
        entities={},
        relationships=[],
        correlations=[],
        timeline=[],
        contradictions=[],
        risk_assessment=None,
        insights_summary="",
        qa_history=[],
        mentor_recommendations=[],
        fir_draft="",
        confidence_scores=[],
        evidence_references=[],
        agent_execution_metadata=[],
        human_review_status=[],
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def log_agent_execution(
    state: InvestigationState,
    agent_name: str,
    model_used: str,
    started_at: datetime,
    status: Literal["success", "failed", "partial"],
    input_evidence: Optional[List[str]] = None,
    output_summary: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """
    Add one agent execution record to the shared state.
    """

    execution_time = (
        datetime.utcnow() - started_at
    ).total_seconds()

    state["agent_execution_metadata"].append(
        AgentExecutionMetadata(
            agent_name=agent_name,
            model_used=model_used,
            started_at=started_at.isoformat(),
            execution_time_seconds=execution_time,
            status=status,
            input_evidence=input_evidence or [],
            output_summary=output_summary,
            error_message=error_message,
        )
    )


def add_confidence_score(
    state: InvestigationState,
    item_id: str,
    category: Literal[
        "entity",
        "relationship",
        "event",
        "correlation",
        "timeline",
        "contradiction",
        "risk",
    ],
    score: float,
    reason: Optional[str] = None,
) -> None:
    """
    Add a confidence score to the shared state.

    The score is automatically clamped to 0.0 - 1.0.
    """

    score = max(0.0, min(1.0, float(score)))

    state["confidence_scores"].append(
        ConfidenceScore(
            item_id=item_id,
            category=category,
            score=score,
            reason=reason,
        )
    )


def add_evidence_reference(
    state: InvestigationState,
    finding: str,
    evidence_id: str,
    source: str,
    timestamp: Optional[str] = None,
    excerpt: Optional[str] = None,
) -> None:
    """
    Connect an AI-generated finding to its source evidence.
    """

    state["evidence_references"].append(
        EvidenceReference(
            finding=finding,
            evidence_id=evidence_id,
            source=source,
            timestamp=timestamp,
            excerpt=excerpt,
        )
    )


def flag_for_review(
    state: InvestigationState,
    item_id: str,
    category: Literal[
        "contradiction",
        "risk_score",
        "correlated_entity",
        "fir_draft",
        "major_finding",
    ],
    notes: Optional[str] = None,
) -> None:
    """
    Mark a sensitive AI output for human investigator review.
    """

    state["human_review_status"].append(
        HumanReviewStatus(
            item_id=item_id,
            category=category,
            status="pending_review",
            reviewed_by=None,
            reviewed_at=None,
            notes=notes,
        )
    )