"""
core/state.py

Shared LangGraph state for INVESTCOPS AI.

This TypedDict is passed between ALL agents (Agent 1 -> Agent 11) in the
pipeline. Every agent reads what it needs from this state and writes its
output back into it. Keep this file identical across all team members'
branches -- it is the shared "contract" of the whole system.
"""

from typing import TypedDict, List, Dict, Optional, Any, Literal
from datetime import datetime


# ---------------------------------------------------------------------------
# Supporting sub-structures (used inside the main state)
# ---------------------------------------------------------------------------

class EvidenceMetadata(TypedDict):
    """Metadata for a single piece of uploaded evidence."""
    evidence_id: str          # e.g. "EVD003"
    file_name: str
    file_type: str            # pdf, image, audio, video, apk, txt, etc.
    file_size: int             # bytes
    source: str                 # e.g. "WhatsApp export", "CCTV", "Phone dump"
    hash: str                    # SHA-256 hash for chain of custody
    uploaded_by: str
    uploaded_at: str              # ISO timestamp string


class ConfidenceScore(TypedDict):
    """Confidence score attached to any AI-generated result."""
    item_id: str                # id of the entity / relationship / event / finding
    category: Literal[
        "entity", "relationship", "timeline", "contradiction", "risk"
    ]
    score: float                  # 0.0 - 1.0
    reason: Optional[str]          # short explanation for the score


class EvidenceReference(TypedDict):
    """Links an AI-generated finding back to the exact evidence that supports it."""
    finding: str                 # human-readable claim, e.g. "Rahul contacted victim at 10:32 PM"
    evidence_id: str               # e.g. "EVD003"
    source: str                      # e.g. "WhatsApp message"
    timestamp: Optional[str]          # when the evidence event occurred
    excerpt: Optional[str]             # short supporting snippet/quote from the evidence


class AgentExecutionMetadata(TypedDict):
    """Execution/audit trail for a single agent run. Used for debugging & demo."""
    agent_name: str               # e.g. "Agent 2 - Entity Extraction"
    model_used: str                 # e.g. "qwen3:8b"
    started_at: str                   # ISO timestamp
    execution_time_seconds: float
    status: Literal["success", "failed", "partial"]
    input_evidence: List[str]          # list of evidence_ids consumed
    output_summary: Optional[str]       # brief description of what was produced
    error_message: Optional[str]         # populated only if status == "failed"


class HumanReviewStatus(TypedDict):
    """Review status for sensitive AI outputs that need human sign-off."""
    item_id: str                  # id of the finding/contradiction/risk/FIR section etc.
    category: Literal[
        "contradiction", "risk_score", "correlated_entity",
        "fir_draft", "major_finding"
    ]
    status: Literal["pending_review", "verified", "rejected"]
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    notes: Optional[str]


# ---------------------------------------------------------------------------
# Main investigation state
# ---------------------------------------------------------------------------

class InvestigationState(TypedDict):
    # --- Core pipeline fields (original) ---
    raw_texts: List[str]
    evidence_metadata: Dict[str, EvidenceMetadata]          # keyed by evidence_id
    cleaned_documents: List[Dict[str, str]]
    entities: Dict[str, List[Dict[str, str]]]
    relationships: List[Dict[str, str]]
    correlated_entities: Dict[str, List[str]]
    timeline: List[Dict[str, str]]
    contradictions: List[Dict[str, str]]
    risk_score: int
    insights_summary: str
    qa_history: List[Dict[str, str]]
    mentor_recommendations: List[str]
    fir_draft: str

    # --- Supporting layers (added) ---
    confidence_scores: List[ConfidenceScore]
    evidence_references: List[EvidenceReference]
    agent_execution_metadata: List[AgentExecutionMetadata]
    human_review_status: List[HumanReviewStatus]


# ---------------------------------------------------------------------------
# Helper: build a fresh, empty state
# ---------------------------------------------------------------------------

def get_initial_state() -> InvestigationState:
    """Returns a fully-initialized, empty InvestigationState.

    Every agent module should be able to run against this without KeyErrors,
    since all keys already exist (with empty/default values).
    """
    return InvestigationState(
        raw_texts=[],
        evidence_metadata={},
        cleaned_documents=[],
        entities={},
        relationships=[],
        correlated_entities={},
        timeline=[],
        contradictions=[],
        risk_score=0,
        insights_summary="",
        qa_history=[],
        mentor_recommendations=[],
        fir_draft="",
        confidence_scores=[],
        evidence_references=[],
        agent_execution_metadata=[],
        human_review_status=[],
    )


# ---------------------------------------------------------------------------
# Small utility helpers agents can reuse (optional, but saves repetition)
# ---------------------------------------------------------------------------

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
    """Appends an AgentExecutionMetadata entry to state in-place.

    Call this at the end of every agent's `run()` method so we always have
    a full audit trail of the pipeline (useful for the demo + debugging).
    """
    execution_time = (datetime.utcnow() - started_at).total_seconds()
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
    category: Literal["entity", "relationship", "timeline", "contradiction", "risk"],
    score: float,
    reason: Optional[str] = None,
) -> None:
    """Appends a ConfidenceScore entry to state in-place."""
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
    """Appends an EvidenceReference entry to state in-place."""
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
        "contradiction", "risk_score", "correlated_entity",
        "fir_draft", "major_finding"
    ],
    notes: Optional[str] = None,
) -> None:
    """Marks an item as pending_review. Call this from Agents 6, 7, 4, 11
    (contradictions, risk, correlation, FIR) whenever they produce a
    sensitive/high-impact output.
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