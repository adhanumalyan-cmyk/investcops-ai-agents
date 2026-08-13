"""
Audit logging service: every important action is recorded.
"""

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.models import AuditLog, User


def log_action(
    db: Session,
    user: User | None,
    action: str,
    case_id: str = "",
    target_id: str = "",
    status: str = "OK",
    metadata: dict | None = None,
    request: Request | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else "",
        action=action,
        case_id=case_id,
        target_id=target_id,
        status=status,
        metadata_json=metadata or {},
    )
    db.add(entry)
    return entry