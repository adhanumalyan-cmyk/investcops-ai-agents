"""Reports and audit routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.models.models import AuditLog, ReportRecord, User
from app.schemas.schemas import AuditOut, ReportOut
from app.services.audit import log_action
from app.services.cases import get_case
from app.services.reports import generate_investigation_report, get_fir_draft

router = APIRouter(prefix="/api/cases", tags=["reports"])


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{case_id}/report", response_model=ReportOut)
def investigation_report(
    case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        get_case(db, current_user, case_id)
        content = generate_investigation_report(db, case_id)
        log_action(db, current_user, "report_generation", case_id=case_id, target_id=case_id)
        db.commit()
        return ReportOut(
            case_id=case_id,
            report_type="INVESTIGATION",
            content=content,
            generated_at=content["generated_at"],
            review_status="PENDING_REVIEW",
        )
    except Exception as exc:
        raise _handle(exc)


@router.get("/{case_id}/fir-draft", response_model=ReportOut)
def fir_draft(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        get_case(db, current_user, case_id)
        content = get_fir_draft(db, case_id)
        log_action(db, current_user, "fir_generation", case_id=case_id, target_id=case_id)
        db.commit()
        return ReportOut(
            case_id=case_id,
            report_type="FIR",
            content=content,
            generated_at=content.get("generated_at", ""),
            review_status=content.get("review_status", "PENDING_REVIEW"),
        )
    except Exception as exc:
        raise _handle(exc)


@router.post("/{case_id}/fir-draft/review")
def review_fir_draft(
    case_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Human review action on the FIR draft (VERIFIED / REJECTED / ...)."""
    review_status = str(payload.get("review_status", "")).upper()
    if review_status not in ("PENDING_REVIEW", "VERIFIED", "REJECTED", "REQUIRES_MORE_EVIDENCE"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid review_status")
    try:
        get_case(db, current_user, case_id)
        fir = db.scalar(
            select(ReportRecord)
            .where(ReportRecord.case_id == case_id, ReportRecord.report_type == "FIR")
            .order_by(ReportRecord.created_at.desc())
        )
        if fir is None:
            raise NotFoundError("No FIR draft exists yet")
        fir.review_status = review_status
        content = dict(fir.content_json or {})
        content["review_status"] = review_status
        fir.content_json = content
        log_action(db, current_user, "review_action", case_id=case_id, target_id="fir_draft",
                   metadata_json={"review_status": review_status})
        db.commit()
        return {"case_id": case_id, "review_status": review_status}
    except Exception as exc:
        raise _handle(exc)


@router.get("/{case_id}/audit", response_model=list[AuditOut])
def case_audit(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        get_case(db, current_user, case_id)
    except Exception as exc:
        raise _handle(exc)
    rows = list(
        db.scalars(select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.created_at.desc()))
    )
    return [AuditOut.model_validate(r) for r in rows]