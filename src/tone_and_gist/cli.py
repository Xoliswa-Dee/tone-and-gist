"""Command line interface: ``tone-and-gist analyze`` and ``tone-and-gist serve``."""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import List, Optional

from . import __version__
from .analyzer import Analysis, AnalysisError, analyze_text
from .lexicon import EMOTION_LABELS
from .readers import UnsupportedFileError, read_text
from .samples import load_samples
from .text import fmt_pct, fmt_signed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tone-and-gist",
        description="Summarise text and analyse its sentiment.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="analyze a file, standard input or a bundled sample")
    analyze.add_argument("file", nargs="?", help="path to a .txt, .md, .csv, .docx or .pdf file, or - for standard input")
    analyze.add_argument("--sample", choices=sorted(load_samples()), help="analyze a bundled sample instead of a file")
    analyze.add_argument("--length", choices=("short", "medium", "long"), default="medium", help="summary length (default: medium)")
    analyze.add_argument("--json", action="store_true", help="print the full result as JSON")

    serve = sub.add_parser("serve", help="start the web app")
    serve.add_argument("--host", default="127.0.0.1", help="address to listen on (default: 127.0.0.1)")
    serve.add_argument("--port", type=int, default=8000, help="port to listen on (default: 8000)")
    return parser


def _wrap(text: str, indent: str = "  ", bullet: str = "") -> str:
    return textwrap.fill(text, width=88, initial_indent=indent + bullet, subsequent_indent=indent + " " * len(bullet))


def format_report(analysis: Analysis, title: str, length: str = "medium") -> str:
    shares = analysis.shares
    lines: List[str] = [
        f"Tone & Gist report: {title}",
        "=" * 60,
        f"Mood:      {analysis.verdict} (average sentence score {fmt_signed(analysis.avg_score)})",
        f"Sentences: {fmt_pct(shares['pos'])} positive, {fmt_pct(shares['neu'])} neutral, {fmt_pct(shares['neg'])} negative",
        f"Length:    {analysis.words:,} words in {len(analysis.sentences):,} sentences",
        "",
        f"Summary ({length})",
    ]
    for sentence in analysis.summary_sentences(length):
        lines.append(_wrap(sentence.text, bullet="- "))
    lines += ["", "Key topics: " + ", ".join(w for w, _ in analysis.keywords)]
    emotions = ", ".join(f"{EMOTION_LABELS[k].lower()} {v}" for k, v in analysis.emotions.items() if v)
    lines.append("Emotion words: " + (emotions or "none found"))
    lines += ["", "Insights"]
    for note in analysis.insights:
        lines.append(_wrap(note, bullet="- "))
    if analysis.truncated:
        lines += ["", "Note: only the first 300,000 characters were analyzed."]
    return "\n".join(lines)


def _load_input(args: argparse.Namespace) -> tuple:
    if args.sample:
        return load_samples()[args.sample]["text"], f"sample '{args.sample}'"
    if not args.file or args.file == "-":
        if sys.stdin.isatty() and not args.file:
            raise UnsupportedFileError("Give a file path, use - to read standard input, or pass --sample NAME.")
        return sys.stdin.read(), "standard input"
    try:
        with open(args.file, "rb") as handle:
            data = handle.read()
    except OSError as error:
        raise UnsupportedFileError(f"Could not open {args.file}: {error.strerror}")
    return read_text(args.file, data), args.file


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        from .server import serve

        serve(args.host, args.port)
        return 0
    try:
        text, title = _load_input(args)
        analysis = analyze_text(text)
    except (AnalysisError, UnsupportedFileError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    try:
        if args.json:
            print(json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(format_report(analysis, title, args.length))
        sys.stdout.flush()
    except BrokenPipeError:  # for example: tone-and-gist analyze file.txt | head
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 0
