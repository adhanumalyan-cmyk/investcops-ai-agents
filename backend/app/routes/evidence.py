"""Evidence routes: upload, list, detail, process, delete."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.exceptions import (
    AuthorizationError,
    DuplicateEvidenceError,
    EvidenceValidationError,
    NotFoundError,
    UnsupportedEvidenceError,
)
from app.database.session import get_db
from app.models.models import Evidence, EvidenceProcessing, User
from app.schemas.schemas import EvidenceDetailOut, EvidenceOut, EvidenceProcessingOut
from app.services.audit import log_action
from app.services.cases import get_case
from app.services.evidence import EvidenceService

router = APIRouter(prefix="/api", tags=["evidence"])


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (AuthorizationError,)):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, (DuplicateEvidenceError,)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, (EvidenceValidationError, UnsupportedEvidenceError)):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/cases/{case_id}/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        get_case(db, current_user, case_id)
        content = await file.read()
        svc = EvidenceService(db, current_user)
        ev = svc.upload(case_id, file.filename or "unnamed", content)
        return EvidenceOut.model_validate(ev)
    except Exception as exc:
        raise _handle(exc)


@router.get("/cases/{case_id}/evidence", response_model=list[EvidenceOut])
def list_evidence(
    case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        get_case(db, current_user, case_id)
        svc = EvidenceService(db, current_user)
        return [EvidenceOut.model_validate(e) for e in svc.list_for_case(case_id)]
    except Exception as exc:
        raise _handle(exc)


@router.get("/evidence/{evidence_id}", response_model=EvidenceDetailOut)
def get_evidence(
    evidence_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        ev = db.scalar(select(Evidence).where(Evidence.evidence_id == evidence_id))
        if ev is None:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        get_case(db, current_user, ev.case_id)
        processing = list(
            db.scalars(select(EvidenceProcessing).where(EvidenceProcessing.evidence_id == evidence_id))
        )
        log_action(db, current_user, "evidence_access", case_id=ev.case_id, target_id=evidence_id)
        db.commit()
        return EvidenceDetailOut(
            **EvidenceOut.model_validate(ev).model_dump(),
            processing=[EvidenceProcessingOut.model_validate(p) for p in processing],
        )
    except Exception as exc:
        raise _handle(exc)


@router.post("/evidence/{evidence_id}/process", response_model=EvidenceDetailOut)
def process_evidence(
    evidence_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        ev = db.scalar(select(Evidence).where(Evidence.evidence_id == evidence_id))
        if ev is None:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        get_case(db, current_user, ev.case_id)
        svc = EvidenceService(db, current_user)
        svc.process(evidence_id)
        db.refresh(ev)
        processing = list(
            db.scalars(select(EvidenceProcessing).where(EvidenceProcessing.evidence_id == evidence_id))
        )
        return EvidenceDetailOut(
            **EvidenceOut.model_validate(ev).model_dump(),
            processing=[EvidenceProcessingOut.model_validate(p) for p in processing],
        )
    except Exception as exc:
        raise _handle(exc)


@router.delete("/evidence/{evidence_id}", response_model=dict)
def delete_evidence(
    evidence_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        ev = db.scalar(select(Evidence).where(Evidence.evidence_id == evidence_id))
        if ev is None:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        get_case(db, current_user, ev.case_id)
        EvidenceService(db, current_user).delete(evidence_id)
        return {"message": f"Evidence {evidence_id} deleted"}
    except Exception as exc:
        raise _handle(exc)