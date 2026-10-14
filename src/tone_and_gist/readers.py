"""Read text out of uploaded files: .txt, .md, .csv, .docx and .pdf."""
from __future__ import annotations

import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_DOCX_XML_BYTES = 60 * 1024 * 1024
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".text"}
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class UnsupportedFileError(ValueError):
    """The file type is not supported or the file could not be read."""


def read_text(filename: str, data: bytes, max_chars: int = 300_000) -> str:
    """Return the text inside an uploaded file, or raise UnsupportedFileError."""
    if len(data) > MAX_FILE_BYTES:
        raise UnsupportedFileError("That file is over 15 MB. Try a smaller one or paste the text.")
    extension = os.path.splitext(filename or "")[1].lower()
    if extension in TEXT_EXTENSIONS:
        text = _decode(data)
    elif extension == ".docx":
        text = _read_docx(data)
    elif extension == ".pdf":
        text = _read_pdf(data, max_chars)
    else:
        raise UnsupportedFileError("That file type is not supported. Use .txt, .md, .csv, .docx or .pdf.")
    return text


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _read_docx(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > MAX_DOCX_XML_BYTES:
                raise UnsupportedFileError("That document is too large to read safely.")
            xml = archive.read(info)
    except (zipfile.BadZipFile, KeyError):
        raise UnsupportedFileError("That doesn't look like a valid .docx file.")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        raise UnsupportedFileError("That .docx file could not be parsed.")
    paragraphs = []
    for paragraph in root.iter(_W + "p"):
        parts = []
        for element in paragraph.iter():
            if element.tag == _W + "t":
                parts.append(element.text or "")
            elif element.tag in (_W + "tab", _W + "br"):
                parts.append(" ")
        line = "".join(parts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def _read_pdf(data: bytes, max_chars: int) -> str:
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError:
        raise UnsupportedFileError(
            "PDF support needs the optional 'pypdf' package. Install it with: pip install \"tone-and-gist[pdf]\""
        )
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise UnsupportedFileError("That PDF is password protected.")
        pages = []
        total = 0
        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            pages.append(text)
            total += len(text)
            if total >= max_chars:
                break
    except UnsupportedFileError:
        raise
    except (PdfReadError, ValueError, OSError):
        raise UnsupportedFileError("That PDF could not be read.")
    text = "\n\n".join(p for p in pages if p)
    if len(re.sub(r"\s", "", text)) < 30:
        raise UnsupportedFileError("This PDF has no selectable text. It may be a scan, which needs OCR first.")
    return text
