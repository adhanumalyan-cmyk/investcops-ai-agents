"""
Report service: generates the investigation report and FIR draft from live
database state. Never injects fixture conclusions.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.models import (
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
)


def _case_or_404(db: Session, case_id: str) -> Case:
    case = db.scalar(select(Case).where(Case.case_id == case_id))
    if case is None:
        raise NotFoundError(f"Case {case_id} not found")
    return case


def generate_investigation_report(db: Session, case_id: str) -> dict[str, Any]:
    case = _case_or_404(db, case_id)
    evidence = list(db.scalars(select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at)))
    proc = list(
        db.scalars(
            select(EvidenceProcessing)
            .where(EvidenceProcessing.evidence_id.in_([e.evidence_id for e in evidence] or [""]))
        )
    )
    entities = list(db.scalars(select(EntityRecord).where(EntityRecord.case_id == case_id)))
    relationships = list(db.scalars(select(RelationshipRecord).where(RelationshipRecord.case_id == case_id)))
    timeline = list(db.scalars(select(TimelineEventRecord).where(TimelineEventRecord.case_id == case_id)))
    contradictions = list(db.scalars(select(ContradictionRecord).where(ContradictionRecord.case_id == case_id)))
    risk = db.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.case_id == case_id).order_by(RiskAssessmentRecord.created_at.desc()))
    mentors = list(db.scalars(select(MentorRecommendationRecord).where(MentorRecommendationRecord.case_id == case_id)))
    qa = list(db.scalars(select(QAHistoryRecord).where(QAHistoryRecord.case_id == case_id)))
    fir = db.scalar(select(ReportRecord).where(ReportRecord.case_id == case_id, ReportRecord.report_type == "FIR").order_by(ReportRecord.created_at.desc()))
    agent_runs = list(db.scalars(select(AgentRun).where(AgentRun.case_id == case_id).order_by(AgentRun.finished_at)))
    audits = list(db.scalars(select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.created_at)))

    by_ev: dict[str, EvidenceProcessing] = {}
    for p in proc:
        prev = by_ev.get(p.evidence_id)
        if prev is None or (p.created_at or p.id) > (prev.created_at or prev.id):
            by_ev[p.evidence_id] = p

    return {
        "report_type": "INVESTIGATION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case": {
            "case_id": case.case_id,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "owner_id": case.owner_id,
            "created_at": case.created_at.isoformat() if case.created_at else None,
        },
        "evidence_inventory": [
            {
                "evidence_id": e.evidence_id,
                "file_name": e.file_name,
                "mime_type": e.mime_type,
                "size": e.size,
                "sha256": e.sha256,
                "validation_status": e.validation_status,
                "integrity_status": e.integrity_status,
                "source_type": e.source_type,
                "review_status": e.review_status,
            }
            for e in evidence
        ],
        "evidence_processing_summary": [
            {
                "evidence_id": p.evidence_id,
                "processor": p.processor,
                "status": p.status,
                "text_chars": len(p.output_text or ""),
                "error_message": p.error_message,
            }
            for p in {p.evidence_id: p for p in proc}.values()
        ],
        "entity_summary": list(_as_entity_summary(entities)),
        "relationship_summary": [
            {
                "relationship_id": r.relationship_id,
                "source": r.source_entity_value,
                "type": r.relation_type,
                "target": r.target_entity_value,
                "confidence": r.confidence,
            }
            for r in relationships
        ],
        "timeline": [
            {
                "event_id": t.event_id,
                "timestamp": t.timestamp,
                "event_type": t.event_type,
                "description": t.description,
                "evidence_ids": t.evidence_ids_json,
                "confidence": t.confidence,
            }
            for t in sorted(timeline, key=lambda x: x.timestamp or "9999")
        ],
        "contradictions": [
            {
                "contradiction_id": c.contradiction_id,
                "claim_a": c.claim_a,
                "claim_b": c.claim_b,
                "severity": c.severity,
                "confidence": c.confidence,
                "evidence": c.evidence_a_json + c.evidence_b_json,
                "review_status": c.review_status,
            }
            for c in contradictions
        ],
        "risk_assessment": {
            "risk_score": risk.risk_score if risk else None,
            "risk_level": risk.risk_level if risk else None,
            "factors": (risk.payload_json or {}).get("risk_factors", []) if risk else [],
            "calculation_trace": (risk.payload_json or {}).get("calculation_trace", []) if risk else [],
        },
        "recommendations": [
            {
                "recommendation": m.recommendation,
                "reason": m.reason,
                "priority": m.priority,
                "supporting_evidence": m.supporting_evidence_json,
                "estimated_confidence_improvement": m.estimated_confidence_improvement,
            }
            for m in mentors
        ],
        "qa_history": [
            {"question": q.question, "answer": q.answer, "evidence_ids": q.evidence_ids_json}
            for q in qa[-10:]
        ],
        "readiness": fir.content_json.get("readiness") if fir else None,
        "fir_draft": fir.content_json if fir else None,
        "agent_runs": [
            {
                "agent_name": r.agent_name,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "duration_ms": r.duration_ms,
                "confidence": r.confidence,
                "model_used": r.model_used,
                "prompt_version": r.prompt_version,
                "agent_version": r.agent_version,
            }
            for r in agent_runs
        ],
        "audit_metadata": [
            {
                "action": a.action,
                "user": a.user_email,
                "timestamp": a.created_at.isoformat() if a.created_at else None,
                "status": a.status,
                "target_id": a.target_id,
            }
            for a in audits
        ],
        "disclaimer": (
            "Report generated from current case data by AI agents. "
            "All findings require human review before any investigative or legal use."
        ),
    }


def _as_entity_summary(entities: list[EntityRecord]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    samples: dict[str, list[str]] = {}
    for e in entities:
        counts[e.entity_type] = counts.get(e.entity_type, 0) + 1
        samples.setdefault(e.entity_type, []).append(e.normalized_value)
    return [
        {"entity_type": t, "count": c, "samples": list(dict.fromkeys(samples[t]))[:10]}
        for t, c in sorted(counts.items(), key=lambda i: -i[1])
    ]


def get_fir_draft(db: Session, case_id: str) -> dict[str, Any]:
    _case_or_404(db, case_id)
    fir = db.scalar(
        select(ReportRecord)
        .where(ReportRecord.case_id == case_id, ReportRecord.report_type == "FIR")
        .order_by(ReportRecord.created_at.desc())
    )
    if fir is None:
        raise NotFoundError("No FIR draft yet - run the mentor/FIR agent first.")
    return fir.content_json