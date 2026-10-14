"""The analysis pipeline: text in, one structured result out."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .emotions import count_emotions
from .insights import build_insights
from .sentiment import DOCUMENT_THRESHOLD, SENTENCE_THRESHOLD, label_for, score_text
from .summarize import keywords, summaries_by_length
from .text import count_words, reading_time, round_half_up, split_sentences

MAX_CHARS = 300_000
MIN_WORDS = 15
MIN_SENTENCES = 2
ARC_STRETCHES = 12


class AnalysisError(ValueError):
    """The text cannot be analyzed (for example, it is too short)."""


@dataclass
class SentenceResult:
    text: str
    score: float
    label: str
    paragraph: int
    hits: int


@dataclass
class Analysis:
    text: str
    truncated: bool
    words: int
    sentences: List[SentenceResult]
    avg_score: float
    shares: Dict[str, float]
    opinionated_share: float
    avg_sentence_length: int
    verdict: str
    summaries: Dict[str, List[int]]
    keywords: List[Any]
    emotions: Dict[str, int]
    arc: List[float]
    segments: List[Any] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)

    @property
    def verdict_tone(self) -> str:
        if self.avg_score >= DOCUMENT_THRESHOLD:
            return "pos"
        if self.avg_score <= -DOCUMENT_THRESHOLD:
            return "neg"
        return "neu"

    def standouts(self, limit: int = 2) -> Dict[str, List[SentenceResult]]:
        positive = sorted((s for s in self.sentences if s.score >= SENTENCE_THRESHOLD), key=lambda s: -s.score)
        negative = sorted((s for s in self.sentences if s.score <= -SENTENCE_THRESHOLD), key=lambda s: s.score)
        return {"positive": positive[:limit], "negative": negative[:limit]}

    def summary_sentences(self, length: str = "medium") -> List[SentenceResult]:
        return [self.sentences[i] for i in self.summaries[length]]

    def to_dict(self) -> Dict[str, Any]:
        def sentence(s: SentenceResult) -> Dict[str, Any]:
            return {"text": s.text, "score": round(s.score, 4), "label": s.label}

        stand = self.standouts()
        return {
            "text": self.text,
            "truncated": self.truncated,
            "words": self.words,
            "reading_time": reading_time(self.words),
            "avg_sentence_length": self.avg_sentence_length,
            "avg_score": round(self.avg_score, 4),
            "verdict": self.verdict,
            "verdict_tone": self.verdict_tone,
            "shares": {k: round(v, 4) for k, v in self.shares.items()},
            "opinionated_share": round(self.opinionated_share, 4),
            "sentences": [sentence(s) for s in self.sentences],
            "summaries": self.summaries,
            "keywords": [{"word": w, "count": c} for w, c in self.keywords],
            "emotions": self.emotions,
            "arc": [round(x, 4) for x in self.arc],
            "standouts": {k: [sentence(s) for s in v] for k, v in stand.items()},
            "insights": self.insights,
            "annotated": [{"text": s.text, "kind": s.kind, "tip": s.tip} for s in self.segments],
        }


def _verdict(avg: float, shares: Dict[str, float]) -> str:
    if shares["pos"] >= 0.25 and shares["neg"] >= 0.25:
        if avg >= DOCUMENT_THRESHOLD:
            return "Mixed, leaning positive"
        if avg <= -DOCUMENT_THRESHOLD:
            return "Mixed, leaning negative"
        return "Mixed"
    if avg >= 0.25:
        return "Clearly positive"
    if avg >= DOCUMENT_THRESHOLD:
        return "Positive"
    if avg <= -0.25:
        return "Clearly negative"
    if avg <= -DOCUMENT_THRESHOLD:
        return "Negative"
    return "Neutral"


def _arc(scores: List[float]) -> List[float]:
    n = len(scores)
    if n < 3:
        return []
    stretches = ARC_STRETCHES if n >= ARC_STRETCHES else n
    out = []
    for s in range(stretches):
        start = s * n // stretches
        end = max(start + 1, (s + 1) * n // stretches)
        part = scores[start:end]
        out.append(sum(part) / len(part))
    return out


def analyze_text(text: str, max_chars: int = MAX_CHARS) -> Analysis:
    """Summarise ``text`` and analyse its sentiment. Raises AnalysisError if it is too short."""
    text = text.replace("\r", "").strip()
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]

    split = split_sentences(text)
    words = count_words(text)
    if words < MIN_WORDS or len(split) < MIN_SENTENCES:
        raise AnalysisError(
            "Add a little more text. At least two sentences or about 15 words are needed."
        )

    results: List[SentenceResult] = []
    for item in split:
        scored = score_text(item.text)
        results.append(SentenceResult(item.text, scored.score, label_for(scored.score, SENTENCE_THRESHOLD),
                                      item.paragraph, scored.hits))

    count = len(results)
    shares = {k: sum(1 for r in results if r.label == k) / count for k in ("neg", "neu", "pos")}
    scores = [r.score for r in results]
    avg = sum(scores) / count
    sentence_texts = [r.text for r in results]

    analysis = Analysis(
        text=text,
        truncated=truncated,
        words=words,
        sentences=results,
        avg_score=avg,
        shares=shares,
        opinionated_share=sum(1 for r in results if r.hits > 0) / count,
        avg_sentence_length=round_half_up(words / count),
        verdict=_verdict(avg, shares),
        summaries=summaries_by_length(sentence_texts),
        keywords=keywords(sentence_texts),
        emotions=count_emotions(text),
        arc=_arc(scores),
        segments=score_text(text, annotate=True).segments,
    )
    analysis.insights = build_insights(analysis)
    return analysis
