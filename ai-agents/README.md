# INVESTCOPS AI - Agents Module

## Overview

The agents module contains 11 specialized AI agents that work together to conduct digital investigations.

## Agent Workflow

```
Evidence Input
     ↓
[Agent 1] Ingestion & Validation
     ↓
[Agent 2] Evidence Analysis
     ↓
[Agent 3] Entity Extraction
     ↓
[Agent 4] Relationship Analysis
     ↓
[Agent 5] Cross-Evidence Correlation
     ↓
[Agent 6] Timeline Reconstruction
     ↓
[Agent 7] Contradiction Detection
     ↓
[Agent 8] Risk Assessment
     ↓
[Agent 9] Explainability & Insights
     ↓
[Agent 10] RAG Q&A
     ↓
[Agent 11] Mentor & FIR Draft
     ↓
Investigation Report
```

## Project Structure

```
ai-agents/
├── core/
│   ├── state.py           # Shared investigation state schema
│   ├── base_agent.py      # Base class for all agents
│   └── config.py          # Configuration management
│
├── agents/
│   ├── agent_1_ingestion.py
│   ├── agent_2_evidence_analysis.py
│   ├── agent_3_entities.py
│   ├── agent_4_relationships.py
│   ├── agent_5_correlate.py
│   ├── agent_6_timeline.py
│   ├── agent_7_contradict.py
│   ├── agent_8_risk.py
│   ├── agent_9_insights.py
│   ├── agent_10_rag_qa.py
│   └── agent_11_mentor_fir.py
│
├── orchestrator/
│   └── graph_builder.py   # Workflow orchestration
│
├── tests/                 # Agent unit tests
├── test_data/            # Synthetic test data
│   ├── cases/
│   ├── evidence/
│   └── expected_outputs/
│
└── requirements.txt      # Dependencies
```

## Development Status

- [x] Project structure
- [x] Core infrastructure (state, base agent, config)
- [x] Agent module stubs (11 agents)
- [ ] Agent implementations
- [ ] Agent orchestration (LangGraph)
- [ ] Integration tests
- [ ] Test data generation

## Running Tests

```bash
pytest tests/
```

## Dependencies

See `requirements.txt` for current dependencies. Future integrations:
- LangGraph for agent orchestration
- OpenAI API for LLM capabilities
- Neo4j for knowledge graph storage

## Notes

- Do NOT implement agents yet
- Do NOT add AI APIs yet
- Do NOT add Neo4j integration yet
- Do NOT add LangGraph yet
- Keep test data separate in test_data/
