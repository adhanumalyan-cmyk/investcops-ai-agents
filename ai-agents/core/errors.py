"""
Structured exceptions used across the agent framework and services.
"""


class InvestCopsError(Exception):
    """Base application error."""


class ConfigError(InvestCopsError):
    """Invalid or missing configuration."""


class EvidenceValidationError(InvestCopsError):
    """Evidence failed ingestion/validation."""


class UnsupportedEvidenceError(EvidenceValidationError):
    """Evidence type is not supported."""


class EvidenceCorruptError(EvidenceValidationError):
    """Evidence file appears corrupted or unreadable."""


class StorageError(InvestCopsError):
    """File storage failure."""


class AuthError(InvestCopsError):
    """Authentication/authorization failure."""


class AgentExecutionError(InvestCopsError):
    """Agent could not complete processing."""


class InsufficientEvidenceError(AgentExecutionError):
    """Agent cannot proceed: insufficient evidence (-> NEEDS_REVIEW)."""


class GraphError(InvestCopsError):
    """Neo4j graph operation failure."""


class NotFoundError(InvestCopsError):
    """Requested resource does not exist."""


class DuplicateEvidenceError(EvidenceValidationError):
    """Evidence already exists in the case (same SHA-256)."""


class LLMError(InvestCopsError):
    """LLM provider failure (timeout, rate limit, invalid key, ...)."""


class ProcessingError(InvestCopsError):
    """Forensic processing (OCR/transcription/APK/media) failure."""