# Web API

Start the server with `tone-and-gist serve`. Every analysis endpoint returns the same JSON object.

## `GET /api/samples`

Returns the bundled sample texts: `{"email": {"title": "Customer email", "text": "..."}, ...}`.

## `POST /api/analyze`

Send JSON with the text to analyze.

```bash
curl -s http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The launch went well and the team was proud. The only problem was a slow server."}'
```

## `POST /api/analyze-file`

Send the raw file bytes as the body, and the file name in an `X-Filename` header (URL-encoded). The file extension decides how it is read.

```bash
curl -s http://127.0.0.1:8000/api/analyze-file \
  -H "X-Filename: report.docx" \
  --data-binary @report.docx
```

## Response

| Field | Meaning |
| --- | --- |
| `verdict`, `verdict_tone` | Overall mood in words, and `pos`, `neg` or `neu` |
| `avg_score` | Average sentence score from −1 to +1 |
| `shares` | Share of `pos`, `neu` and `neg` sentences (0 to 1) |
| `sentences` | Each sentence with its `text`, `score` and `label` |
| `summaries` | Sentence indexes for the `short`, `medium` and `long` summaries |
| `keywords` | Key topics as `{word, count}` |
| `emotions` | Word counts for `joy`, `trust`, `anger`, `fear`, `sadness` |
| `arc` | Average score for up to 12 stretches of the text |
| `standouts` | The most `positive` and `negative` sentences |
| `insights` | Written insights |
| `annotated` | The text as segments `{text, kind, tip}` for highlighting scored words |
| `words`, `reading_time`, `avg_sentence_length`, `opinionated_share`, `truncated`, `text` | Basic facts about the text |

## Errors

Errors return `{"error": "..."}`. A text that is too short, an unsupported file or a malformed request returns **422**. A missing `Content-Length` returns **411**, an oversized request **413**, and an unknown path **404**.
