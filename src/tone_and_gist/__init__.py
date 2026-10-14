"""Tone & Gist: summarise text and analyse its sentiment."""
from .analyzer import Analysis, AnalysisError, analyze_text

__version__ = "1.0.0"
__all__ = ["Analysis", "AnalysisError", "analyze_text", "__version__"]
