"""Rule-based sentiment scoring.

Each word is looked up in a small dictionary. Negation, intensifiers and a few
other rules adjust the values, and the sum is squashed into the range -1 to +1:

    score = s / sqrt(s^2 + 15 + n / 4)

where ``s`` is the sum of word values and ``n`` the number of words.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import List, Optional

from .lexicon import BOOSTERS, LEXICON, NEGATIONS
from .text import fmt_signed

SENTENCE_THRESHOLD = 0.2   # a sentence at or beyond this is positive / negative
DOCUMENT_THRESHOLD = 0.08  # the same idea for a whole-text average
NEGATION_WINDOW = 3        # a negation affects this many following words
NEGATION_FACTOR = -0.74    # flipped and slightly weakened
CAPS_FACTOR = 1.3

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z']*|[.!?;:,\n]")
_REDACTION_RE = re.compile(r"X+")
_CLAUSE_BREAKS = frozenset({"but", "however", "though"})


@dataclass
class Segment:
    """A run of text for the annotated view. ``kind`` is 'pos', 'neg' or None."""

    text: str
    kind: Optional[str] = None
    tip: Optional[str] = None


@dataclass
class TextScore:
    score: float
    hits: int  # how many dictionary words were found
    segments: List[Segment] = field(default_factory=list)


def label_for(score: float, threshold: float) -> str:
    if score >= threshold:
        return "pos"
    if score <= -threshold:
        return "neg"
    return "neu"


def _add_plain(segments: List[Segment], text: str) -> None:
    if not text:
        return
    if segments and segments[-1].kind is None:
        segments[-1].text += text
    else:
        segments.append(Segment(text))


def score_text(text: str, annotate: bool = False) -> TextScore:
    """Score ``text``. With ``annotate`` the result also lists the scored words."""
    total = 0.0
    word_count = 0
    hits = 0
    negation_left = 0
    boost = 1.0
    boost_left = 0
    last = 0
    segments: List[Segment] = []

    for match in _TOKEN_RE.finditer(text):
        raw = match.group(0)
        if annotate:
            _add_plain(segments, text[last:match.start()])
        last = match.end()
        kind: Optional[str] = None
        tip: Optional[str] = None

        if not raw[0].isalpha():  # punctuation ends any pending negation or boost
            negation_left = 0
            boost_left = 0
            boost = 1.0
        else:
            word_count += 1
            word = raw.lower().replace("'", "")
            if word in _CLAUSE_BREAKS:
                negation_left = 0
                boost_left = 0
                boost = 1.0
            elif word in NEGATIONS:
                negation_left = NEGATION_WINDOW
            elif word in BOOSTERS:
                boost = BOOSTERS[word]
                boost_left = 3
            elif word in LEXICON:
                value = float(LEXICON[word])
                if boost_left > 0:
                    value *= boost
                if len(raw) > 2 and raw == raw.upper() and not _REDACTION_RE.fullmatch(raw):
                    value *= CAPS_FACTOR
                flipped = negation_left > 0
                if flipped:
                    value *= NEGATION_FACTOR
                total += value
                hits += 1
                kind = "neg" if value < 0 else "pos"
                tip = fmt_signed(value, 1) + (" (flipped by negation)" if flipped else "")
                boost_left = 0
                boost = 1.0
            if negation_left > 0 and word not in NEGATIONS:
                negation_left -= 1
            if boost_left > 0 and word not in BOOSTERS:
                boost_left -= 1

        if annotate:
            if kind:
                segments.append(Segment(raw, kind, tip))
            else:
                _add_plain(segments, raw)

    if annotate:
        _add_plain(segments, text[last:])

    score = total / math.sqrt(total * total + 15 + word_count / 4) if word_count else 0.0
    return TextScore(score, hits, segments)
