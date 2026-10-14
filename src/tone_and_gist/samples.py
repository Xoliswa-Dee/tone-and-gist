"""Bundled sample texts (stored as plain files in the ``samples`` folder)."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

_FOLDER = Path(__file__).parent / "samples"
TITLES = {"email": "Customer email", "review": "Product review", "update": "Company update"}


def load_samples() -> Dict[str, Dict[str, str]]:
    """Return {name: {"title": ..., "text": ...}} for every bundled sample."""
    out: Dict[str, Dict[str, str]] = {}
    for name, title in TITLES.items():
        path = _FOLDER / f"{name}.txt"
        if path.is_file():
            out[name] = {"title": title, "text": path.read_text(encoding="utf-8").strip()}
    return out
