from pathlib import Path

from fastapi.testclient import TestClient

from app.b1_control_adapter import import_b1_control_workbook
from app.db import SessionLocal
from app.main import app
from app.models import CockpitDecision, Project, ProjectExtractedField, ProjectSourceContent, ProjectSourceFile

CONTRACT = Path(__file__).resolve().parents[1] / "demo" / "b1" / "source" / "DEMO-B1-001_contract.txt"
CONTROL = Path(__file__).resolve().parents[1] / "demo" / "b1" / "assets" / "DEMO-B1-001_control.xlsx"


def _create_demo_project(client: TestClient):
    response = client.post("/projects", data={"code": "DEMO-B1-001", "pm_username": "pm_greco", "sales_username": "sales_riva"}, follow_redirects=False)
    assert response.status_code == 303


def _add_content(project_code: str, kind: str, content_type: str, text: str, name: str, metadata_json: str = "{}") -> int:
    with SessionLocal() as db:
        project = db.query(Project).filter_by(code=project_code).one()
        source = ProjectSourceFile(
            project_id=project.id,
            source_type="DOCUMENT" if kind == "DOCUMENT" else "OUTLOOK",
            file_name=name,
            relative_path=f"{project_code}/{'Documenti' if kind == 'DOCUMENT' else 'Outlook'}/{name}",
            size_bytes=len(text.encode("utf-8")),
            modified_at=project.created_at,
            sha256=("b" if kind == "DOCUMENT" else "c") * 64,
            is_present=True,
            change_status="UNCHANGED",
        )
        db.add(source)
        db.flush()
        content = ProjectSourceContent(
            project_id=project.id,
            source_file_id=source.id,
            source_hash=source.sha256,
            content_kind=kind,
            content_type=content_type,
            extracted_text=text,
            metadata_json=metadata_json,
        )
        db.add(content)
        db.commit()
        return content.id


def test_contract_analysis_extracts_core_fields_and_is_idempotent():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        _create_demo_project(client)
        _add_content("DEMO-B1-001", "DOCUMENT", "CONTRACT", CONTRACT.read_text(encoding="utf-8"), "DEMO-B1-001_contract.pdf")
        response = client.post("/project/DEMO-B1-001/ai/analyze", follow_redirects=False)
        assert response.status_code == 303
        detail = client.get("/api/projects/DEMO-B1-001").json()
        fields = {item["field_key"]: item for item in detail["extracted_fields"]}
        assert fields["customer_name"]["extracted_value"] == "Demo Process Industries S.p.A."
        assert fields["order_number"]["extracted_value"] == "PO-DEMO-2026-001"
        assert fields["order_date"]["extracted_value"] == "2026-01-15"
        assert fields["contract_value"]["extracted_value"] == "500000.00"
        assert fields["currency"]["extracted_value"] == "EUR"
        assert fields["contractual_delivery_date"]["extracted_value"] == "2026-10-15"
        assert fields["penalty_cap"]["confidence"] < 0.8
        assert fields["penalty_cap"]["operational_value"] is None
        count = len(fields)
        client.post("/project/DEMO-B1-001/ai/analyze", follow_redirects=False)
        assert len(client.get("/api/projects/DEMO-B1-001").json()["extracted_fields"]) == count


def test_human_review_applies_only_confirmed_contract_values_and_redirects():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        _create_demo_project(client)
        _add_content("DEMO-B1-001", "DOCUMENT", "CONTRACT", CONTRACT.read_text(encoding="utf-8"), "contract.pdf")
        client.post("/project/DEMO-B1-001/ai/analyze", follow_redirects=False)
        detail = client.get("/api/projects/DEMO-B1-001").json()
        fields = {item["field_key"]: item for item in detail["extracted_fields"]}

        pending = client.post(
            f"/api/extracted-fields/{fields['penalty_cap']['id']}/review",
            data={"status": "TO_VERIFY", "return_to": "/project/DEMO-B1-001#ai-analysis"},
            follow_redirects=False,
        )
        assert pending.status_code == 303
        with SessionLocal() as db:
            project = db.query(Project).filter_by(code="DEMO-B1-001").one()
            assert project.customer == "__PENDING__" and project.order_value == 0
            assert db.query(CockpitDecision).filter_by(project_id=project.id, decision_key="penalty_cap").count() == 0

        for key in ("customer_name", "contract_value", "order_number", "order_date", "currency", "payment_terms"):
            response = client.post(f"/api/extracted-fields/{fields[key]['id']}/review", data={"status": "CONFIRMED"}).json()
            assert response["provenance"] == "OPERATIONAL"

        after = client.get("/api/projects/DEMO-B1-001").json()
        assert after["customer"] == "Demo Process Industries S.p.A."
        assert after["order_value"] == 500000
        assert after["contract_value_known"] is True
        with SessionLocal() as db:
            project = db.query(Project).filter_by(code="DEMO-B1-001").one()
            assert len(project.customer_orders) == 1
            assert project.customer_orders[0].order_number == "PO-DEMO-2026-001"
            assert project.customer_orders[0].net_value == 500000


def test_cross_source_analysis_surfaces_galileo_outlook_and_unconfirmed_penalty_cap():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        _create_demo_project(client)
        _add_content("DEMO-B1-001", "DOCUMENT", "CONTRACT", CONTRACT.read_text(encoding="utf-8"), "contract.pdf")
        _add_content(
            "DEMO-B1-001", "EMAIL", "OUTLOOK_EMAIL",
            "We confirm EUR 50,000 has been paid. EUR 200,000 remains open and payment is expected by 30 September 2026.",
            "payment.eml", '{"sender":"finance@customer.example","subject":"Payment status INV-DEMO-001"}',
        )
        with SessionLocal() as db:
            import_b1_control_workbook(CONTROL.read_bytes(), db, expected_project_code="DEMO-B1-001")
        client.post("/project/DEMO-B1-001/ai/analyze", follow_redirects=False)
        payload = client.get("/api/projects/DEMO-B1-001").json()
        titles = {item["title"] for item in payload["ai_analysis"]["findings"]}
        assert "Sforamento economico rilevato" in titles
        assert "Incasso scaduto" in titles
        assert "Email collegata al pagamento rilevata" in titles
        assert "Cap penali da verificare" in titles
        assert payload["finance"]["overdue"] == 200000
        assert payload["control"]["budget_health"]["gross_overrun"] == 40000


def test_review_is_denied_for_project_outside_user_visibility():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        content_id = _add_content("P-26003", "DOCUMENT", "CONTRACT", "Customer: Hidden Customer", "hidden.pdf")
        created = client.post("/api/projects/P-26003/extracted-fields", data={
            "source_content_id": content_id, "field_key": "customer_name", "extracted_value": "Hidden Customer", "confidence": "0.9",
        }).json()
        client.post("/login", data={"username": "sales_riva"})
        response = client.post(f"/api/extracted-fields/{created['id']}/review", data={"status": "CONFIRMED"})
        assert response.status_code == 403
