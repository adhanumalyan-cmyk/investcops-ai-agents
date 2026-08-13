"""
Case service: CRUD with authorization.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.models import Case, User


def create_case(db: Session, user: User, title: str, description: str = "") -> Case:
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    case = Case(
        case_id=case_id,
        title=title,
        description=description,
        status="OPEN",
        owner_id=user.id,
    )
    db.add(case)
    return case


def get_case(db: Session, user: User, case_id: str) -> Case:
    case = db.scalar(select(Case).where(Case.case_id == case_id))
    if case is None:
        raise NotFoundError(f"Case {case_id} not found")
    if not _can_access(user, case):
        raise AuthorizationError("You do not have access to this case")
    return case


def list_cases(db: Session, user: User) -> list[Case]:
    stmt = select(Case).order_by(Case.created_at.desc())
    if user.role == "INVESTIGATOR":
        stmt = stmt.where(Case.owner_id == user.id)
    return list(db.scalars(stmt))


def update_case(db: Session, user: User, case_id: str, **fields) -> Case:
    case = get_case(db, user, case_id)
    for key, value in fields.items():
        if value is not None:
            setattr(case, key, value)
    return case


def delete_case(db: Session, user: User, case_id: str) -> None:
    case = get_case(db, user, case_id)
    db.delete(case)


def _can_access(user: User, case: Case) -> bool:
    return user.role in ("ADMIN", "SUPERVISOR") or case.owner_id == user.id