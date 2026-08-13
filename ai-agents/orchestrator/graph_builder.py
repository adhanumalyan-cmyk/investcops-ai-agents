"""
Investigation Graph Builder

Real LangGraph orchestration of the 11-agent pipeline with:
- node registration from the shared registry
- typed state flow (dict-based, matches InvestigationState)
- conditional routing (stop when no valid evidence)
- retries with backoff
- failure handling (agent failure never silently continues as fake success;
  downstream nodes run on the best available state)
- status tracking and logging
"""

import logging
import time
from typing import Any, Callable, Dict, List, TypedDict

from agents.registry import PIPELINE_ORDER, get_agent

logger = logging.getLogger("investcops.orchestrator")

MAX_RETRIES = 2
BACKOFF_SECONDS = 0.5


class GraphState(TypedDict):
    """LangGraph state: the serializable InvestigationState plus run extras."""

    case_id: str
    state: Dict[str, Any]
    agent_status: Dict[str, str]
    errors: List[Dict[str, Any]]


def _make_node(agent_name: str) -> Callable[[GraphState], GraphState]:
    """Factory for an agent node with retries + status tracking."""

    def node(graph_state: GraphState) -> GraphState:
        agent = get_agent(agent_name)
        statuses = dict(graph_state.get("agent_status", {}))
        state_data = graph_state.get("state", {})

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                new_state = agent.run(state_data)
                statuses[agent_name] = new_state.get("agent_results", {}).get(agent_name, {}).get("status", "COMPLETED")
                logger.info("Node %s finished (attempt %d)", agent_name, attempt)
                return {"state": new_state, "agent_status": statuses, "errors": graph_state.get("errors", [])}
            except Exception as exc:
                last_error = exc
                logger.warning("Node %s attempt %d failed: %s", agent_name, attempt, exc)
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS * attempt)
        # All retries failed: record the failure, keep prior state, continue chain.
        errors = list(graph_state.get("errors", []))
        errors.append({"agent_name": agent_name, "error": str(last_error), "attempts": MAX_RETRIES})
        statuses[agent_name] = "FAILED"
        return {"state": state_data, "agent_status": statuses, "errors": errors}

    return node


def _route_after_ingestion(graph_state: GraphState) -> str:
    """Stop when nothing was validated; otherwise continue the pipeline."""
    result = graph_state.get("agent_status", {}).get("agent_1_ingestion", "")
    if result and result != "COMPLETED":
        return "stop"
    return "continue"


def build_investigation_graph():
    """
    Build the compiled LangGraph pipeline for the 11 agents.

    Returns a callable graph: graph.invoke({"case_id":..., "state": {...}})
    """
    from langgraph.graph import END, START, StateGraph

    g = StateGraph(GraphState)

    # Node registration (Agent 10 is optional; invoked on demand via API).
    for name in PIPELINE_ORDER:
        if name == "agent_10_rag_qa":
            continue
        g.add_node(name, _make_node(name))

    # Linear flow with a routing gate after ingestion.
    g.add_edge(START, "agent_1_ingestion")
    g.add_conditional_edges(
        "agent_1_ingestion",
        _route_after_ingestion,
        {"continue": "agent_2_evidence_analysis", "stop": END},
    )
    for a, b in zip(PIPELINE_ORDER[1:-1], PIPELINE_ORDER[2:]):
        if a == "agent_10_rag_qa" or b == "agent_10_rag_qa":
            continue
        g.add_edge(a, b)
    # Agent 10 (RAG Q&A) is invoked on demand via the API; Agent 11 runs after
    # Agent 9 in the full pipeline.
    g.add_edge("agent_9_insights", "agent_11_mentor_fir")

    return g.compile()


def run_full_pipeline(state_data: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    """Execute the entire 11-agent pipeline over a serialized InvestigationState."""
    graph = build_investigation_graph()
    result = graph.invoke(
        {
            "case_id": case_id,
            "state": state_data,
            "agent_status": {},
            "errors": [],
        }
    )
    return result


def run_qa_on_state(state_data: Dict[str, Any], question: str, case_id: str) -> Dict[str, Any]:
    """Run Agent 10 (RAG Q&A) against an existing investigation state."""
    from agents.registry import get_agent as _get

    agent = _get("agent_10_rag_qa")
    agent._question = question
    return agent.run(state_data)