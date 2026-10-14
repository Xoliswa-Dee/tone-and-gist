import json
import threading
import unittest
import urllib.error
import urllib.request
from urllib.parse import quote

from tone_and_gist.server import create_server

from .helpers import make_docx

TEXT = "The launch went well and the team was proud. The only problem was a slow server that crashed twice."


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0, quiet=True)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, path, data=None, headers=None, method=None):
        req = urllib.request.Request(self.base + path, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.headers, error.read()

    def post_json(self, payload):
        return self.request("/api/analyze", json.dumps(payload).encode(), {"Content-Type": "application/json"})

    def test_serves_the_web_app(self):
        for path, kind in (("/", "text/html"), ("/style.css", "text/css"), ("/app.js", "application/javascript")):
            status, headers, body = self.request(path)
            self.assertEqual(status, 200, path)
            self.assertTrue(headers["Content-Type"].startswith(kind), path)
            self.assertTrue(body)

    def test_security_headers(self):
        _, headers, _ = self.request("/")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_samples(self):
        status, _, body = self.request("/api/samples")
        self.assertEqual(status, 200)
        self.assertEqual(set(json.loads(body)), {"email", "review", "update"})

    def test_analyze_text(self):
        status, _, body = self.post_json({"text": TEXT})
        data = json.loads(body)
        self.assertEqual(status, 200)
        self.assertIn("verdict", data)
        self.assertEqual(data["text"], TEXT)

    def test_analyze_file(self):
        docx = make_docx([TEXT])
        status, _, body = self.request(
            "/api/analyze-file", docx, {"X-Filename": quote("Q3 notes.docx"), "Content-Type": "application/octet-stream"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["text"], TEXT)

    def test_bad_requests_get_clear_errors(self):
        status, _, body = self.post_json({"text": "Too short."})
        self.assertEqual(status, 422)
        self.assertIn("two sentences", json.loads(body)["error"])
        self.assertEqual(self.post_json({"nope": 1})[0], 422)
        self.assertEqual(self.post_json({"text": 5})[0], 422)
        status, _, _ = self.request("/api/analyze", b"not json", {"Content-Type": "application/json"})
        self.assertEqual(status, 422)
        status, _, body = self.request("/api/analyze-file", b"data", {"X-Filename": "photo.png"})
        self.assertEqual(status, 422)
        self.assertIn("not supported", json.loads(body)["error"])

    def test_unknown_paths_and_traversal_are_404(self):
        for path in ("/nope", "/../pyproject.toml", "/%2e%2e/pyproject.toml", "/web/index.html", "/api/other"):
            self.assertEqual(self.request(path)[0], 404, path)
        self.assertEqual(self.request("/api/other", b"{}", method="POST")[0], 404)


if __name__ == "__main__":
    unittest.main()
