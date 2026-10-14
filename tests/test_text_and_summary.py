import unittest

from tone_and_gist.summarize import keywords, summarize
from tone_and_gist.text import clip, fmt_pct, fmt_signed, reading_time, split_sentences


class SplitSentencesTests(unittest.TestCase):
    def test_splits_on_end_punctuation(self):
        parts = split_sentences("This is one. This is two! Is this three?")
        self.assertEqual([p.text for p in parts], ["This is one.", "This is two!", "Is this three?"])

    def test_tracks_paragraphs_and_drops_tiny_fragments(self):
        parts = split_sentences("First line here.\n\nOk.\nSecond line here.")
        self.assertEqual([p.text for p in parts], ["First line here.", "Second line here."])
        self.assertEqual([p.paragraph for p in parts], [0, 2])

    def test_text_without_punctuation_is_one_sentence(self):
        self.assertEqual(len(split_sentences("just some words with no ending")), 1)


class FormatTests(unittest.TestCase):
    def test_formatting_helpers(self):
        self.assertEqual(fmt_signed(0.123), "+0.12")
        self.assertEqual(fmt_signed(-0.4), "−0.40")
        self.assertEqual(fmt_pct(0.445), "45%")
        self.assertEqual(clip("abcdef", 4), "abc…")
        self.assertEqual(clip("abc", 4), "abc")
        self.assertEqual(reading_time(100), "under 1 min")
        self.assertEqual(reading_time(2300), "10 min")


SENTENCES = [
    "The new portal has improved onboarding for every new hire this year.",
    "Onboarding with the portal is faster because the checklist guides every new hire.",
    "The cafeteria also changed its opening hours last month.",
    "Reporting in the portal crashed twice during our Monday review meeting.",
    "Onboarding with the portal is faster because the checklist guides every new hire.",
    "Short one.",
]


class SummarizeTests(unittest.TestCase):
    def test_returns_requested_count_in_original_order(self):
        picked = summarize(SENTENCES, 2)
        self.assertEqual(len(picked), 2)
        self.assertEqual(picked, sorted(picked))

    def test_skips_near_duplicates_and_tiny_sentences(self):
        picked = summarize(SENTENCES, 5)
        self.assertNotIn(5, picked)
        self.assertFalse({1, 4} <= set(picked))

    def test_opening_sentence_gets_a_boost(self):
        self.assertIn(0, summarize(SENTENCES, 1))

    def test_never_returns_more_than_half_the_sentences(self):
        self.assertLessEqual(len(summarize(SENTENCES[:4], 8)), 2)

    def test_handles_empty_input(self):
        self.assertEqual(summarize([], 3), [])


class KeywordTests(unittest.TestCase):
    def test_repeated_phrases_come_first(self):
        word, count = keywords(SENTENCES)[0]
        self.assertEqual(len(word.split()), 2)
        self.assertGreaterEqual(count, 2)

    def test_words_inside_a_phrase_are_not_repeated_on_their_own(self):
        found = [w for w, _ in keywords(SENTENCES)]
        self.assertIn("checklist guides", found)
        self.assertNotIn("checklist", found)

    def test_stopwords_and_short_words_are_ignored(self):
        words = [w for w, _ in keywords(["The cat and the dog sat on the mat today."])]
        self.assertNotIn("the", words)
        self.assertNotIn("cat", words)  # three letters or fewer


if __name__ == "__main__":
    unittest.main()
