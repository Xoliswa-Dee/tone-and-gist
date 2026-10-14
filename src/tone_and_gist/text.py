"""Plain text helpers: sentence splitting and small formatting utilities."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List

_SENTENCE_RE = re.compile(r"[^.!?]+(?:[.!?]+[\"')\]]*|$)")
_WORD_RE = re.compile(r"[a-z']+")
MIN_WORDS_PER_SENTENCE = 3


@dataclass
class Sentence:
    text: str
    paragraph: int


def split_sentences(text: str) -> List[Sentence]:
    """Cut text into sentences, line by line. Fragments under three words are dropped."""
    out: List[Sentence] = []
    for index, line in enumerate(re.split(r"\n+", text)):
        line = line.strip()
        if not line:
            continue
        for part in _SENTENCE_RE.findall(line) or [line]:
            part = part.strip()
            if len(part.split()) >= MIN_WORDS_PER_SENTENCE:
                out.append(Sentence(part, index))
    return out


def lowercase_words(text: str) -> List[str]:
    return _WORD_RE.findall(text.lower())


def count_words(text: str) -> int:
    return len(text.split())


def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def fmt_signed(x: float, digits: int = 2) -> str:
    """Format with an explicit sign and a true minus, e.g. +0.12 or −0.40."""
    return ("−" if x < 0 else "+") + f"{abs(x):.{digits}f}"


def fmt_pct(x: float) -> str:
    return f"{round_half_up(x * 100)}%"


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].strip() + "…"


def reading_time(words: int, wpm: int = 230) -> str:
    minutes = words / wpm
    return "under 1 min" if minutes < 1 else f"{round_half_up(minutes)} min"
