from __future__ import annotations

import re

from .base import Answer, Citation

_SENT_RE = re.compile(r"(?<=[.!?])\s+")


class ExtractiveAnswerer:
    """
    No-LLM fallback.
    Produces a short answer by selecting sentences from the top sources.
    """

    name = "extractive"

    def answer(self, question: str, context: list[tuple[str, str, int, str]]) -> Answer:
        if not context:
            return Answer(
                text="I don't have enough information in the provided sources to answer that.",
                citations=[],
                refused=True,
                provider=self.name,
            )

        q_terms = set(re.findall(r"[A-Za-z0-9_]+", question.lower()))
        chosen: list[str] = []
        citations: list[Citation] = []

        for chunk_id, doc_id, idx, text in context[:3]:
            # Pick up to 2 sentences that overlap with question terms
            sents = _SENT_RE.split(text.strip())
            picked: list[str] = []
            for s in sents:
                if len(picked) >= 2:
                    break
                terms = set(re.findall(r"[A-Za-z0-9_]+", s.lower()))
                if q_terms and len(q_terms.intersection(terms)) == 0:
                    continue
                picked.append(s.strip())
            if not picked:
                picked = [sents[0].strip()] if sents else []
            if picked:
                quote = " ".join(picked)[:300]
                citations.append(Citation(chunk_id=chunk_id, doc_id=doc_id, idx=idx, quote=quote))
                chosen.append(" ".join(picked))

        if not chosen:
            return Answer(
                text="I don't have enough information in the provided sources to answer that.",
                citations=[],
                refused=True,
                provider=self.name,
            )

        answer = " ".join(chosen)
        return Answer(text=answer, citations=citations, refused=False, provider=self.name)
