import json
import unittest

from tone_and_gist import AnalysisError, analyze_text
from tone_and_gist.samples import load_samples


class SampleParityTests(unittest.TestCase):
    """The bundled samples should score the same as in the browser version."""

    def setUp(self):
        self.samples = load_samples()

    def test_email_is_mixed(self):
        a = analyze_text(self.samples["email"]["text"])
        self.assertEqual(a.verdict, "Mixed")
        self.assertEqual(round(a.avg_score, 2), 0.07)
        self.assertEqual(len(a.sentences), 9)
        self.assertAlmostEqual(a.shares["pos"], 4 / 9, places=3)

    def test_review_is_clearly_positive(self):
        a = analyze_text(self.samples["review"]["text"])
        self.assertEqual(a.verdict, "Clearly positive")
        self.assertEqual(a.verdict_tone, "pos")

    def test_update_is_mixed_and_balanced(self):
        a = analyze_text(self.samples["update"]["text"])
        self.assertTrue(a.verdict.startswith("Mixed"))
        self.assertEqual(a.emotions["fear"], 2)


class AnalyzeTextTests(unittest.TestCase):
    def test_too_short_text_is_rejected(self):
        with self.assertRaises(AnalysisError):
            analyze_text("Too short.")
        with self.assertRaises(AnalysisError):
            analyze_text("   ")

    def test_long_text_is_truncated(self):
        text = "The service was good and the staff were helpful. " * 50
        a = analyze_text(text, max_chars=500)
        self.assertTrue(a.truncated)
        self.assertLessEqual(len(a.text), 500)

    def test_shares_add_up_to_one(self):
        a = analyze_text(load_samples()["email"]["text"])
        self.assertAlmostEqual(sum(a.shares.values()), 1.0, places=6)

    def test_summaries_exist_for_every_length(self):
        a = analyze_text(load_samples()["email"]["text"])
        self.assertEqual(set(a.summaries), {"short", "medium", "long"})
        self.assertLessEqual(len(a.summaries["short"]), len(a.summaries["long"]))

    def test_tone_arc_is_one_value_per_sentence_when_short(self):
        a = analyze_text(load_samples()["email"]["text"])
        self.assertEqual(len(a.arc), len(a.sentences))

    def test_tone_arc_is_capped_at_twelve(self):
        text = "The service was good and the staff were helpful. " * 40
        self.assertEqual(len(analyze_text(text).arc), 12)

    def test_standouts_pick_the_extremes(self):
        a = analyze_text(load_samples()["email"]["text"])
        stand = a.standouts()
        self.assertIn("slow", stand["negative"][0].text)
        self.assertGreaterEqual(stand["positive"][0].score, stand["positive"][-1].score)

    def test_insights_are_written(self):
        a = analyze_text(load_samples()["email"]["text"])
        self.assertTrue(a.insights[0].startswith("Overall the text reads as mixed."))
        self.assertTrue(any("most negative passage" in line for line in a.insights))

    def test_to_dict_is_json_serialisable_and_complete(self):
        data = analyze_text(load_samples()["review"]["text"]).to_dict()
        json.dumps(data)
        for key in ("verdict", "avg_score", "shares", "sentences", "summaries", "keywords",
                    "emotions", "arc", "standouts", "insights", "annotated", "reading_time"):
            self.assertIn(key, data)
        self.assertEqual("".join(s["text"] for s in data["annotated"]), data["text"])


if __name__ == "__main__":
    unittest.main()
