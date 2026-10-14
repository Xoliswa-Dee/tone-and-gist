import io
import unittest

from tone_and_gist.readers import MAX_FILE_BYTES, UnsupportedFileError, read_text

from .helpers import make_docx, make_text_pdf

try:
    import pypdf  # noqa: F401
    HAS_PYPDF = True
except ImportError:  # pragma: no cover
    HAS_PYPDF = False


class TextFileTests(unittest.TestCase):
    def test_reads_plain_text_formats(self):
        for name in ("a.txt", "a.md", "a.markdown", "a.csv", "A.TXT"):
            self.assertEqual(read_text(name, b"Hello there."), "Hello there.")

    def test_strips_byte_order_mark_and_falls_back_to_cp1252(self):
        self.assertEqual(read_text("a.txt", b"\xef\xbb\xbfHello"), "Hello")
        self.assertEqual(read_text("a.txt", "caf\u00e9".encode("cp1252")), "caf\u00e9")

    def test_rejects_unknown_types_and_oversized_files(self):
        with self.assertRaises(UnsupportedFileError):
            read_text("picture.png", b"data")
        with self.assertRaises(UnsupportedFileError):
            read_text("a.txt", b"x" * (MAX_FILE_BYTES + 1))


class DocxTests(unittest.TestCase):
    def test_reads_paragraphs(self):
        data = make_docx(["First paragraph.", "Second & final paragraph."])
        self.assertEqual(read_text("notes.docx", data), "First paragraph.\nSecond & final paragraph.")

    def test_rejects_files_that_are_not_docx(self):
        with self.assertRaises(UnsupportedFileError):
            read_text("fake.docx", b"this is not a zip file")


@unittest.skipUnless(HAS_PYPDF, "pypdf is not installed")
class PdfTests(unittest.TestCase):
    def test_reads_selectable_text(self):
        text = read_text("report.pdf", make_text_pdf("The quarterly report looks very good this year"))
        self.assertIn("quarterly report", text)

    def test_blank_pdf_explains_ocr(self):
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        buffer = io.BytesIO()
        writer.write(buffer)
        with self.assertRaises(UnsupportedFileError) as caught:
            read_text("scan.pdf", buffer.getvalue())
        self.assertIn("OCR", str(caught.exception))

    def test_garbage_pdf_is_rejected(self):
        with self.assertRaises(UnsupportedFileError):
            read_text("bad.pdf", b"not a pdf at all")


if __name__ == "__main__":
    unittest.main()
