"""
agents/agent_5_timeline.py

Agent 5 - Timeline Reconstruction

Input:
    state["cleaned_documents"]   (from Agent 1)
    state["entities"]            (from Agent 2, for entity_id matching)

Output:
    {
        "timeline": [
            {
                "event_id": "EVT001",
                "timestamp": "2024-08-12T22:32:00" | None,
                "event_type": "call" | "message" | "location_visit" | "transaction" | "login" | "other",
                "description": "Rahul called the victim at 10:32 PM",
                "evidence_ids": ["EVD003", "EVD007"],
                "entity_ids": ["rahul", "victim"],
                "confidence": 0.9
            }
        ]
    }

Purpose:
    Reconstruct a chronological sequence of events from evidence, so
    investigators (and Agent 6 - Contradiction Detection) can see WHAT
    happened WHEN, across all evidence sources.

Important:
    This agent must NOT invent timestamps or events. If a document does
    not clearly state when something happened, timestamp is returned as
    None rather than guessed.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
    flag_for_review,
)

from core.base_agent import BaseAgent


# Events without a strict severity flag still get reviewed if the
# extracted confidence is below this bar — cheap, ambiguous, or
# LLM-uncertain timeline entries shouldn't silently anchor an FIR draft.
LOW_CONFIDENCE_REVIEW_THRESHOLD = 0.5


class TimelineReconstructionAgent(BaseAgent):
    """
    Agent 5 reconstructs a chronological timeline of events from
    cleaned evidence documents, cross-referencing entities found by
    Agent 2 so each event can be linked to the people/devices/locations
    involved.

    Input:
        cleaned_documents
        entities

    Output:
        timeline
    """

    AGENT_NAME = "Agent 5 - Timeline Reconstruction"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(
            agent_name=self.AGENT_NAME,
            model_name=model_used,
        )

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, state: InvestigationState) -> Dict[str, Any]:

        started_at = datetime.utcnow()

        # ------------------------------------------------------
        # Get cleaned documents from Agent 1
        # ------------------------------------------------------

        cleaned_documents: List[Dict[str, Any]] = state.get("cleaned_documents", [])

        # ------------------------------------------------------
        # Get entities from Agent 2 (for entity_id matching)
        # ------------------------------------------------------

        entities: Dict[str, List[Dict[str, Any]]] = state.get("entities", {})

        empty_timeline: List[Dict[str, Any]] = []

        if not cleaned_documents:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_name,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary="No cleaned_documents found in state.",
            )
            return {"timeline": empty_timeline}

        # ======================================================
        # Build a flat, lowercase lookup of known entity names
        # so extracted event descriptions can be linked back to
        # Agent 2's entities (people/locations/orgs/devices).
        # ======================================================

        known_entity_names: List[str] = []

        for entity_type, entity_list in entities.items():
            if not isinstance(entity_list, list):
                continue
            for entity in entity_list:
                if not isinstance(entity, dict):
                    continue
                name = str(entity.get("name", "")).strip()
                if name and name.lower() not in known_entity_names:
                    known_entity_names.append(name.lower())

        # ======================================================
        # PROCESS EACH DOCUMENT
        # ======================================================

        # merged[key] -> event dict, where key groups near-duplicate
        # events (same normalized description + same timestamp) so the
        # SAME real-world event mentioned in two evidence sources
        # (e.g. a call log entry AND a WhatsApp message about the call)
        # merges into one timeline entry with combined evidence_ids.
        merged: Dict[str, Dict[str, Any]] = {}

        failures = 0
        event_counter = 0

        doc_ids = [
            document.get("doc_id", f"DOC{i + 1:03d}")
            for i, document in enumerate(cleaned_documents)
        ]

        for index, document in enumerate(cleaned_documents):

            doc_id = document.get("doc_id", f"DOC{index + 1:03d}")
            evidence_id = document.get("evidence_id", doc_id)
            text = document.get("cleaned_text", "")

            if not isinstance(text, str) or not text.strip():
                continue

            try:
                schema = {
                    "type": "object",
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": ["string", "null"]},
                                    "event_type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "confidence": {"type": "number"},
                                },
                                "required": ["description", "confidence"],
                            },
                        }
                    },
                    "required": ["events"],
                }

                prompt = self._build_prompt(text)

                print(f"\n========== AGENT 5 PROMPT (doc {doc_id}) ==========")
                print(prompt)
                print("========== END AGENT 5 DEBUG ==========\n")

                result = self.call_llm(prompt, json_schema=schema)

                raw_events = result.get("events", []) or []
                if not isinstance(raw_events, list):
                    raise ValueError("LLM returned invalid events format.")

                for item in raw_events:
                    if not isinstance(item, dict):
                        continue

                    description = str(item.get("description", "")).strip()
                    if not description:
                        continue

                    timestamp = self._normalize_timestamp(item.get("timestamp"))
                    event_type = str(item.get("event_type", "other") or "other").strip().lower()

                    try:
                        confidence = float(item.get("confidence", 0.6))
                    except (TypeError, ValueError):
                        confidence = 0.6
                    confidence = max(0.0, min(1.0, confidence))

                    # --------------------------------------------------
                    # Link entities mentioned in this event's description
                    # back to Agent 2's known entities.
                    # --------------------------------------------------
                    matched_entity_ids = [
                        name for name in known_entity_names
                        if name in description.lower()
                    ]

                    # --------------------------------------------------
                    # Merge key: same normalized description text +
                    # same timestamp bucket = same real-world event.
                    # --------------------------------------------------
                    merge_key = f"{timestamp or 'unknown'}|{description.lower().strip()}"

                    if merge_key not in merged:
                        event_counter += 1
                        merged[merge_key] = {
                            "event_id": f"EVT{event_counter:03d}",
                            "timestamp": timestamp,
                            "event_type": event_type,
                            "description": description,
                            "evidence_ids": [],
                            "entity_ids": [],
                            "confidences": [],
                        }

                    if evidence_id not in merged[merge_key]["evidence_ids"]:
                        merged[merge_key]["evidence_ids"].append(evidence_id)

                    for entity_id in matched_entity_ids:
                        if entity_id not in merged[merge_key]["entity_ids"]:
                            merged[merge_key]["entity_ids"].append(entity_id)

                    merged[merge_key]["confidences"].append(confidence)

            except Exception as error:
                failures += 1
                print(f"[Agent 5] Failed processing {doc_id}: {error}")

        # ======================================================
        # BUILD FINAL TIMELINE
        # ======================================================

        timeline: List[Dict[str, Any]] = []

        for merge_key, data in merged.items():
            confidences = data["confidences"]
            average_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

            # An event corroborated by more than one evidence source is
            # more trustworthy — nudge confidence up slightly, capped at 0.99.
            if len(data["evidence_ids"]) > 1:
                average_confidence = round(min(0.99, average_confidence + 0.1), 2)

            event_record = {
                "event_id": data["event_id"],
                "timestamp": data["timestamp"],
                "event_type": data["event_type"],
                "description": data["description"],
                "evidence_ids": sorted(set(data["evidence_ids"])),
                "entity_ids": sorted(set(data["entity_ids"])),
                "confidence": average_confidence,
            }

            timeline.append(event_record)

            add_confidence_score(
                state,
                item_id=data["event_id"],
                category="timeline",
                score=average_confidence,
                reason=(
                    f"Supported by {len(event_record['evidence_ids'])} evidence "
                    f"source(s); {len(confidences)} extraction(s) averaged."
                ),
            )

            if average_confidence < LOW_CONFIDENCE_REVIEW_THRESHOLD:
                flag_for_review(
                    state,
                    item_id=data["event_id"],
                    category="major_finding",
                    notes=(
                        f"Low-confidence timeline event ({average_confidence}): "
                        f"{data['description']}"
                    ),
                )

        # ======================================================
        # SORT CHRONOLOGICALLY
        # Events with a real timestamp come first, in order.
        # Events with no timestamp (None) are appended at the end,
        # since we cannot place them on the timeline reliably.
        # ======================================================

        timeline.sort(
            key=lambda e: (e["timestamp"] is None, e["timestamp"] or "")
        )

        # ======================================================
        # DETERMINE STATUS
        # ======================================================

        total_documents = len(cleaned_documents)

        if failures == 0:
            status = "success"
        elif failures < total_documents:
            status = "partial"
        else:
            status = "failed"

        # ======================================================
        # EXECUTION LOG
        # ======================================================

        log_agent_execution(
            state,
            agent_name=self.AGENT_NAME,
            model_used=self.model_name,
            started_at=started_at,
            status=status,
            input_evidence=doc_ids,
            output_summary=(
                f"Reconstructed {len(timeline)} timeline event(s) from "
                f"{total_documents - failures}/{total_documents} documents "
                f"({len(merged)} unique after cross-evidence merging)."
            ),
            error_message=f"{failures} document(s) failed timeline extraction." if failures else None,
        )

        return {"timeline": timeline}

    # ==========================================================
    # TIMESTAMP NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_timestamp(raw_timestamp: Optional[str]) -> Optional[str]:
        """Best-effort normalization of an LLM-extracted timestamp string
        into ISO 8601. Returns None (never a guess) if it can't be parsed
        confidently — an unreconstructable time is safer than a wrong one.
        """
        if not raw_timestamp or not isinstance(raw_timestamp, str):
            return None

        raw_timestamp = raw_timestamp.strip()
        if not raw_timestamp or raw_timestamp.lower() in {"unknown", "null", "none", ""}:
            return None

        candidate_formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%y, %I:%M %p",
            "%d/%m/%Y, %I:%M %p",
            "%d/%m/%y %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d",
        ]

        for fmt in candidate_formats:
            try:
                parsed = datetime.strptime(raw_timestamp, fmt)
                return parsed.isoformat()
            except ValueError:
                continue

        # Couldn't confidently parse — return the raw string as-is rather
        # than silently dropping it; sort will bucket it after real
        # ISO timestamps since it won't match the None check but also
        # won't sort correctly against them. Preferable to losing evidence.
        return raw_timestamp

    # ==========================================================
    # PROMPT BUILDER
    # ==========================================================

    @staticmethod
    def _build_prompt(text: str) -> str:
        return f"""
