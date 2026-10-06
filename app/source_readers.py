from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path

from docx import Document

try:
    from extract_msg import Message
except ImportError:  # .msg support is optional until the dependency is installed
    Message = None
from pypdf import PdfReader


class SourceReadError(ValueError):
    pass


@dataclass(frozen=True)
class ReadContent:
    content_kind: str
    content_type: str
    extracted_text: str
    metadata_json: str


def _document_type(name: str, text: str) -> str:
    sample = f"{name} {text[:1200]}".lower()
    if any(word in sample for word in ("contract", "contratto", "agreement")):
        return "CONTRACT"
    if any(word in sample for word in ("purchase order", "customer order", "ordine cliente", "po ")):
        return "CUSTOMER_ORDER"
    if any(word in sample for word in ("technical specification", "specifica tecnica", "datasheet")):
        return "TECHNICAL_SPEC"
    return "OTHER"


def _document(content: bytes, filename: str) -> ReadContent:
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages).strip()
        elif suffix == ".docx":
            text = "\n".join(paragraph.text for paragraph in Document(BytesIO(content)).paragraphs).strip()
        else:
            raise SourceReadError("Formato documento non supportato.")
    except SourceReadError:
        raise
    except Exception as exc:
        raise SourceReadError("Documento non leggibile.") from exc
    if not text:
        raise SourceReadError("Documento senza testo estraibile; OCR non disponibile.")
    return ReadContent(
        "DOCUMENT",
        _document_type(filename, text),
        text,
        json.dumps({"filename": filename, "format": suffix[1:].upper()}, ensure_ascii=False),
    )


def _addresses(value) -> list[str]:
    if not value:
        return []
    return [str(value)] if isinstance(value, str) else [str(item) for item in value]


def _eml(content: bytes) -> ReadContent:
    try:
        message = BytesParser(policy=policy.default).parsebytes(content)
        body = message.get_body(preferencelist=("plain",))
        text = body.get_content() if body else ""
        attachments = [part.get_filename() for part in message.iter_attachments() if part.get_filename()]
    except Exception as exc:
        raise SourceReadError("Email EML non leggibile.") from exc
    if not (message.get("Subject") or text):
        raise SourceReadError("Email EML senza contenuto leggibile.")
    metadata = {
        "sender": message.get("From", ""),
        "recipients": _addresses(message.get_all("To", [])),
        "cc": _addresses(message.get_all("Cc", [])),
        "sent_at": message.get("Date"),
        "subject": message.get("Subject", ""),
        "attachment_names": attachments,
    }
    return ReadContent("EMAIL", "OUTLOOK_EMAIL", text.strip(), json.dumps(metadata, ensure_ascii=False))


def _msg(content: bytes) -> ReadContent:
    temp = tempfile.NamedTemporaryFile(suffix=".msg", delete=False)
    try:
        temp.write(content)
        temp.close()
        if Message is None:
            raise SourceReadError("Lettura MSG non disponibile: installare extract-msg.")
        message = Message(temp.name)
        attachments = [
            getattr(item, "longFilename", None) or getattr(item, "shortFilename", None) for item in message.attachments
        ]
        metadata = {
            "sender": message.sender or "",
            "recipients": _addresses(message.to),
            "cc": _addresses(message.cc),
            "sent_at": str(message.date) if message.date else None,
            "subject": message.subject or "",
            "attachment_names": [item for item in attachments if item],
        }
        text = (message.body or "").strip()
    except Exception as exc:
        raise SourceReadError("Email MSG non leggibile.") from exc
    finally:
        try:
            temp.close()
            Path(temp.name).unlink(missing_ok=True)
        except OSError:
            pass
    if not (metadata["subject"] or text):
        raise SourceReadError("Email MSG senza contenuto leggibile.")
    return ReadContent("EMAIL", "OUTLOOK_EMAIL", text, json.dumps(metadata, ensure_ascii=False))


def read_source_content(content: bytes, filename: str, source_type: str) -> ReadContent:
    if source_type == "DOCUMENT":
        return _document(content, filename)
    if source_type == "OUTLOOK":
        suffix = Path(filename).suffix.lower()
        if suffix == ".eml":
            return _eml(content)
        if suffix == ".msg":
            return _msg(content)
    raise SourceReadError("Formato sorgente non supportato.")
