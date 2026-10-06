from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

import app.source_readers as readers
from app.source_readers import SourceReadError, read_source_content

PDF = Path(__file__).resolve().parents[1] / "demo" / "b1" / "assets" / "DEMO-B1-001_contract.pdf"


def test_reads_text_pdf_and_docx():
    original = PDF.read_bytes()
    pdf = read_source_content(original, PDF.name, "DOCUMENT")
    assert pdf.content_kind == "DOCUMENT" and pdf.extracted_text
    assert PDF.read_bytes() == original
    document = Document()
    document.add_paragraph("Technical specification for thermal unit")
    buffer = BytesIO()
    document.save(buffer)
    docx = read_source_content(buffer.getvalue(), "spec.docx", "DOCUMENT")
    assert docx.content_type == "TECHNICAL_SPEC" and "Technical specification" in docx.extracted_text


def test_rejects_non_text_pdf_and_reads_eml(monkeypatch):
    with pytest.raises(SourceReadError):
        read_source_content(b"not-a-pdf", "scan.pdf", "DOCUMENT")
    eml = b"From: sender@example.com\nTo: recipient@example.com\nCc: cc@example.com\nSubject: Test\nDate: Tue, 01 Sep 2026 10:00:00 +0000\nMIME-Version: 1.0\nContent-Type: text/plain\n\nBody text"
    email = read_source_content(eml, "message.eml", "OUTLOOK")
    assert email.content_kind == "EMAIL" and '"sender": "sender@example.com"' in email.metadata_json
    class FakeMessage:
        sender = "sender@example.com"; to = "recipient@example.com"; cc = "cc@example.com"; date = "2026-09-01"; subject = "MSG"; body = "MSG body"; attachments = []
    monkeypatch.setattr(readers, "Message", lambda _: FakeMessage())
    msg = read_source_content(b"msg", "message.msg", "OUTLOOK")
    assert msg.content_type == "OUTLOOK_EMAIL" and msg.extracted_text == "MSG body"