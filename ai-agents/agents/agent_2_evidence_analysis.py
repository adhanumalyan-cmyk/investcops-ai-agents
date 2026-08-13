"""
Agent 2: Evidence Analysis & Content Understanding.

Real processing: for each validated evidence item with extracted text it
produces a summary, key findings, indicators, dates/times, relevance and
provenance. Deterministic parsing is primary; the optional LLM layer only
adds semantic interpretation when configured. No invented content.
"""

from typing import Any, Dict, List

from core.base_agent import BaseAgent, InsufficientEvidenceError
from core.extract import (
    extract_dates,
    extract_emails,
    extract_locations,
    extract_names,
    extract_phones,
    extract_times,
    extract_transactions,
    indicator_hits,
    rank_units_by_keywords,
    sentence_split,
)
from core.llm import complete, llm_enabled
from core.state import EvidenceAnalysisResult, InvestigationState, Provenance
from core.utils import normalize_text


class Agent2EvidenceAnalysis(BaseAgent):
    name = "agent_2_evidence_analysis"
    description = "Evidence Analysis and Content Understanding"
    prompt_version = "2.0.0"

    def process(self, state: InvestigationState) -> Dict[str, Any]:
        docs = {d["evidence_id"]: d for d in state.cleaned_documents}
        valid = {v.evidence_id: v for v in state.validated_evidence}
        if not valid:
            raise InsufficientEvidenceError("No validated evidence to analyze.")

        analyses: List[EvidenceAnalysisResult] = []
        provenance: List[Provenance] = []
        warnings: List[str] = []

        for ev_id, ev in valid.items():
            text = docs.get(ev_id, {}).get("text", "") if docs else ""
            if not text:
                analyses.append(
                    EvidenceAnalysisResult(
                        evidence_id=ev_id,
                        summary="No extractable text available for this evidence (may require OCR/transcription).",
                        key_findings=[],
                        relevance=0.0,
                        indicators=[],
                        limitations=["No text content extracted; processing may have failed or type is unanalyzable."],
                    )
                )
                warnings.append(f"Evidence {ev_id}: no text content available for analysis.")
                continue

            findings, provenance_entry = self._analyze_text(state, ev_id, ev.file_name, text)
            analyses.append(findings)
            if provenance_entry:
                provenance.append(provenance_entry)

        overall_confidence = round(
            sum(a.relevance for a in analyses) / len(analyses), 3
        ) if analyses else 0.0

        result = {
            "analyzed_evidence_count": len(analyses),
            "with_text": sum(1 for a in analyses if a.key_findings),
            "without_text": sum(1 for a in analyses if not a.key_findings),
            "total_findings": sum(len(a.key_findings) for a in analyses),
            "indicators_by_category": self._indicator_summary(analyses),
            "analyses": [a.model_dump() for a in analyses],
        }
        return {
            "result": result,
            "state_fields": {"evidence_analyses": analyses},
            "confidence": overall_confidence,
            "evidence_references": provenance,
            "warnings": warnings,
            "evidence_ids": [v.evidence_id for v in valid.values()],
        }

    def _analyze_text(
        self, state: InvestigationState, ev_id: str, file_name: str, text: str
    ) -> tuple[EvidenceAnalysisResult, Provenance | None]:
        text = normalize_text(text)
        phones = list(dict.fromkeys(extract_phones(text)))
        emails = extract_emails(text)
        names = list(dict.fromkeys(extract_names(text)))
        locations = list(dict.fromkeys(extract_locations(text)))
        dates = extract_dates(text)
        times = extract_times(text)
        txns = extract_transactions(text)
        indicators = indicator_hits(text)
        units = sentence_split(text, max_len=400)

        indicator_descriptions = sorted(
            {f"{cat} ({kw})" for cat, kw in indicators}
        )

        keywords = [k for _, k in indicators] + names + phones
        salient = rank_units_by_keywords(text, keywords, limit=6)
        if not salient:
            salient = units[:4]

        findings: List[str] = []
        if names:
            findings.append(f"Persons identified: {', '.join(names[:5])}")
        if phones:
            findings.append(f"Phone numbers present: {', '.join(phones[:5])}")
        if emails:
            findings.append(f"Email addresses present: {', '.join(emails[:5])}")
        if locations:
            findings.append(f"Locations mentioned: {', '.join(locations[:5])}")
        if dates:
            findings.append(f"Dates referenced: {', '.join(dates[:5])}")
        if txns:
            findings.append(f"Transaction records detected: {len(txns)} entries")
        if indicator_descriptions:
            findings.append(f"Indicators detected: {', '.join(indicator_descriptions[:5])}")
        if salient:
            findings.append(f"Key statement: \"{salient[0][:240]}\"")
            if len(salient) > 1:
                findings.append(f"Related statement: \"{salient[1][:240]}\"")

        if not findings:
            findings.append("No persons, contacts, timestamps or indicators extractable from this text.")

        # Relevance: measured presence of investigative content, deterministic.
        relevance = 0.0
        weights = [
            (0.25, bool(phones or emails or txns)),
            (0.20, bool(names)),
            (0.20, bool(locations)),
            (0.20, bool(dates or times)),
            (0.15, bool(indicators)),
        ]
        relevance = round(sum(w for w, hit in weights if hit), 2)

        summary = (
            f"Evidence {ev_id} ({file_name}): {len(units)} analysis units reviewed; "
            f"{len(findings)} findings produced. "
            + (f"Primary content: {salient[0][:180]}" if salient else "No salient content extracted.")
        )

        limitations: List[str] = []
        if not phones and not emails and not names:
            limitations.append("No contact identifiers or person names extracted.")
        if indicators:
            limitations.append("Indicators are keyword matches; they require investigator verification.")

        # Optional LLM interpretation of the salient units only (never the raw dump).
        if llm_enabled() and salient and len(text) < 40_000:
            try:
                llm_note = complete(
                    "Summarize the following chat/document excerpt for an investigation file. "
                    "Use ONLY the excerpt. Report uncertainty.\n\n"
                    + "\n".join(f"- {u}" for u in salient[:6]),
                    system=self._llm_system(),
                )
                findings.append(f"AI interpretation: {llm_note[:300]}")
            except Exception as exc:
                warnings_pool = getattr(self, "_null_warnings", [])
                self._null_warnings = warnings_pool
                self._llm_note_failed(exc)

        excerpt = salient[0][:200] if salient else units[0][:200] if units else ""
        prov = self._provenance(
            ev_id,
            source_reference=f"{file_name}",
            file_name=file_name,
            excerpt_or_locator=excerpt,
            confidence=max(relevance, 0.3),
        )
        return (
            EvidenceAnalysisResult(
                evidence_id=ev_id,
                summary=summary,
                key_findings=findings,
                relevance=relevance,
                indicators=indicator_descriptions,
                limitations=limitations,
            ),
            prov,
        )

    def _indicator_summary(self, analyses: List[EvidenceAnalysisResult]) -> dict:
        cats: dict[str, int] = {}
        for a in analyses:
            for ind in a.indicators:
                cat = ind.split(" (")[0]
                cats[cat] = cats.get(cat, 0) + 1
        return {k: v for k, v in sorted(cats.items(), key=lambda i: -i[1])}

    def _llm_system(self) -> str:
        return (
            "You are a digital investigation analyst. Use ONLY the provided excerpt. "
            "Never invent facts, identities or citations. Report uncertainty. "
            "No legal determinations."
        )

    def _llm_note_failed(self, exc: Exception) -> None:
        """LLM enhancement failure must not fabricate success - only annotate."""
        self.logger.warning("LLM interpretation unavailable for Agent 2: %s", exc)