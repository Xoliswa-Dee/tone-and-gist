"""Turn the numbers from an analysis into plain-language insights."""
from __future__ import annotations

from typing import List, TYPE_CHECKING

from .lexicon import EMOTION_LABELS
from .sentiment import DOCUMENT_THRESHOLD, SENTENCE_THRESHOLD
from .text import clip, fmt_pct, fmt_signed, reading_time

if TYPE_CHECKING:  # pragma: no cover
    from .analyzer import Analysis


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_insights(a: "Analysis") -> List[str]:
    notes: List[str] = []
    shares = a.shares
    count = len(a.sentences)

    notes.append(
        f"Overall the text reads as {a.verdict.lower()}. The average sentence score is "
        f"{fmt_signed(a.avg_score)}, with {fmt_pct(shares['pos'])} of sentences positive, "
        f"{fmt_pct(shares['neu'])} neutral and {fmt_pct(shares['neg'])} negative."
    )

    if a.opinionated_share < 0.3:
        style = "mostly factual in style"
    elif a.opinionated_share > 0.65:
        style = "strongly opinionated"
    else:
        style = "a mix of fact and opinion"
    notes.append(
        f"{fmt_pct(a.opinionated_share)} of sentences contain evaluative or emotional wording, "
        f"so the text is {style}."
    )

    if shares["pos"] >= 0.25 and shares["neg"] >= 0.25:
        notes.append(
            "It swings between positive and negative passages instead of staying in one register, "
            "so the average hides real tension. Read the standout passages to see both sides."
        )

    scores = [s.score for s in a.sentences]
    if count >= 6:
        third = max(2, count // 3)
        start, end = _mean(scores[:third]), _mean(scores[-third:])
        change = end - start
        if abs(change) < 0.08:
            notes.append(
                f"The tone stays steady from start to finish ({fmt_signed(start)} at the start, "
                f"{fmt_signed(end)} at the end)."
            )
        elif change > 0:
            notes.append(
                f"The tone improves toward the end, from {fmt_signed(start)} in the opening third to "
                f"{fmt_signed(end)} in the closing third. The text ends more positively than it begins."
            )
        else:
            notes.append(
                f"The tone worsens toward the end, from {fmt_signed(start)} in the opening third to "
                f"{fmt_signed(end)} in the closing third. The text ends more negatively than it begins."
            )

    ranked = sorted(((n, c) for n, c in a.emotions.items() if c > 0), key=lambda nc: -nc[1])
    if ranked and sum(c for _, c in ranked) >= 3:
        line = f"The strongest emotion signal is {EMOTION_LABELS[ranked[0][0]].lower()} ({ranked[0][1]} words)"
        if len(ranked) > 1:
            line += f", followed by {EMOTION_LABELS[ranked[1][0]].lower()} ({ranked[1][1]})"
        notes.append(line + ".")

    negative = sorted((s for s in a.sentences if s.score <= -SENTENCE_THRESHOLD), key=lambda s: s.score)
    positive = sorted((s for s in a.sentences if s.score >= SENTENCE_THRESHOLD), key=lambda s: -s.score)
    if negative:
        line = f"The most negative passage is “{clip(negative[0].text, 160)}”"
        if a.avg_score <= -DOCUMENT_THRESHOLD:
            line += " If you need to act on this text, start there."
        notes.append(line)
    if positive:
        notes.append(f"The most positive passage is “{clip(positive[0].text, 160)}”")

    long_note = " Sentences this long can be hard to follow." if a.avg_sentence_length > 25 else ""
    notes.append(
        f"The text has {a.words:,} words in {count:,} sentences, about {a.avg_sentence_length} words per "
        f"sentence, and takes {reading_time(a.words)} to read.{long_note}"
    )
    return notes
