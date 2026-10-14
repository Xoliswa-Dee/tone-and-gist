# How Tone & Gist works

Tone & Gist uses transparent rules rather than a black box, so each result can be explained. The work happens in five steps, and each step lives in its own module.

| Step | What happens | Module |
| --- | --- | --- |
| 1 | Split into sentences | `text.py` |
| 2 | Score the sentiment | `sentiment.py`, `lexicon.py` |
| 3 | Summarise | `summarize.py` |
| 4 | Read the mood | `analyzer.py`, `emotions.py` |
| 5 | Write the insights | `insights.py` |

## 1. Split into sentences

The text is cleaned and cut into sentences, line by line. Fragments under three words are ignored.

## 2. Score the sentiment

Each sentence is scored with a dictionary of about 400 words valued from −3 (terrible) to +3 (excellent).

- **Negation.** A word such as `not`, `never` or `didn't` flips the next three scored words and weakens them by about a quarter (they are multiplied by −0.74).
- **Intensity.** Words such as `extremely` amplify the next scored word, and `slightly` softens it. A scored word typed in capitals is amplified by 1.3.
- **Clause breaks.** Punctuation and the words `but`, `however` and `though` end any pending negation or intensifier.

The values are summed and squashed into the range −1 to +1:

```
score = s / sqrt(s^2 + 15 + n / 4)
```

where `s` is the sum of word values and `n` is the number of words. Long sentences therefore need more evidence to reach the extremes.

A sentence scoring **+0.20 or above is positive** and **−0.20 or below is negative**. Everything in between is neutral.

## 3. Summarise

The summary is **extractive**: it only picks sentences that already exist in the text.

1. Count how often each content word appears in the whole text.
2. Score each sentence by the sum of the frequencies of the unique content words it contains, divided by the square root of its length.
3. Give the opening sentence a 1.3× boost, and the next two a 1.1× boost.
4. Ignore sentences under 6 or over 55 words.
5. Pick the best sentences, skipping any that overlaps more than 60% with one already chosen.
6. Show the chosen sentences in their original order.

The three lengths pick 3, 5 and 8 sentences, never more than half of the sentences in the text.

## 4. Read the mood

- The **overall score** is the average sentence score.
- The **verdict** comes from that average and the share of positive, neutral and negative sentences. A text is called *mixed* when at least 25% of sentences are positive and at least 25% are negative. Otherwise an average of +0.08 or above reads as positive and −0.08 or below as negative, with "clearly" added beyond ±0.25.
- The **tone chart** averages sentences into up to 12 stretches from the start to the end of the text.
- **Emotion words** are counted from five small word lists: joy, trust, anger, fear and sadness.

## 5. Write the insights

Plain rules turn those numbers into sentences. They cover the overall mood, whether the text is factual or opinionated, whether the tone improves or worsens toward the end, the strongest emotion, and the most positive and most negative passages.

## Limits to keep in mind

- An extractive summary can only pick sentences that already exist. It cannot rephrase or combine ideas the way a language model can.
- A word list cannot read sarcasm, irony or context, and it works in English only.
- The emotion counts ignore negation, so treat them as a rough signal.
- PDFs need selectable text. Scanned pages need OCR first.
- Only the first 300,000 characters of a text are analyzed, and uploads are limited to 15 MB.

## Next steps

A trained text classifier, or a language model for the summary, would address the first two limits.