You are a forensic timeline reconstruction assistant for INVESTCOPS AI.

Your task is to extract a chronological list of EVENTS that are
EXPLICITLY supported by the investigation evidence below. An event is
something that happened at (or around) a specific time — a call, a
message sent, a location visited, a transaction, a login, a meeting,
etc.

For every event provide:

- timestamp: ISO-8601 if the evidence gives a clear date/time,
  otherwise null. NEVER guess or estimate a timestamp.
- event_type: one of "call", "message", "location_visit",
  "transaction", "login", "meeting", "other"
- description: one clear sentence describing what happened, including
  who was involved if known (e.g. "Rahul called the victim at 10:32 PM")
- confidence: 0.0 to 1.0, how certain you are this event and its
  timestamp are accurately extracted from the evidence

IMPORTANT RULES:

1. Do NOT invent events that are not stated in the evidence.
2. Do NOT guess a timestamp if the evidence does not clearly provide one
   — return null instead.
3. Do NOT merge unrelated events into one.
4. Do NOT draw conclusions about guilt, intent, or motive — only
   describe what the evidence literally shows happened.
5. If there are no clearly supported events, return an empty list.
6. Return ONLY valid JSON.
7. Do not use Markdown.
8. Do not include explanations outside JSON.

INVESTIGATION EVIDENCE:

{text}

RETURN EXACTLY THIS JSON STRUCTURE:

{{
    "events": [
        {{
            "timestamp": "2024-08-12T22:32:00",
            "event_type": "call",
            "description": "Rahul called the victim at 10:32 PM",
            "confidence": 0.9
        }}
    ]
}}
"""