from datetime import datetime
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import Project, ProjectSourceContent, ProjectSourceFile


def _content():
    with SessionLocal() as db:
        project = db.query(Project).filter_by(code="P-26001").one()
        source = ProjectSourceFile(
            project_id=project.id, source_type="DOCUMENT", file_name="contract.pdf",
            relative_path=f"P-26001/Documenti/contract-{datetime.utcnow().timestamp()}.pdf", size_bytes=10,
            modified_at=datetime.utcnow(), sha256="a" * 64, is_present=True,
            change_status="UNCHANGED",
        )
        db.add(source)
        db.flush()
        content = ProjectSourceContent(
            project_id=project.id, source_file_id=source.id, source_hash=source.sha256,
            content_kind="DOCUMENT", content_type="CONTRACT",
            extracted_text="contract text", metadata_json="{}",
        )
        db.add(content)
        db.commit()
        return content.id


def test_extracted_field_review_lifecycle_and_idempotency():
    with TestClient(app) as client:
        content_id = _content()
        created = client.post(
            "/api/projects/P-26001/extracted-fields",
            data={"source_content_id": content_id, "field_key": "customer_name", "extracted_value": "Acme", "confidence": "0.8"},
        ).json()
        assert created["created"] is True
        assert created["review_status"] == "NEW"
        assert created["provenance"] == "EXTRACTED"
        duplicate = client.post(
            "/api/projects/P-26001/extracted-fields",
            data={"source_content_id": content_id, "field_key": "customer_name", "extracted_value": "Other", "confidence": "0.1"},
        ).json()
        assert duplicate["created"] is False and duplicate["id"] == created["id"]

        detail = client.get("/api/projects/P-26001").json()
        field = next(x for x in detail["extracted_fields"] if x["id"] == created["id"])
        assert field["review_status"] == "NEW" and field["operational_value"] is None
        assert field["provenance"] == "EXTRACTED"

        confirmed = client.post(f"/api/extracted-fields/{created['id']}/review", data={"status": "CONFIRMED"}).json()
        assert confirmed["operational_value"] == "Acme" and confirmed["provenance"] == "OPERATIONAL"

        corrected = client.post(f"/api/projects/P-26001/extracted-fields", data={"source_content_id": content_id, "field_key": "delivery_date", "extracted_value": "2026-01-01", "confidence": "0.7"}).json()
        corrected_review = client.post(f"/api/extracted-fields/{corrected['id']}/review", data={"status": "CORRECTED", "corrected_value": "2026-02-01"}).json()
        assert corrected_review["operational_value"] == "2026-02-01"

        pending = client.post(f"/api/projects/P-26001/extracted-fields", data={"source_content_id": content_id, "field_key": "penalties", "extracted_value": "5%", "confidence": "0.4"}).json()
        to_verify = client.post(f"/api/extracted-fields/{pending['id']}/review", data={"status": "TO_VERIFY"}).json()
        assert to_verify["operational_value"] is None and to_verify["provenance"] == "REVIEWED"

        page = client.get("/project/P-26001").text
        assert "Analisi AI" in page
        assert "Cliente" in page
        assert "Conferma" in page and "Correggi" in page and "Da verificare" in page


def test_unreviewed_and_to_verify_fields_do_not_update_operational_project_data():
    with TestClient(app) as client:
        content_id = _content()
        before = client.get("/api/projects/P-26001").json()
        field = client.post("/api/projects/P-26001/extracted-fields", data={
            "source_content_id": content_id, "field_key": "customer_name", "extracted_value": "Real customer", "confidence": "1",
        }).json()
        after_extract = client.get("/api/projects/P-26001").json()
        assert after_extract["customer"] == before["customer"]
        client.post(f"/api/extracted-fields/{field['id']}/review", data={"status": "TO_VERIFY"})
        after_review = client.get("/api/projects/P-26001").json()
        assert after_review["customer"] == before["customer"]
        assert after_review["order_value"] == before["order_value"]
