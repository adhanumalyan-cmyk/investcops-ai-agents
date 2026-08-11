"""
agents/agent_4_correlate.py

Agent 4 - Cross-Evidence Correlation

Input : state["entities"]   (Dict[str, List[Dict[str, str]]])
Output: {"correlated_entities": {"<canonical_name>": ["doc1", "doc2", ...]}}

Purpose: resolve aliases / duplicate references to the SAME real-world
entity across different pieces of evidence (e.g. "Rahul K." in DOC001 and
"Rahul Kumar" in DOC004 are the same person) and merge their mention lists
into a single canonical entry.
"""

from datetime import datetime
from typing import Any, Dict, List

from core.state import (
    InvestigationState,
    log_agent_execution,
    add_confidence_score,
)
from core.base_agent import BaseAgent


class CorrelationAgent(BaseAgent):
    """Groups entities that refer to the same real-world person/place/org/
    device across different evidence documents into canonical clusters.
    """

    AGENT_NAME = "Agent 4 - Cross-Evidence Correlation"

    def __init__(self, model_used: str = "qwen3:8b"):
        super().__init__(agent_name=self.AGENT_NAME, model_used=model_used)

    # ------------------------------------------------------------------
    def process(self, state: InvestigationState) -> Dict[str, Any]:
        started_at = datetime.utcnow()
        entities: Dict[str, List[Dict[str, Any]]] = state.get("entities", {})

        # Flatten all entities into a single list the LLM can reason over.
        flat_entities: List[Dict[str, Any]] = []
        for etype, items in (entities or {}).items():
            for item in items:
                flat_entities.append(
                    {
                        "name": item.get("name", ""),
                        "type": etype,
                        "mentions": item.get("mentions", []),
                    }
                )

        if not flat_entities:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="partial",
                input_evidence=[],
                output_summary="No entities found in state; nothing to correlate.",
            )
            return {"correlated_entities": {}}

        try:
            schema = {
                "type": "object",
                "properties": {
                    "clusters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "canonical_name": {"type": "string"},
                                "aliases": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "confidence": {"type": "number"},
                            },
                            "required": ["canonical_name", "aliases"],
                        },
                    }
                },
                "required": ["clusters"],
            }
            prompt = self._build_prompt(flat_entities)
            result = self.call_llm(prompt, json_schema=schema)
            clusters = result.get("clusters", []) or []

            # Build a lookup: name_lower -> mentions, for merging.
            name_to_mentions = {
                e["name"].strip().lower(): e.get("mentions", []) for e in flat_entities
            }

            correlated_entities: Dict[str, List[str]] = {}

            for cluster in clusters:
                canonical = (cluster.get("canonical_name") or "").strip()
                if not canonical:
                    continue
                aliases = cluster.get("aliases", []) or [canonical]
                confidence = float(cluster.get("confidence", 0.75))

                merged_mentions: List[str] = []
                for alias in aliases:
                    merged_mentions.extend(name_to_mentions.get(alias.strip().lower(), []))
                # include the canonical name's own mentions too, if separate
                merged_mentions.extend(name_to_mentions.get(canonical.lower(), []))

                correlated_entities[canonical] = sorted(set(merged_mentions))

                add_confidence_score(
                    state,
                    item_id=f"correlation:{canonical}",
                    category="entity",
                    score=confidence,
                    reason=f"Correlated from {len(aliases)} alias(es): {', '.join(aliases)}",
                )

            # Any entity the LLM didn't cluster: keep as its own singleton group,
            # so nothing found by Agent 2 silently disappears.
            clustered_names = {a.strip().lower() for c in clusters for a in c.get("aliases", [])}
            clustered_names |= {c.get("canonical_name", "").strip().lower() for c in clusters}

            for e in flat_entities:
                key = e["name"].strip().lower()
                if key not in clustered_names and e["name"] not in correlated_entities:
                    correlated_entities[e["name"]] = sorted(set(e.get("mentions", [])))

            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="success",
                input_evidence=[e["name"] for e in flat_entities],
                output_summary=f"Correlated {len(flat_entities)} entities into {len(correlated_entities)} canonical groups.",
            )

            return {"correlated_entities": correlated_entities}

        except Exception as e:
            log_agent_execution(
                state,
                agent_name=self.AGENT_NAME,
                model_used=self.model_used,
                started_at=started_at,
                status="failed",
                input_evidence=[e_["name"] for e_ in flat_entities],
                output_summary="Correlation failed; returning ungrouped entities as fallback.",
                error_message=str(e),
            )
            # Fallback: no correlation performed, each entity is its own group.
            fallback = {
                e["name"]: sorted(set(e.get("mentions", []))) for e in flat_entities
            }
            return {"correlated_entities": fallback}

    # ------------------------------------------------------------------
    @staticmethod
    def _build_prompt(flat_entities: List[Dict[str, Any]]) -> str:
        entity_lines = "\n".join(
            f"- [{e['type']}] {e['name']} (mentioned in: {', '.join(e['mentions']) or 'unknown'})"
            for e in flat_entities
        )
        return f"""You are a forensic entity-resolution assistant for INVESTCOPS AI.

Below is a list of entities extracted independently from multiple pieces of
evidence. Some entries may refer to the SAME real-world person, place,
organization, or device under slightly different names (e.g. "Rahul K." and
"Rahul Kumar", or "9876543210" and "+91 9876543210").

Group entities that refer to the same real-world thing into clusters. Each
cluster needs one canonical_name (the fullest/most complete form) and a list
of all aliases (including the canonical name itself) that belong to it.
Give a confidence score (0.0-1.0) for how sure you are the aliases are the
same entity. Do NOT merge entities that are only superficially similar but
likely different people/places.

Entities:
{entity_lines}

Return ONLY valid JSON:
{{
  "clusters": [
    {{"canonical_name": "<name>", "aliases": ["<alias1>", "<alias2>"], "confidence": 0.9}}
  ]
}}"""