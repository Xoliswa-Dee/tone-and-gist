import contextlib
import io
import json
import os
import tempfile
import unittest

from tone_and_gist.cli import main


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_sample_report(self):
        code, out, _ = run("analyze", "--sample", "email")
        self.assertEqual(code, 0)
        self.assertIn("Mood:      Mixed", out)
        self.assertIn("Summary (medium)", out)
        self.assertIn("Insights", out)

    def test_summary_length_option(self):
        def summary_bullets(output):
            section = output.split("Key topics:")[0].split("Summary (")[1]
            return section.count("\n  - ")

        _, short, _ = run("analyze", "--sample", "email", "--length", "short")
        _, long, _ = run("analyze", "--sample", "email", "--length", "long")
        self.assertEqual(summary_bullets(short), 3)
        self.assertGreater(summary_bullets(long), summary_bullets(short))

    def test_json_output(self):
        code, out, _ = run("analyze", "--sample", "review", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["verdict"], "Clearly positive")

    def test_analyze_a_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "note.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("The launch went well and the team was proud. The only problem was a slow server.")
            code, out, _ = run("analyze", path)
        self.assertEqual(code, 0)
        self.assertIn("note.txt", out)

    def test_errors_exit_with_code_two(self):
        code, _, err = run("analyze", "does-not-exist.txt")
        self.assertEqual(code, 2)
        self.assertIn("error:", err)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "tiny.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("Too short.")
            code, _, err = run("analyze", path)
        self.assertEqual(code, 2)
        self.assertIn("two sentences", err)


if __name__ == "__main__":
    unittest.main()
