"""
Evidence service: upload, validation, hashing, dedupe, storage, processing.
All IDs/metadata are persisted to PostgreSQL; bytes go to object storage.
"""

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    DuplicateEvidenceError,
    EvidenceValidationError,
    NotFoundError,
    UnsupportedEvidenceError,
)
from app.core.logging import get_logger
from app.core.utils import safe_filename, sha256_bytes
from app.models.models import AuditLog, Evidence, User
from app.processing.pipeline import EvidenceProcessor, screen_media_authenticity
from app.services.storage import get_storage

logger = get_logger("evidence")

MIME_BY_EXT = {
    ".txt": "text/plain",
    ".json": "application/json",
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".apk": "application/vnd.android.package-archive",
    ".html": "text/html",
    ".csv": "text/csv",
    ".eml": "message/rfc822",
    ".zip": "application/zip",
}

SOURCE_TYPE_HINTS = {
    "whatsapp": "chat_whatsapp",
    "telegram": "chat_telegram",
    "instagram": "chat_instagram",
    "chat": "chat_whatsapp",
    "email": "email",
    ".eml": "email",
    "gps": "gps",
    "location": "gps",
    "bank": "transaction",
    "transaction": "transaction",
    "call": "call_log",
    ".apk": "apk",
}


def guess_mime_type(file_name: str) -> str:
    ext = Path(file_name).suffix.lower()
    return MIME_BY_EXT.get(ext, "application/octet-stream")


def guess_source_type(file_name: str, mime: str) -> str:
    low = file_name.lower()
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    for hint, source in SOURCE_TYPE_HINTS.items():
        if hint in low:
            return source
    return "other"


class EvidenceService:
    """Handles evidence lifecycle. One service instance per request is fine."""

    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.storage = get_storage()

    def upload(self, case_id: str, file_name: str, content: bytes, metadata: dict | None = None) -> Evidence:
        """Validate, hash, dedupe, store and record evidence."""
        safe_name = safe_filename(file_name)
        if not safe_name:
            raise EvidenceValidationError("Invalid filename")

        ext = Path(safe_name).suffix.lower().lstrip(".")
        if ext not in settings.allowed_extensions_list:
            raise UnsupportedEvidenceError(f"File extension .{ext} is not allowed")
        if not content:
            raise EvidenceValidationError("Empty file")

        size_mb = len(content) / (1024 * 1024)
        if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise EvidenceValidationError(
                f"File too large: {size_mb:.1f} MB (limit {settings.MAX_UPLOAD_MB} MB)"
            )

        sha256 = sha256_bytes(content)
        existing = self.db.scalar(
            select(Evidence).where(Evidence.case_id == case_id, Evidence.sha256 == sha256)
        )
        if existing:
            raise DuplicateEvidenceError(
                f"Duplicate evidence: same SHA-256 {sha256[:12]}... already uploaded as {existing.evidence_id}"
            )

        mime = guess_mime_type(safe_name)
        evidence_id = f"E-{uuid.uuid4().hex[:10].upper()}"
        storage_key = f"{case_id}/{evidence_id}/{safe_name}"

        ev = Evidence(
            evidence_id=evidence_id,
            case_id=case_id,
            file_name=safe_name,
            mime_type=mime,
            size=len(content),
            sha256=sha256,
            source_type=guess_source_type(safe_name, mime),
            validation_status="NEEDS_REVIEW",
            integrity_status="HASHED",
            storage_key=storage_key,
            metadata_json=metadata or {},
            uploaded_by=self.user.id,
        )
        self.db.add(ev)
        self.db.flush()

        tmp = Path(settings.LOCAL_STORAGE_DIR) / ".tmp" / f"{uuid.uuid4().hex}.bin"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(content)
        try:
            self.storage.put(storage_key, str(tmp))
        finally:
            tmp.unlink(missing_ok=True)

        # Basic readability check (integrity) without running heavy processors.
        self._basic_readability(ev, content)

        if ev.validation_status != "VALID":
            ev.validation_status = "VALID" if ev.integrity_status == "READABLE" else "NEEDS_REVIEW"

        audit = AuditLog(
            user_id=self.user.id, user_email=self.user.email,
            action="evidence_upload", case_id=case_id, target_id=evidence_id,
            metadata_json={"file_name": safe_name, "size": len(content), "sha256": sha256[:16]},
        )
        self.db.add(audit)
        self.db.commit()
        logger.info("Evidence %s uploaded to case %s", evidence_id, case_id)
        return ev

    def _basic_readability(self, ev: Evidence, content: bytes) -> None:
        """Lightweight corruption/readability screen."""
        magic_checks = {
            "application/pdf": b"%PDF",
            "image/jpeg": b"\xff\xd8\xff",
            "image/png": b"\x89PNG",
            "application/vnd.android.package-archive": b"PK\x03\x04",
            "application/zip": b"PK\x03\x04",
        }
        expected = magic_checks.get(ev.mime_type)
        if expected:
            if content[: len(expected)] == expected:
                ev.integrity_status = "READABLE"
                ev.validation_status = "VALID"
            else:
                ev.integrity_status = "CORRUPT"
                ev.validation_status = "INVALID"
                ev.warnings_json = [f"Magic bytes mismatch for {ev.mime_type}"]
        elif ev.mime_type.startswith(("text/", "application/json", "message/rfc822")):
            try:
                content.decode("utf-8-sig")
                ev.integrity_status = "READABLE"
                ev.validation_status = "VALID"
            except UnicodeDecodeError:
                ev.integrity_status = "CORRUPT"
                ev.validation_status = "INVALID"
                ev.warnings_json = ["File is not valid UTF-8 text"]
        else:
            ev.integrity_status = "READABLE"
            ev.validation_status = "VALID"

    def process(self, evidence_id: str) -> Evidence:
        """Run the evidence processing pipeline for an evidence item."""
        ev = self.db.scalar(select(Evidence).where(Evidence.evidence_id == evidence_id))
        if ev is None:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        dest = f"{settings.LOCAL_STORAGE_DIR}/.tmp/{uuid.uuid4().hex}.bin"
        if not self.storage.get(ev.storage_key, dest):
            raise NotFoundError(f"Evidence file {ev.storage_key} missing from storage")
        try:
            self.db.add(
                AuditLog(
                    user_id=self.user.id, user_email=self.user.email,
                    action="evidence_processing", case_id=ev.case_id, target_id=evidence_id,
                )
            )
            processor = EvidenceProcessor()
            rec = processor.process(self.db, ev, dest)
            if rec.status == "COMPLETED" and ev.mime_type.startswith("image/"):
                ev.metadata_json = {
                    **(ev.metadata_json or {}),
                    "authenticity_screening": screen_media_authenticity(dest),
                }
            self.db.commit()
        finally:
            Path(dest).unlink(missing_ok=True)
        return ev

    def get(self, evidence_id: str) -> Evidence:
        ev = self.db.scalar(select(Evidence).where(Evidence.evidence_id == evidence_id))
        if ev is None:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        return ev

    def list_for_case(self, case_id: str) -> list[Evidence]:
        return list(self.db.scalars(select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at)))

    def delete(self, evidence_id: str) -> None:
        ev = self.get(evidence_id)
        self.storage.delete(ev.storage_key)
        self.db.delete(ev)
        self.db.add(
            AuditLog(
                user_id=self.user.id, user_email=self.user.email,
                action="evidence_delete", case_id=ev.case_id, target_id=evidence_id,
            )
        )
        self.db.commit()