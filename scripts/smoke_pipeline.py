"""Dev smoke test: run the 11-agent pipeline over a tiny synthetic case."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai-agents"))

from agents.registry import PIPELINE_ORDER, get_agent
from core.state import EvidenceRecord, InvestigationState
from core.utils import sha256_bytes

if __name__ == "__main__":
    chat = """[12/02/2025, 3:45:12 PM] Ravi Kumar: Please transfer the amount to account 9876543210123
[12/02/2025, 3:50:00 PM] Anjali Sharma: I already sent Rs. 45,000 via UPI to 98765 43210
[13/02/2025, 9:10:55 AM] Ravi Kumar: You will be sorry if you don't pay. I know where your office at Mumbai is.
[13/02/2025, 9:15:30 AM] Anjali Sharma: I am scared. Please don't threaten me. I will report you.
[14/02/2025, 6:30:00 PM] SafeExit2026: Meet me at Connaught Place tomorrow at 5 pm."""

    email = """From: victim@example.com
To: support@payments.com
Subject: Complaint
Date: 15 Feb 2025 10:12

I received threats from someone using phone +91-98765-43210 and email ravi.k@example.com."""

    state = InvestigationState(case_id="CASE-SMOKE-001", case_title="Smoke test case")
    for i, (name, mime, content) in enumerate(
        [
            ("whatsapp_chat.txt", "text/plain", chat),
            ("followup.eml", "message/rfc822", email),
        ],
        start=1,
    ):
        rec = EvidenceRecord(
            evidence_id=f"E-SMOKE-{i}",
            file_name=name,
            mime_type=mime,
            size=len(content.encode()),
            sha256=sha256_bytes(content.encode()),
            source_type="chat_whatsapp" if i == 1 else "email",
            validation_status="VALID",
            integrity_status="READABLE",
        )
        state.evidence.append(rec)
        state.cleaned_documents.append({"evidence_id": rec.evidence_id, "file_name": name, "text": content})

    agent = get_agent("agent_10_rag_qa")
    agent._question = "What amount and phone number are mentioned in the chat?"
    for name in PIPELINE_ORDER:
        a = get_agent(name)
        if name == "agent_10_rag_qa":
            continue
        state_dict = a.run(state.to_serializable())
        state = InvestigationState.model_validate(state_dict)
        res = state.agent_results[name]
        print(f"{name:32s} -> {res['status']:12s} conf={res['confidence']}")

    res = agent.run(state.to_serializable())
    state = InvestigationState.model_validate(res)
    qa = state.qa_history[-1]
    print(f"{'agent_10_rag_qa':32s} -> {state.agent_results['agent_10_rag_qa']['status']} conf={state.agent_results['agent_10_rag_qa']['confidence']}")
    print()
    print("ANSWER:", qa.answer[:400])
    print()
    print("Risk:", state.risk_score.risk_score, state.risk_score.risk_level)
    print("Timeline events:", len(state.timeline), "| Entities:", len(state.entities), "| Relations:", len(state.relationships))
    print("Correlations:", len(state.correlated_entities), "| Contradictions:", len(state.contradictions))
    print("Readiness:", state.readiness.readiness_score, "| Mentor recs:", len(state.mentor_recommendations))
    print("FIR facts:", len(state.fir_draft.facts))