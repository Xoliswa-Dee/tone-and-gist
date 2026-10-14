"""Rough emotion counts from five small word lists (joy, trust, anger, fear, sadness)."""
from __future__ import annotations

from typing import Dict

from .lexicon import EMOTION_WORDS
from .text import lowercase_words


def count_emotions(text: str) -> Dict[str, int]:
    """Count words per emotion. Negation is ignored, so treat the result as a rough signal."""
    counts = {name: 0 for name in EMOTION_WORDS}
    for word in lowercase_words(text):
        for name, words in EMOTION_WORDS.items():
            if word in words:
                counts[name] += 1
    return counts
