# Tone & Gist

Tone & Gist summarises a piece of text and analyses its mood. Give it an email, review, article or report and it returns a short summary, a sentiment verdict, how the tone moves from start to end, and written insights.

It is written in Python and **the core has no dependencies**, only the standard library. Use it as a command line tool, a small web app, or a Python library.

## Features

- **Summary** at three lengths, picked from the text's own sentences
- **Sentiment** for every sentence and for the whole text, with negation and intensity rules
- **Mood** details: positive, neutral and negative shares, a tone-over-time chart, and joy, trust, anger, fear and sadness word counts
- **Insights** written in plain language, plus the most positive and negative passages
- **Inputs:** pasted text, `.txt`, `.md`, `.csv`, `.docx`, and `.pdf` with selectable text
- Every score can be traced back to a word. See [how it works](docs/how-it-works.md).

## Quick start

You need Python 3.9 or newer.

```bash
git clone https://github.com/Xoliswa-Dee/tone-and-gist
cd tone-and-gist
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[pdf]"          # drop [pdf] if you do not need PDF support
```

Try it on a bundled sample:

```bash
tone-and-gist analyze --sample review --length short
```

```text
Tone & Gist report: sample 'review'
============================================================
Mood:      Clearly positive (average sentence score +0.29)
Sentences: 88% positive, 0% neutral, 13% negative
Length:    95 words in 8 sentences

Summary (short)
  - I bought this blender three months ago and I love it.
  - It crushes ice without any fuss and the smoothies come out perfectly smooth.
  - The price felt high when I ordered it, but I now think it was worth every penny.
...
```

Percentages are rounded separately, so they can add up to 101%.

## Command line

```bash
tone-and-gist analyze report.docx            # a file (.txt .md .csv .docx .pdf)
cat notes.txt | tone-and-gist analyze -      # standard input
tone-and-gist analyze notes.txt --json       # the full result as JSON
tone-and-gist analyze --sample email         # bundled samples: email, review, update
tone-and-gist serve --port 8000              # the web app
```

Without installing, run it straight from the source folder:

```bash
PYTHONPATH=src python -m tone_and_gist serve
```

## Web app

```bash
tone-and-gist serve
```

Open <http://127.0.0.1:8000>. Paste text or drop a file onto the box. The browser only draws the results. All analysis runs in the Python server on your own machine, and the server listens on `127.0.0.1` by default. The endpoints are described in [docs/api.md](docs/api.md).

## Use it as a library

```python
from tone_and_gist import analyze_text

result = analyze_text("The launch went well and the team was proud. The only problem was a slow server.")
print(result.verdict, round(result.avg_score, 2))
for sentence in result.summary_sentences("short"):
    print("-", sentence.text)
print(result.insights)
data = result.to_dict()   # JSON-ready
```

`analyze_text` raises `AnalysisError` when the text is too short (under about 15 words or two sentences).

## Project layout

```text
src/tone_and_gist/
  lexicon.py      word lists: sentiment values, negations, intensifiers, emotions, stop words
  text.py         sentence splitting and formatting helpers
  sentiment.py    rule-based sentence and text scoring
  summarize.py    extractive summary and key topics
  emotions.py     joy / trust / anger / fear / sadness counts
  insights.py     turns the numbers into written insights
  analyzer.py     the pipeline, and the Analysis result
  readers.py      .txt .md .csv .docx .pdf to text
  cli.py          command line interface
  server.py       web server (standard library)
  web/            index.html, style.css, app.js
  samples/        bundled sample texts
tests/            unit tests (unittest)
docs/             how-it-works.md, api.md
```

## Tests

```bash
python -m unittest discover -s tests -t .
```

The suite also runs under `pytest` if you install it (`pip install -e ".[dev]"`). PDF tests are skipped when `pypdf` is not installed.

## Docker

```bash
docker build -t tone-and-gist .
docker run --rm -p 8000:8000 tone-and-gist
```

The Docker setup has not been run yet. Check it builds on your machine before relying on it.

## Limits

- The summary only picks existing sentences. It cannot rephrase.
- A word list cannot read sarcasm or context, and it works in English only.
- Scanned PDFs need OCR first.
- Only the first 300,000 characters are analyzed, and uploads are limited to 15 MB.

The natural next step is a trained text classifier, or a language model for the summary. The full list of limits is in [docs/how-it-works.md](docs/how-it-works.md).

## License

MIT. See [LICENSE](LICENSE).
