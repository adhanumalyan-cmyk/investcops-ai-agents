"""
Investigation Agents Package

Contains 11 specialized agents for digital investigation:
1. Evidence Ingestion / Validation
2. Evidence Analysis
3. Entity Extraction
4. Relationship Analysis
5. Cross-Evidence Correlation
6. Timeline Reconstruction
7. Contradiction Detection
8. Risk Assessment
9. Explainability / Insights
10. Investigation GPT / RAG Q&A
11. Investigation Mentor + Evidence Readiness + FIR Draft
"""

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
from .registry import AGENT_CLASSES, PIPELINE_ORDER, get_agent

__all__ = [
    "Agent1Ingestion",
    "Agent2EvidenceAnalysis",
    "Agent3Entities",
    "Agent4Relationships",
    "Agent5Correlate",
    "Agent6Timeline",
    "Agent7Contradict",
    "Agent8Risk",
    "Agent9Insights",
    "Agent10RagQA",
    "Agent11MentorFIR",
    "AGENT_CLASSES",
    "PIPELINE_ORDER",
    "get_agent",
]