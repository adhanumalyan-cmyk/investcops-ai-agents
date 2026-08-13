"""Case routes with authorization (RBAC)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.core.exceptions import AuthorizationError, NotFoundError
from app.database.session import get_db
from app.models.models import AuditLog, User
from app.schemas.schemas import CaseCreate, CaseListOut, CaseOut, CaseUpdate, Message
from app.services.cases import create_case, delete_case, get_case, list_cases, update_case

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, AuthorizationError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case_endpoint(
    req: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "INVESTIGATOR", "SUPERVISOR")),
):
    try:
        case = create_case(db, current_user, req.title, req.description)
        db.add(
            AuditLog(
                user_id=current_user.id, user_email=current_user.email,
                action="case_creation", case_id=case.case_id, target_id=case.case_id,
            )
        )
        db.commit()
        db.refresh(case)
        return case
    except Exception as exc:
        raise _handle(exc)


@router.get("", response_model=CaseListOut)
def list_cases_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cases = list_cases(db, current_user)
    return CaseListOut(total=len(cases), cases=[CaseOut.model_validate(c) for c in cases])


@router.get("/{case_id}", response_model=CaseOut)
def get_case_endpoint(
    case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        return CaseOut.model_validate(get_case(db, current_user, case_id))
    except Exception as exc:
        raise _handle(exc)


@router.put("/{case_id}", response_model=CaseOut)
def update_case_endpoint(
    case_id: str, req: CaseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        case = update_case(db, current_user, case_id, title=req.title, description=req.description, status=req.status)
        db.add(
            AuditLog(
                user_id=current_user.id, user_email=current_user.email,
                action="case_update", case_id=case.case_id,
            )
        )
        db.commit()
        db.refresh(case)
        return CaseOut.model_validate(case)
    except Exception as exc:
        raise _handle(exc)


@router.delete("/{case_id}", response_model=Message)
def delete_case_endpoint(
    case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        delete_case(db, current_user, case_id)
        db.add(
            AuditLog(
                user_id=current_user.id, user_email=current_user.email,
                action="case_delete", case_id=case_id,
            )
        )
        db.commit()
        return Message(message=f"Case {case_id} deleted")
    except Exception as exc:
        raise _handle(exc)