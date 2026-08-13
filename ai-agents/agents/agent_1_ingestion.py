"""
Agent 1: Evidence Ingestion & Validation.

Real processing: MIME/extension consistency, size limits, SHA-256 presence,
duplicate detection, readability status, source classification. Confidence
and status are derived from the actual records -- never hardcoded.
"""

"""Agent 1: Evidence Ingestion & Validation.

Real processing: MIME/extension consistency, size limits, SHA-256 presence,
duplicate detection, readability status, source classification. Confidence
and status are derived from the actual records -- never hardcoded.
"""

from typing import Any, Dict

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.state import EvidenceRecord, InvestigationState, Provenance, ValidationStatus

MAX_TEXT_CHARS = 150_000  # guard: never analyze gigantic dumps wholesale


class Agent1Ingestion(BaseAgent):
    name = "agent_1_ingestion"
    description = "Evidence Ingestion and Validation"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        if not state.evidence:
            raise InsufficientEvidenceError("No evidence provided for ingestion.")

        valid_mime_by_ext = {
            ".txt": ["text/plain"],
            ".json": ["application/json"],
            ".pdf": ["application/pdf"],
            ".jpg": ["image/jpeg"],
            ".jpeg": ["image/jpeg"],
            ".png": ["image/png"],
            ".mp4": ["video/mp4"],
            ".webm": ["video/webm"],
            ".mp3": ["audio/mpeg"],
            ".wav": ["audio/wav"],
            ".m4a": ["audio/mp4"],
            ".apk": ["application/vnd.android.package-archive"],
            ".html": ["text/html"],
            ".csv": ["text/csv"],
            ".eml": ["message/rfc822", "text/plain"],
            ".zip": ["application/zip"],
        }

        validated: list[EvidenceRecord] = []
        seen_sha: set[str] = {e.sha256 for e in state.validated_evidence if e.sha256}
        provenance: list[Provenance] = []
        warnings: list[str] = []

        for ev in state.evidence:
            rec = ev.model_copy(deep=True)
            rec_warnings: list[str] = []

            ext_mime_ok = True
            for ext, allowed in valid_mime_by_ext.items():
                if rec.file_name.lower().endswith(ext) and rec.mime_type not in allowed:
                    ext_mime_ok = False
                    rec_warnings.append(f"MIME {rec.mime_type} does not match extension {ext}")

            if not ext_mime_ok:
                rec.validation_status = ValidationStatus.NEEDS_REVIEW
            else:
                rec.validation_status = ValidationStatus.VALID

            if rec.size > MAX_TEXT_CHARS and rec.mime_type.startswith("text/"):
                rec_warnings.append(f"Large text file ({rec.size} chars) - will be truncated for analysis")

            if rec.sha256 and len(rec.sha256) == 64:
                if rec.sha256 in seen_sha:
                    rec_warnings.append(f"Duplicate SHA-256 {rec.sha256[:12]}... already validated in this case")
                    rec.validation_status = ValidationStatus.NEEDS_REVIEW
                else:
                    seen_sha.add(rec.sha256)
            else:
                rec_warnings.append("Missing or invalid SHA-256 hash")

            if rec.integrity_status == "CORRUPT":
                rec.validation_status = ValidationStatus.INVALID
                rec_warnings.append("Readability check failed (corrupt file)")

            rec.warnings = rec_warnings
            if rec_warnings:
                warnings.extend(rec_warnings)
                provenance.append(
                    self._provenance(
                        rec.evidence_id,
                        file_name=rec.file_name,
                        excerpt_or_locator=f"warnings: {rec_warnings[:2]}",
                        confidence=0.3,
                    )
                )
            validated.append(rec)

        # Confidence is derived from the real validation outcomes.
        valid_count = sum(1 for v in validated if v.validation_status == ValidationStatus.VALID)
        confidence = round(valid_count / len(validated), 3) if validated else 0.0

        result = {
            "total_submitted": len(state.evidence),
            "validated": valid_count,
            "needs_review": sum(1 for v in validated if v.validation_status == ValidationStatus.NEEDS_REVIEW),
            "invalid": sum(1 for v in validated if v.validation_status == ValidationStatus.INVALID),
            "duplicates": state_duplicates(validated),
            "source_types": sorted({v.source_type.value for v in validated}),
        }
        return {
            "result": result,
            "state_fields": {"validated_evidence": validated, "evidence": validated},
            "confidence": confidence,
            "evidence_references": provenance,
            "warnings": warnings or ["Evidence validated but contains warnings - review recommended."],
            "evidence_ids": [v.evidence_id for v in validated],
        }


def state_duplicates(items: list[EvidenceRecord]) -> list[str]:
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for it in items:
        if it.sha256:
            prev = seen.get(it.sha256)
            if prev is not None:
                dupes.append(f"{it.evidence_id} (matches {prev})")
            else:
                seen[it.sha256] = it.evidence_id
    return dupes