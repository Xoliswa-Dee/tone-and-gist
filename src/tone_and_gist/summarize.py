"""Extractive summary and key topics.

The summary only ever picks sentences that already exist in the text. Each
sentence is ranked by how many of the document's most frequent words it
contains, then the best ones are returned in their original order.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Sequence, Set, Tuple

from .lexicon import STOPWORDS
from .text import lowercase_words

SUMMARY_SIZES = {"short": 3, "medium": 5, "long": 8}
MIN_SENTENCE_WORDS = 6
MAX_SENTENCE_WORDS = 55
DUPLICATE_OVERLAP = 0.6


def _content_words(words: Sequence[str]) -> List[str]:
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]


def summarize(sentences: Sequence[str], count: int) -> List[int]:
    """Return the indexes of the ``count`` most representative sentences, in order."""
    count = min(count, max(1, math.ceil(len(sentences) * 0.5)))
    tokens = [lowercase_words(s) for s in sentences]

    frequency: Counter = Counter()
    for words in tokens:
        frequency.update(_content_words(words))
    top = max(frequency.values(), default=1)

    candidates: List[Tuple[int, float, Set[str]]] = []
    for index, words in enumerate(tokens):
        if not MIN_SENTENCE_WORDS <= len(words) <= MAX_SENTENCE_WORDS:
            continue
        unique = set(_content_words(words))
        score = sum(frequency[w] / top for w in unique) / math.sqrt(len(words) or 1)
        if index == 0:
            score *= 1.3
        elif index < 3:
            score *= 1.1
        candidates.append((index, score, unique))

    candidates.sort(key=lambda c: -c[1])  # stable: ties keep text order
    chosen: List[Tuple[int, float, Set[str]]] = []
    for candidate in candidates:
        if len(chosen) >= count:
            break
        _, _, words = candidate
        duplicate = any(
            len(words & other) / max(1, min(len(words), len(other))) > DUPLICATE_OVERLAP
            for _, _, other in chosen
        )
        if not duplicate:
            chosen.append(candidate)
    return sorted(index for index, _, _ in chosen)


def summaries_by_length(sentences: Sequence[str]) -> Dict[str, List[int]]:
    return {name: summarize(sentences, size) for name, size in SUMMARY_SIZES.items()}


def keywords(sentences: Sequence[str], limit: int = 10) -> List[Tuple[str, int]]:
    """Repeated two-word phrases first, then the most frequent single words."""
    singles: Counter = Counter()
    pairs: Counter = Counter()
    for sentence in sentences:
        previous = None
        for word in lowercase_words(sentence):
            if len(word) > 3 and word not in STOPWORDS:
                singles[word] += 1
                if previous:
                    pairs[f"{previous} {word}"] += 1
                previous = word
            else:
                previous = None
    top_pairs = [(p, c) for p, c in pairs.items() if c >= 2]
    top_pairs.sort(key=lambda pc: -pc[1])
    top_pairs = top_pairs[:4]
    used = {w for pair, _ in top_pairs for w in pair.split()}
    rest = sorted(((w, c) for w, c in singles.items() if w not in used), key=lambda wc: (-wc[1], wc[0]))
    return top_pairs + rest[: max(0, limit - len(top_pairs))]
