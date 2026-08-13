"""Results routes: read derived investigation outputs per case."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db
from app.models.models import (
    ContradictionRecord,
    EntityRecord,
    MentorRecommendationRecord,
    QAHistoryRecord,
    RelationshipRecord,
    RiskAssessmentRecord,
    TimelineEventRecord,
    User,
)
from app.services.agent_service import build_state
from app.services.cases import get_case

router = APIRouter(prefix="/api/cases", tags=["results"])


def _guard(db: Session, user: User, case_id: str) -> None:
    try:
        get_case(db, user, case_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{case_id}/entities")
def list_entities(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    rows = list(db.scalars(select(EntityRecord).where(EntityRecord.case_id == case_id).order_by(EntityRecord.confidence.desc())))
    return {"case_id": case_id, "count": len(rows), "entities": [r.__dict__ | {"evidence_ids": r.evidence_ids_json} for r in rows]}


@router.get("/{case_id}/relationships")
def list_relationships(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    rows = list(db.scalars(select(RelationshipRecord).where(RelationshipRecord.case_id == case_id)))
    return {"case_id": case_id, "count": len(rows), "relationships": [r.__dict__ for r in rows]}


@router.get("/{case_id}/timeline")
def list_timeline(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    rows = list(
        db.scalars(
            select(TimelineEventRecord).where(TimelineEventRecord.case_id == case_id)
        )
    )
    rows.sort(key=lambda r: r.timestamp or "9999")
    return {
        "case_id": case_id,
        "count": len(rows),
        "events": [{"event_id": r.event_id, "timestamp": r.timestamp, "event_type": r.event_type,
                    "description": r.description, "evidence_ids": r.evidence_ids_json, "confidence": r.confidence}
                   for r in rows],
    }


@router.get("/{case_id}/contradictions")
def list_contradictions(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    rows = list(db.scalars(select(ContradictionRecord).where(ContradictionRecord.case_id == case_id)))
    return {"case_id": case_id, "count": len(rows), "contradictions": [
        {"contradiction_id": r.contradiction_id, "claim_a": r.claim_a, "claim_b": r.claim_b,
         "severity": r.severity, "confidence": r.confidence, "explanation": r.explanation,
         "evidence_a": r.evidence_a_json, "evidence_b": r.evidence_b_json, "review_status": r.review_status}
        for r in rows
    ]}


@router.get("/{case_id}/risk")
def get_risk(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    row = db.scalar(
        select(RiskAssessmentRecord).where(RiskAssessmentRecord.case_id == case_id).order_by(RiskAssessmentRecord.created_at.desc())
    )
    if row is None:
        return {"case_id": case_id, "risk_score": None, "note": "Run the risk agent first."}
    payload = dict(row.payload_json or {})
    payload.update({"risk_score": row.risk_score, "risk_level": row.risk_level})
    return {"case_id": case_id, **payload}


@router.get("/{case_id}/explainability")
def get_explainability(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    state = build_state(db, case_id)
    insights = state.insights_summary.model_dump()
    if not insights.get("finding_explanations"):
        env = state.agent_results.get("agent_9_insights", {})
        insights = env.get("result", {})
    return {"case_id": case_id, **insights}


@router.get("/{case_id}/mentor")
def get_mentor(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    rows = list(db.scalars(select(MentorRecommendationRecord).where(MentorRecommendationRecord.case_id == case_id)))
    return {"case_id": case_id, "count": len(rows), "recommendations": [
        {"recommendation": r.recommendation, "reason": r.reason, "priority": r.priority,
         "supporting_evidence": r.supporting_evidence_json,
         "estimated_confidence_improvement": r.estimated_confidence_improvement}
        for r in rows
    ]}


@router.get("/{case_id}/qa")
def get_qa(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _guard(db, user, case_id)
    rows = list(db.scalars(select(QAHistoryRecord).where(QAHistoryRecord.case_id == case_id)))
    return {"case_id": case_id, "count": len(rows), "qa_history": [
        {"question": r.question, "answer": r.answer, "evidence_ids": r.evidence_ids_json,
         "confidence": r.confidence, "asked_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]}