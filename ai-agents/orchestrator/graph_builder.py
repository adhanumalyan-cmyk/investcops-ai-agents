"""
orchestrator/graph_builder.py

Wires all 11 agents into a single LangGraph pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from core.state import InvestigationState, get_initial_state
from intake.case_builder import CaseBuilder
from intake.adb_fetch import ADBFetcher

# --- YOUR agents (already implemented) ---
from agents.agent_1_ingestion import EvidenceIngestionAgent   # 👈 FIX: Correct class name
from agents.agent_2_entities import EntityExtractionAgent
from agents.agent_4_correlate import CorrelationAgent
from agents.agent_6_contradict import ContradictionDetectionAgent
from agents.agent_7_risk import RiskAssessmentAgent
from agents.agent_11_fir import FIRDraftAgent

# --- Friends agents (pending — placeholder) ---
# TODO(teammate B): from agents.agent_3_relationships import RelationshipAgent
# TODO(teammate A): from agents.agent_5_timeline import TimelineAgent
# TODO(teammate A): from agents.agent_8_insights import InsightsAgent
# TODO(teammate C): from agents.agent_9_rag_qa import RAGQAAgent
# TODO(teammate B): from agents.agent_10_mentor import MentorAgent


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_ROOT = PROJECT_ROOT / "cases"


# ---------------------------------------------------------------------------
# Node wrappers
# ---------------------------------------------------------------------------

def node_agent_1_ingestion(state: InvestigationState) -> Dict[str, Any]:
    """Agent 1: Evidence Ingestion — reads files from case folder."""
    return EvidenceIngestionAgent().process(state)  # 👈 FIX: Correct class name


def node_agent_2_entities(state: InvestigationState) -> Dict[str, Any]:
    return EntityExtractionAgent().process(state)


def node_agent_3_relationships(state: InvestigationState) -> Dict[str, Any]:
    # Placeholder — Friend B
    return {"relationships": state.get("relationships", [])}


def node_agent_4_correlate(state: InvestigationState) -> Dict[str, Any]:
    return CorrelationAgent().process(state)


def node_agent_5_timeline(state: InvestigationState) -> Dict[str, Any]:
    # Placeholder — Friend A
    return {"timeline": state.get("timeline", [])}


def node_agent_6_contradict(state: InvestigationState) -> Dict[str, Any]:
    return ContradictionDetectionAgent().process(state)


def node_agent_7_risk(state: InvestigationState) -> Dict[str, Any]:
    return RiskAssessmentAgent().process(state)


def node_agent_8_insights(state: InvestigationState) -> Dict[str, Any]:
    # Placeholder — Friend A
    return {"insights_summary": state.get("insights_summary", "")}


def node_agent_10_mentor(state: InvestigationState) -> Dict[str, Any]:
    # Placeholder — Friend B
    return {"mentor_recommendations": state.get("mentor_recommendations", [])}


def node_agent_11_fir(state: InvestigationState) -> Dict[str, Any]:
    return FIRDraftAgent().process(state)


# ---------------------------------------------------------------------------
# Build Graph — CORRECTED FUNCTION NAME
# ---------------------------------------------------------------------------

def build_case_pipeline():
    """Builds and returns the compiled LangGraph pipeline."""
    graph = StateGraph(InvestigationState)

    # Add nodes — Agent 1 uses correct class
    graph.add_node("agent_1_ingestion", node_agent_1_ingestion)  # 👈 Uses wrapper
    graph.add_node("agent_2_entities", node_agent_2_entities)
    graph.add_node("agent_3_relationships", node_agent_3_relationships)
    graph.add_node("agent_4_correlate", node_agent_4_correlate)
    graph.add_node("agent_5_timeline", node_agent_5_timeline)
    graph.add_node("agent_6_contradict", node_agent_6_contradict)
    graph.add_node("agent_7_risk", node_agent_7_risk)
    graph.add_node("agent_8_insights", node_agent_8_insights)
    graph.add_node("agent_10_mentor", node_agent_10_mentor)
    graph.add_node("agent_11_fir", node_agent_11_fir)

    # Entry point
    graph.set_entry_point("agent_1_ingestion")

    # Edges
    graph.add_edge("agent_1_ingestion", "agent_2_entities")
    graph.add_edge("agent_2_entities", "agent_3_relationships")
    graph.add_edge("agent_3_relationships", "agent_4_correlate")
    graph.add_edge("agent_4_correlate", "agent_5_timeline")
    graph.add_edge("agent_5_timeline", "agent_6_contradict")
    graph.add_edge("agent_6_contradict", "agent_7_risk")
    graph.add_edge("agent_7_risk", "agent_8_insights")
    graph.add_edge("agent_8_insights", "agent_10_mentor")
    graph.add_edge("agent_10_mentor", "agent_11_fir")
    graph.add_edge("agent_11_fir", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Full pipeline entry points
# ---------------------------------------------------------------------------

def run_investigation(case_id: str, investigator: str = "unknown", fetch_from_phone: bool = True) -> InvestigationState:
    """End-to-end run: pulls evidence from connected phone, builds case,
    and runs through AI pipeline."""
    
    builder = CaseBuilder(case_id=case_id, cases_root=str(CASES_ROOT), investigator=investigator)

    if fetch_from_phone:
        fetcher = ADBFetcher()
        builder.run_full_intake(fetcher)

    builder.ingest_chat_exports()
    initial_state = builder.build_initial_state()
    
    # 👈 IMPORTANT: Add case_folder to state so Agent 1 can read files
    initial_state["case_folder"] = str(builder.case_dir.resolve())
    
    app = build_case_pipeline()
    return app.invoke(initial_state)


def run_investigation_from_existing_case(case_id: str) -> InvestigationState:
    """Re-runs agent pipeline on existing case folder."""
    builder = CaseBuilder(case_id=case_id, cases_root=str(CASES_ROOT))
    builder.ingest_chat_exports()
    initial_state = builder.build_initial_state()
    
    # 👈 Add case_folder to state
    initial_state["case_folder"] = str(builder.case_dir.resolve())
    
    app = build_case_pipeline()
    return app.invoke(initial_state)


# ---------------------------------------------------------------------------
# Agent 9 (RAG Q&A) — on-demand
# ---------------------------------------------------------------------------

def ask_question(state: InvestigationState, question: str) -> InvestigationState:
    # TODO(teammate C): replace with RAGQAAgent
    state.setdefault("qa_history", []).append(
        {"question": question, "answer": "[Agent 9 not wired in yet]"}
    )
    return state


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    case_id = sys.argv[1] if len(sys.argv) > 1 else "TEST001"
    result = run_investigation(case_id=case_id, investigator="demo_investigator")

    print("\n=== PIPELINE COMPLETE ===")
    print(f"Entities: { {k: len(v) for k, v in result.get('entities', {}).items()} }")
    print(f"Contradictions: {len(result.get('contradictions', []))}")
    print(f"Risk score: {result.get('risk_score')}")
    print(f"FIR draft length: {len(result.get('fir_draft', ''))} chars")
    print(f"\nCase folder: {CASES_ROOT / f'CASE_{case_id}'}")