"""
Agent registry: maps agent endpoint names to classes. Also exposes the
canonical pipeline order used by the orchestrator and the API.
"""

from typing import Dict, Type

from core.base_agent import BaseAgent

from .agent_1_ingestion import Agent1Ingestion
from .agent_2_evidence_analysis import Agent2EvidenceAnalysis
from .agent_3_entities import Agent3Entities
from .agent_4_relationships import Agent4Relationships
from .agent_5_correlate import Agent5Correlate
from .agent_6_timeline import Agent6Timeline
from .agent_7_contradict import Agent7Contradict
from .agent_8_risk import Agent8Risk
from .agent_9_insights import Agent9Insights
from .agent_10_rag_qa import Agent10RagQA
from .agent_11_mentor_fir import Agent11MentorFIR

AGENT_CLASSES: Dict[str, Type[BaseAgent]] = {
    "agent_1_ingestion": Agent1Ingestion,
    "agent_2_evidence_analysis": Agent2EvidenceAnalysis,
    "agent_3_entities": Agent3Entities,
    "agent_4_relationships": Agent4Relationships,
    "agent_5_correlate": Agent5Correlate,
    "agent_6_timeline": Agent6Timeline,
    "agent_7_contradict": Agent7Contradict,
    "agent_8_risk": Agent8Risk,
    "agent_9_insights": Agent9Insights,
    "agent_10_rag_qa": Agent10RagQA,
    "agent_11_mentor_fir": Agent11MentorFIR,
}

PIPELINE_ORDER = [
    "agent_1_ingestion",
    "agent_2_evidence_analysis",
    "agent_3_entities",
    "agent_4_relationships",
    "agent_5_correlate",
    "agent_6_timeline",
    "agent_7_contradict",
    "agent_8_risk",
    "agent_9_insights",
    "agent_10_rag_qa",
    "agent_11_mentor_fir",
]


def get_agent(name: str) -> BaseAgent:
    """Instantiate an agent by registered name."""
    cls = AGENT_CLASSES.get(name)
    if cls is None:
        raise KeyError(f"Unknown agent: {name!r}")
    return cls()


__all__ = ["AGENT_CLASSES", "PIPELINE_ORDER", "get_agent"]