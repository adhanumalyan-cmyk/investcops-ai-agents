"""
Agent execution service: bridge between FastAPI, PostgreSQL and the
ai-agents investigation framework.

Every run is fully persisted: AgentRun records, structured AgentResult
envelopes, entities, relationships, timeline, contradictions, risk,
mentor recommendations, Q&A history and FIR draft. Neo4j is synced
after relationship-producing runs.
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AI_AGENTS_DIR = os.path.join(ROOT, "ai-agents")
if AI_AGENTS_DIR not in sys.path:
    sys.path.insert(0, AI_AGENTS_DIR)

from app.core.exceptions import NotFoundError  # noqa: E402
from app.core.logging import get_logger  # noqa: E402
from app.graph.neo4j_client import get_graph_client  # noqa: E402
from app.models.models import (  # noqa: E402
    AgentResultRecord,
    AgentRun,
    AuditLog,
    Case,
    ContradictionRecord,
    EntityRecord,
    Evidence,
    EvidenceProcessing,
    MentorRecommendationRecord,
    QAHistoryRecord,
    RelationshipRecord,
    ReportRecord,
    RiskAssessmentRecord,
    TimelineEventRecord,
    User,
)

logger = get_logger("agent_service")

from core.state import (  # noqa: E402
    Contradiction,
    Entity,
    FIRDraft,
    InvestigationState,
    MentorRecommendation,
    QAExchange,
    Relationship,
    RiskAssessment,
    TimelineEvent,
)

AGENT_IDS = {
    "agent_1_ingestion": "agent_1_ingestion",
    "agent_2_evidence_analysis": "agent_2_evidence_analysis",
    "agent_3_entities": "agent_3_entities",
    "agent_4_relationships": "agent_4_relationships",
    "agent_5_correlate": "agent_5_correlate",
    "agent_6_timeline": "agent_6_timeline",
    "agent_7_contradict": "agent_7_contradict",
    "agent_8_risk": "agent_8_risk",
    "agent_9_insights": "agent_9_insights",
    "agent_10_rag_qa": "agent_10_rag_qa",
    "agent_11_mentor_fir": "agent_11_mentor_fir",
}


def _ensure_case(db: Session, case_id: str) -> Case:
    case = db.scalar(select(Case).where(Case.case_id == case_id))
    if case is None:
        raise NotFoundError(f"Case {case_id} not found")
    return case


def build_state(db: Session, case_id: str) -> InvestigationState:
    """Reconstruct the shared investigation state from PostgreSQL."""
    _ensure_case(db, case_id)
    state = InvestigationState(case_id=case_id)

    ev_rows = list(db.scalars(select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at)))
    for row in ev_rows:
        from core.state import EvidenceRecord

        state.evidence.append(
            EvidenceRecord(
                evidence_id=row.evidence_id,
                file_name=row.file_name,
                mime_type=row.mime_type,
                size=row.size,
                sha256=row.sha256,
                source_type=row.source_type,
                validation_status=row.validation_status,
                integrity_status=row.integrity_status,
                warnings=list(row.warnings_json or []),
                metadata=row.metadata_json or {},
                storage_path=row.storage_key,
                review_status=row.review_status,
            )
        )
        state.validated_evidence = list(state.evidence)  # DB is the source of truth post-validation

    proc_rows = list(
        db.scalars(
            select(EvidenceProcessing)
            .where(EvidenceProcessing.evidence_id.in_([e.evidence_id for e in state.evidence] or [""]))
            .order_by(EvidenceProcessing.created_at)
        )
    )
    by_ev: Dict[str, str] = {}
    for p in proc_rows:
        if p.status == "COMPLETED" and p.output_text:
            by_ev.setdefault(p.evidence_id, p.output_text)
    for e in state.evidence:
        text = by_ev.get(e.evidence_id, "")
        state.raw_texts.append({"evidence_id": e.evidence_id, "file_name": e.file_name, "text": text})
        state.cleaned_documents.append({"evidence_id": e.evidence_id, "file_name": e.file_name, "text": text})

    for row in db.scalars(select(EntityRecord).where(EntityRecord.case_id == case_id)):
        state.entities.append(
            Entity(
                entity_id=row.entity_id,
                entity_type=row.entity_type,
                value=row.value,
                normalized_value=row.normalized_value,
                confidence=row.confidence,
                evidence_id=", ".join(row.evidence_ids_json or []),
                source_reference=row.source_reference,
            )
        )
    for row in db.scalars(select(RelationshipRecord).where(RelationshipRecord.case_id == case_id)):
        state.relationships.append(
            Relationship(
                relationship_id=row.relationship_id,
                source_entity_id=row.source_entity_id,
                source_entity_value=row.source_entity_value,
                source_entity_type=row.source_entity_type,
                relation_type=row.relation_type,
                target_entity_id=row.target_entity_id,
                target_entity_value=row.target_entity_value,
                target_entity_type=row.target_entity_type,
                confidence=row.confidence,
                supporting_evidence_ids=list(row.supporting_evidence_ids_json or []),
                source_reference=row.source_reference,
            )
        )
    for row in db.scalars(select(TimelineEventRecord).where(TimelineEventRecord.case_id == case_id)):
        state.timeline.append(
            TimelineEvent(
                event_id=row.event_id,
                timestamp=row.timestamp,
                timestamp_iso=row.timestamp_iso,
                event_type=row.event_type,
                description=row.description,
                entities=list(row.entities_json or []),
                evidence_ids=list(row.evidence_ids_json or []),
                source_reference=row.source_reference,
                confidence=row.confidence,
            )
        )
    for row in db.scalars(select(ContradictionRecord).where(ContradictionRecord.case_id == case_id)):
        state.contradictions.append(
            Contradiction(
                contradiction_id=row.contradiction_id,
                claim_a=row.claim_a,
                claim_b=row.claim_b,
                evidence_a=list(row.evidence_a_json or []),
                evidence_b=list(row.evidence_b_json or []),
                severity=row.severity,
                confidence=row.confidence,
                explanation=row.explanation,
            )
        )
    risk_row = db.scalar(
        select(RiskAssessmentRecord).where(RiskAssessmentRecord.case_id == case_id).order_by(RiskAssessmentRecord.created_at.desc())
    )
    if risk_row:
        payload = dict(risk_row.payload_json or {})
        valid_keys = RiskAssessment.model_fields.keys()
        payload = {k: v for k, v in payload.items() if k in valid_keys}
        state.risk_score = RiskAssessment(
            risk_score=risk_row.risk_score, risk_level=risk_row.risk_level, **payload
        )
    for row in db.scalars(select(MentorRecommendationRecord).where(MentorRecommendationRecord.case_id == case_id)):
        state.mentor_recommendations.append(
            MentorRecommendation(
                recommendation=row.recommendation,
                reason=row.reason,
                priority=row.priority,
                supporting_evidence=list(row.supporting_evidence_json or []),
                expected_value=row.expected_value,
                estimated_confidence_improvement=row.estimated_confidence_improvement,
            )
        )
    for row in db.scalars(select(QAHistoryRecord).where(QAHistoryRecord.case_id == case_id)):
        state.qa_history.append(
            QAExchange(
                question=row.question,
                answer=row.answer,
                evidence_ids=list(row.evidence_ids_json or []),
                source_references=list(row.source_references_json or []),
                confidence=row.confidence,
                limitations=list(row.limitations_json or []),
            )
        )
    fir_row = db.scalar(
        select(ReportRecord)
        .where(ReportRecord.case_id == case_id, ReportRecord.report_type == "FIR")
        .order_by(ReportRecord.created_at.desc())
    )
    if fir_row:
        state.fir_draft = FIRDraft.model_validate(fir_row.content_json)

    for row in db.scalars(select(AgentResultRecord).where(AgentResultRecord.case_id == case_id)):
        state.agent_results[row.agent_name] = row.envelope_json
    return state


def run_agent(
    db: Session,
    user: User,
    case_id: str,
    agent_name: str,
    question: Optional[str] = None,
) -> Dict[str, Any]:
    """Instantiate, run, persist one agent and return its result envelope."""
    _ensure_case(db, case_id)
    if agent_name not in AGENT_IDS:
        raise NotFoundError(f"Unknown agent: {agent_name}")
    if agent_name != "agent_10_rag_qa":
        question = None

    from agents.registry import get_agent

    state = build_state(db, case_id)
    state_data = state.to_serializable()
    agent = get_agent(agent_name)
    if question is not None:
        agent._question = question

    started = datetime.now()
    new_state_dict = agent.run(state_data)
    finished = datetime.now()
    new_state = InvestigationState.model_validate(new_state_dict)

    envelope = new_state.agent_results.get(agent_name, {})

    # Persist run + results.
    db.add(
        AgentRun(
            case_id=case_id,
            agent_name=agent_name,
            status=envelope.get("status", "FAILED"),
            input_evidence_ids=[e.evidence_id for e in new_state.validated_evidence],
            started_at=started,
            finished_at=finished,
            duration_ms=envelope.get("duration_ms", 0),
            model_used=envelope.get("model_used", "deterministic"),
            prompt_version=envelope.get("prompt_version", ""),
            agent_version=envelope.get("agent_version", ""),
            confidence=envelope.get("confidence", 0.0),
            warnings_json=envelope.get("warnings", []),
            error_message=envelope.get("error_message", ""),
        )
    )
    db.add(
        AgentResultRecord(
            case_id=case_id,
            agent_name=agent_name,
            status=envelope.get("status", "FAILED"),
            envelope_json=envelope,
        )
    )
    db.add(
        AuditLog(
            user_id=user.id,
            user_email=user.email,
            action="agent_execution",
            case_id=case_id,
            target_id=agent_name,
            status=envelope.get("status", "FAILED"),
            metadata_json={"duration_ms": envelope.get("duration_ms"), "confidence": envelope.get("confidence")},
        )
    )
    persist_derived(db, case_id, new_state)
    db.commit()
    logger.info("Agent %s persisted for case %s (status=%s)", agent_name, case_id, envelope.get("status"))

    # Graph sync after relationship-producing runs (best effort).
    if agent_name in ("agent_4_relationships", "agent_5_correlate"):
        _sync_graph(db, case_id, new_state)
    return envelope


def run_pipeline(db: Session, user: User, case_id: str) -> Dict[str, Any]:
    """Run the full LangGraph pipeline and persist the resulting state."""
    _ensure_case(db, case_id)
    from orchestrator.graph_builder import run_full_pipeline

    state = build_state(db, case_id)
    result = run_full_pipeline(state.to_serializable(), case_id)
    final_state = InvestigationState.model_validate(result.get("state", {}))
    statuses = result.get("agent_status", {})

    for agent_name, status in statuses.items():
        envelope = final_state.agent_results.get(agent_name, {})
        db.add(
            AgentRun(
                case_id=case_id,
                agent_name=agent_name,
                status=status,
                input_evidence_ids=[e.evidence_id for e in final_state.validated_evidence],
                started_at=datetime.now(),
                finished_at=datetime.now(),
                duration_ms=envelope.get("duration_ms", 0),
                model_used=envelope.get("model_used", "deterministic"),
                prompt_version=envelope.get("prompt_version", ""),
                agent_version=envelope.get("agent_version", ""),
                confidence=envelope.get("confidence", 0.0),
                warnings_json=envelope.get("warnings", []),
                error_message=envelope.get("error_message", ""),
            )
        )
        db.add(
            AgentResultRecord(
                case_id=case_id,
                agent_name=agent_name,
                status=status,
                envelope_json=envelope,
            )
        )
    db.add(
        AuditLog(
            user_id=user.id,
            user_email=user.email,
            action="pipeline_execution",
            case_id=case_id,
            metadata_json=statuses,
        )
    )
    persist_derived(db, case_id, final_state)
    db.commit()
    _sync_graph(db, case_id, final_state)
    return {
        "case_id": case_id,
        "agent_status": statuses,
        "errors": result.get("errors", []),
        "state": final_state.to_serializable(),
    }


def persist_derived(db: Session, case_id: str, state: InvestigationState) -> None:
    """Replace derived tables for the case with the latest state (upsert-by-table)."""
    if state.entities:
        db.execute(delete(EntityRecord).where(EntityRecord.case_id == case_id))
        for e in state.entities:
            db.add(
                EntityRecord(
                    case_id=case_id,
                    entity_id=e.entity_id,
                    entity_type=e.entity_type,
                    value=e.value,
                    normalized_value=e.normalized_value,
                    confidence=e.confidence,
                    evidence_ids_json=[i.strip() for i in e.evidence_id.split(",") if i.strip()],
                    source_reference=e.source_reference,
                )
            )
    if state.relationships:
        db.execute(delete(RelationshipRecord).where(RelationshipRecord.case_id == case_id))
        for r in state.relationships:
            db.add(
                RelationshipRecord(
                    case_id=case_id,
                    relationship_id=r.relationship_id,
                    source_entity_id=r.source_entity_id,
                    source_entity_value=r.source_entity_value,
                    source_entity_type=r.source_entity_type,
                    relation_type=r.relation_type,
                    target_entity_id=r.target_entity_id,
                    target_entity_value=r.target_entity_value,
                    target_entity_type=r.target_entity_type,
                    confidence=r.confidence,
                    supporting_evidence_ids_json=r.supporting_evidence_ids,
                    source_reference=r.source_reference,
                )
            )
    if state.timeline:
        db.execute(delete(TimelineEventRecord).where(TimelineEventRecord.case_id == case_id))
        for t in state.timeline:
            db.add(
                TimelineEventRecord(
                    case_id=case_id,
                    event_id=t.event_id,
                    timestamp=t.timestamp,
                    timestamp_iso=t.timestamp_iso,
                    event_type=t.event_type,
                    description=t.description,
                    entities_json=t.entities,
                    evidence_ids_json=t.evidence_ids,
                    source_reference=t.source_reference,
                    confidence=t.confidence,
                )
            )
    if state.contradictions:
        db.execute(delete(ContradictionRecord).where(ContradictionRecord.case_id == case_id))
        for c in state.contradictions:
            db.add(
                ContradictionRecord(
                    case_id=case_id,
                    contradiction_id=c.contradiction_id,
                    claim_a=c.claim_a,
                    claim_b=c.claim_b,
                    evidence_a_json=c.evidence_a,
                    evidence_b_json=c.evidence_b,
                    severity=c.severity,
                    confidence=c.confidence,
                    explanation=c.explanation,
                )
            )
    if state.risk_score.risk_factors or state.risk_score.risk_score:
        db.execute(delete(RiskAssessmentRecord).where(RiskAssessmentRecord.case_id == case_id))
        payload = state.risk_score.model_dump()
        payload.pop("risk_score", None)
        payload.pop("risk_level", None)
        db.add(
            RiskAssessmentRecord(
                case_id=case_id,
                risk_score=state.risk_score.risk_score,
                risk_level=state.risk_score.risk_level,
                payload_json=payload,
            )
        )
    if state.mentor_recommendations:
        db.execute(delete(MentorRecommendationRecord).where(MentorRecommendationRecord.case_id == case_id))
        for m in state.mentor_recommendations:
            db.add(
                MentorRecommendationRecord(
                    case_id=case_id,
                    recommendation=m.recommendation,
                    reason=m.reason,
                    priority=m.priority,
                    supporting_evidence_json=m.supporting_evidence,
                    expected_value=m.expected_value,
                    estimated_confidence_improvement=m.estimated_confidence_improvement,
                )
            )
    if state.qa_history:
        db.execute(delete(QAHistoryRecord).where(QAHistoryRecord.case_id == case_id))
        for q in state.qa_history:
            db.add(
                QAHistoryRecord(
                    case_id=case_id,
                    question=q.question,
                    answer=q.answer,
                    evidence_ids_json=q.evidence_ids,
                    source_references_json=q.source_references,
                    confidence=q.confidence,
                    limitations_json=q.limitations,
                )
            )
    if state.fir_draft and (state.fir_draft.facts or state.fir_draft.overview or state.fir_draft.evidence_summary):
        db.execute(
            delete(ReportRecord).where(
                ReportRecord.case_id == case_id, ReportRecord.report_type == "FIR"
            )
        )
        db.add(
            ReportRecord(
                case_id=case_id,
                report_type="FIR",
                content_json=state.fir_draft.model_dump(),
                review_status=state.fir_draft.review_status,
            )
        )


def _sync_graph(db: Session, case_id: str, state: InvestigationState) -> dict:
    client = get_graph_client()
    if not client.enabled:
        return {"enabled": False, "nodes": 0, "edges": 0}
    if not state.entities:
        return {"enabled": True, "nodes": 0, "edges": 0}
    return client.sync(
        case_id,
        [e.model_dump() for e in state.entities],
        [r.model_dump() for r in state.relationships],
    )