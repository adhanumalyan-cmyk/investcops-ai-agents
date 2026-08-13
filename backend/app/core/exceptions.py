"""Reusable backend exceptions mapped to HTTP responses in route handlers."""


class BackendError(Exception):
    status_code = 500
    message = "Internal server error"


class NotFoundError(BackendError):
    status_code = 404
    message = "Resource not found"


class DuplicateError(BackendError):
    status_code = 409
    message = "Resource already exists"


class AuthorizationError(BackendError):
    status_code = 403
    message = "Not authorized"


class ValidationFailedError(BackendError):
    status_code = 422
    message = "Validation failed"


class UnsupportedEvidenceError(ValidationFailedError):
    status_code = 422
    message = "Unsupported evidence type"


class EvidenceValidationError(ValidationFailedError):
    status_code = 422
    message = "Evidence failed validation"


class DuplicateEvidenceError(BackendError):
    status_code = 409
    message = "Duplicate evidence"


class ProcessingError(BackendError):
    status_code = 422
    message = "Evidence processing failed"


class StorageError(BackendError):
    status_code = 500
    message = "File storage failure"


class GraphError(BackendError):
    status_code = 500
    message = "Graph database failure"