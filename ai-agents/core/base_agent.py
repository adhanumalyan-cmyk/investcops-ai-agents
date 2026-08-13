"""
Base Agent Class
All agents inherit from this class.

Every agent receives the full typed InvestigationState, performs its own
real processing, and returns an updated state together with a structured
AgentResult envelope (section 8 of the spec). Failure handling, logging,
provenance and result envelope creation are centralized here so that no
agent can silently return "fake success".
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.config import load_config
from core.state import (
    AgentResult,
    AgentStatus,
    InvestigationState,
    Provenance,
    utc_now_iso,
)

logger = logging.getLogger("investcops.agents")

_STATUS_FROM_ERROR: Dict[type, AgentStatus] = {}


class AgentExecutionError(Exception):
    """Raised when an agent cannot complete its processing."""


class InsufficientEvidenceError(AgentExecutionError):
    """Raised when an agent cannot proceed due to insufficient evidence."""


class BaseAgent(ABC):
    """Abstract base class for all investigation agents."""

    name: str = "base_agent"
    description: str = "Base agent for investigation"
    version: str = "1.0.0"
    prompt_version: str = "1.0.0"

    def __init__(self) -> None:
        self.config = load_config()
        self.agent_version = self.config.AGENT_VERSION + "." + self.version
        self.logger = logging.getLogger(f"investcops.agents.{self.name}")

    @abstractmethod
    def process(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Execute the agent's core logic.

        Args:
            state: Current investigation state (validated).

        Returns:
            A dict with:
              - "result": the agent's structured output for the envelope
              - "state_fields": dict of state attribute -> value to update
              - "confidence": float in [0,1] (derived, never fabricated)
              - "evidence_references": list[Provenance]
              - "warnings": list[str]
              - "evidence_ids": list[str]

        May raise AgentExecutionError / InsufficientEvidenceError.
        """
        raise NotImplementedError

    def run(self, state: Dict[str, Any] | InvestigationState) -> Dict[str, Any]:
        """
        Execute agent logic with envelope + failure handling.

        Accepts either an InvestigationState instance or a plain dict for
        backward compatibility. Always returns a dict-compatible state.
        """
        started = time.monotonic()
        state_obj = (
            state if isinstance(state, InvestigationState) else InvestigationState.model_validate(state)
        )
        state_obj.touch()

        run_record = {
            "agent_name": self.name,
            "case_id": state_obj.case_id,
            "input_evidence_ids": [e.evidence_id for e in state_obj.validated_evidence],
            "started_at": utc_now_iso(),
            "status": AgentStatus.RUNNING.value,
            "model_used": "deterministic",
            "prompt_version": self.prompt_version,
            "agent_version": self.agent_version,
        }

        try:
            output = self.process(state_obj)
        except InsufficientEvidenceError as exc:
            return self._fail(
                state_obj, run_record, started, exc, status=AgentStatus.NEEDS_REVIEW
            )
        except AgentExecutionError as exc:
            return self._fail(state_obj, run_record, started, exc)
        except Exception as exc:  # never fabricate success on unexpected failures
            self.logger.exception("Agent %s failed with unexpected error", self.name)
            return self._fail(state_obj, run_record, started, exc)

        finished = time.monotonic()
        duration_ms = int((finished - started) * 1000)
        result = AgentResult(
            agent_name=self.name,
            case_id=state_obj.case_id,
            status=AgentStatus.COMPLETED,
            evidence_ids=output.get("evidence_ids", []),
            result=output.get("result", {}),
            confidence=float(output.get("confidence", 0.0)),
            evidence_references=[_as_provenance(p) for p in output.get("evidence_references", [])],
            warnings=output.get("warnings", []),
            created_at=utc_now_iso(),
            agent_version=self.agent_version,
            prompt_version=self.prompt_version,
            model_used=output.get("model_used", "deterministic"),
            duration_ms=duration_ms,
        )
        self.logger.info(
            "Agent %s completed for case %s in %d ms (confidence=%.2f)",
            self.name, state_obj.case_id, duration_ms, result.confidence,
        )

        state_obj.record_result(result)
        for warning in result.warnings:
            state_obj.add_warning(warning)

        for field_name, value in output.get("state_fields", {}).items():
            if hasattr(state_obj, field_name):
                setattr(state_obj, field_name, value)

        run_record.update(
            finished_at=utc_now_iso(),
            duration_ms=duration_ms,
            status=AgentStatus.COMPLETED.value,
            confidence=result.confidence,
            warnings=result.warnings,
        )
        state_obj.add_agent_run(run_record)
        return state_obj.to_serializable()

    def _fail(
        self,
        state_obj: InvestigationState,
        run_record: Dict[str, Any],
        started: float,
        exc: Exception,
        status: Optional[AgentStatus] = None,
    ) -> Dict[str, Any]:
        """Centralized failure path: status FAILED/NEEDS_REVIEW, never fake success."""
        finished = time.monotonic()
        duration_ms = int((finished - started) * 1000)
        effective = status or AgentStatus.FAILED
        message = str(exc)
        self.logger.error(
            "Agent %s %s for case %s: %s",
            self.name, effective.value, state_obj.case_id, message,
        )
        result = AgentResult(
            agent_name=self.name,
            case_id=state_obj.case_id,
            status=effective,
            evidence_ids=[],
            result={},
            confidence=0.0,
            evidence_references=[],
            warnings=[message],
            created_at=utc_now_iso(),
            agent_version=self.agent_version,
            prompt_version=self.prompt_version,
            model_used="deterministic",
            error_message=message,
            duration_ms=duration_ms,
        )
        state_obj.record_result(result)
        state_obj.add_error(self.name, message)
        if effective == AgentStatus.NEEDS_REVIEW:
            state_obj.add_warning("Insufficient evidence available.")
        run_record.update(
            finished_at=utc_now_iso(),
            duration_ms=duration_ms,
            status=effective.value,
            error_message=message,
        )
        state_obj.add_agent_run(run_record)
        return state_obj.to_serializable()

    def _provenance(
        self,
        evidence_id: str,
        source_reference: str = "",
        file_name: str = "",
        page: Optional[int] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        excerpt_or_locator: str = "",
        confidence: float = 0.0,
    ) -> Provenance:
        """Convenience factory for evidence provenance records."""
        return Provenance(
            evidence_id=evidence_id,
            source_reference=source_reference,
            file_name=file_name,
            page=page,
            message_id=message_id,
            timestamp=timestamp,
            excerpt_or_locator=excerpt_or_locator,
            agent_name=self.name,
            confidence=confidence,
        )


def _as_provenance(item: Any) -> Provenance:
    if isinstance(item, Provenance):
        return item
    if isinstance(item, dict):
        return Provenance(**item)
    raise TypeError(f"Unsupported provenance item: {type(item)!r}")


__all__ = [
    "BaseAgent",
    "AgentExecutionError",
    "InsufficientEvidenceError",
    "Provenance",
]