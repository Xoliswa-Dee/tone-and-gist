import unittest

from tone_and_gist.sentiment import DOCUMENT_THRESHOLD, SENTENCE_THRESHOLD, label_for, score_text


class ScoreTextTests(unittest.TestCase):
    def test_positive_and_negative_words(self):
        self.assertGreater(score_text("The service was excellent and the staff were helpful.").score, 0.3)
        self.assertLess(score_text("The service was terrible and the staff were rude.").score, -0.3)

    def test_text_without_scored_words_is_neutral(self):
        self.assertEqual(score_text("The meeting is on Tuesday at noon.").score, 0.0)
        self.assertEqual(score_text("").score, 0.0)

    def test_score_stays_between_minus_one_and_plus_one(self):
        loud = " ".join(["terrible awful horrible"] * 200)
        self.assertGreater(score_text(loud).score, -1.0)
        self.assertLess(score_text(loud).score, 0.0)

    def test_negation_flips_the_next_words(self):
        plain = score_text("The food was good.").score
        negated = score_text("The food was not good.").score
        self.assertGreater(plain, 0)
        self.assertLess(negated, 0)
        self.assertLess(abs(negated), abs(plain))  # flipped words are weakened

    def test_contraction_counts_as_negation(self):
        self.assertLess(score_text("It wasn't good at all.").score, 0)

    def test_negation_window_ends_at_punctuation_and_but(self):
        self.assertGreater(score_text("It was not here. It was good.").score, 0)
        self.assertGreater(score_text("It was not cheap but it was good.").score, 0)

    def test_intensifier_and_softener(self):
        base = score_text("The reply was bad.").score
        self.assertLess(score_text("The reply was extremely bad.").score, base)
        self.assertGreater(score_text("The reply was slightly bad.").score, base)

    def test_capitals_amplify(self):
        self.assertLess(score_text("This is BAD.").score, score_text("This is bad.").score)

    def test_redaction_marks_are_ignored(self):
        self.assertEqual(score_text("XXXX XXXX called me about XXXX.").score, 0.0)

    def test_longer_sentences_need_more_evidence(self):
        short = score_text("Bad service.").score
        long = score_text("Bad service " + "and so it goes on and on " * 8).score
        self.assertLess(short, long)  # both negative, the long one is closer to zero


class AnnotationTests(unittest.TestCase):
    def test_segments_rebuild_the_original_text(self):
        text = "It was not good, but the staff were very helpful!\nThanks."
        scored = score_text(text, annotate=True)
        self.assertEqual("".join(s.text for s in scored.segments), text)

    def test_scored_words_are_tagged(self):
        scored = score_text("The food was good but the room was awful.", annotate=True)
        tagged = {s.text: s.kind for s in scored.segments if s.kind}
        self.assertEqual(tagged, {"good": "pos", "awful": "neg"})

    def test_negated_word_tip_mentions_the_flip(self):
        scored = score_text("It was not good.", annotate=True)
        tip = next(s.tip for s in scored.segments if s.kind)
        self.assertIn("flipped by negation", tip)

    def test_annotation_does_not_change_the_score(self):
        text = "I really appreciate the quick help, though the delay was frustrating."
        self.assertEqual(score_text(text).score, score_text(text, annotate=True).score)


class LabelTests(unittest.TestCase):
    def test_label_thresholds(self):
        self.assertEqual(label_for(SENTENCE_THRESHOLD, SENTENCE_THRESHOLD), "pos")
        self.assertEqual(label_for(-SENTENCE_THRESHOLD, SENTENCE_THRESHOLD), "neg")
        self.assertEqual(label_for(0.0, SENTENCE_THRESHOLD), "neu")
        self.assertEqual(label_for(DOCUMENT_THRESHOLD - 0.01, DOCUMENT_THRESHOLD), "neu")


if __name__ == "__main__":
    unittest.main()
