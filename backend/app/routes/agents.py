"""Agent execution routes: single agents, full pipeline, results reading."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.models.models import (
    Case,
    User,
)
from app.schemas.schemas import (
    AgentResultEnvelope,
    AgentRunRequest,
    PipelineRunOut,
)
from app.services.agent_service import build_state, run_agent, run_pipeline
from app.services.cases import get_case

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _case(db: Session, case_id: str) -> Case:
    case = db.scalar(select(Case).where(Case.case_id == case_id))
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    return case


def _run_single(
    db: Session, user: User, req: AgentRunRequest, agent_name: str
) -> AgentResultEnvelope:
    try:
        get_case(db, user, req.case_id)
        envelope = run_agent(db, user, req.case_id, agent_name, question=req.question)
        return AgentResultEnvelope.model_validate(envelope)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/validate", response_model=AgentResultEnvelope)
def agent_validate(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_1_ingestion")


@router.post("/evidence-analysis", response_model=AgentResultEnvelope)
def agent_evidence_analysis(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_2_evidence_analysis")


@router.post("/entity-extraction", response_model=AgentResultEnvelope)
def agent_entity_extraction(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_3_entities")


@router.post("/relationships", response_model=AgentResultEnvelope)
def agent_relationships(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_4_relationships")


@router.post("/correlation", response_model=AgentResultEnvelope)
def agent_correlation(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_5_correlate")


@router.post("/timeline", response_model=AgentResultEnvelope)
def agent_timeline(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_6_timeline")


@router.post("/contradiction", response_model=AgentResultEnvelope)
def agent_contradiction(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_7_contradict")


@router.post("/risk", response_model=AgentResultEnvelope)
def agent_risk(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_8_risk")


@router.post("/explainability", response_model=AgentResultEnvelope)
def agent_explainability(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_9_insights")


@router.post("/gpt", response_model=AgentResultEnvelope)
def agent_gpt(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="question is required")
    return _run_single(db, current_user, req, "agent_10_rag_qa")


@router.post("/mentor", response_model=AgentResultEnvelope)
def agent_mentor(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_11_mentor_fir")


@router.post("/readiness", response_model=AgentResultEnvelope)
def agent_readiness(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_11_mentor_fir")


@router.post("/fir", response_model=AgentResultEnvelope)
def agent_fir(req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _run_single(db, current_user, req, "agent_11_mentor_fir")


@router.post("/pipeline", response_model=PipelineRunOut)
def run_full_pipeline_endpoint(
    req: AgentRunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        get_case(db, current_user, req.case_id)
        return PipelineRunOut.model_validate(run_pipeline(db, current_user, req.case_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{case_id}/results")
def case_results(
    case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        get_case(db, current_user, case_id)
        state = build_state(db, case_id)
        return {
            "case_id": case_id,
            "agent_results": state.agent_results,
            "agent_runs": [
                {
                    "agent_name": r["agent_name"],
                    "status": r["status"],
                    "confidence": r.get("confidence"),
                    "started_at": r.get("started_at"),
                }
                for r in state.agent_runs
            ],
        }
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))