from contextlib import contextmanager
from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

ASSETS = Path(__file__).resolve().parents[1] / "demo" / "b1" / "assets"


@contextmanager
def configured_source_root(path):
    previous = settings.source_root
    object.__setattr__(settings, "source_root", path)
    try:
        yield
    finally:
        object.__setattr__(settings, "source_root", previous)


def _copy_sources(root: Path):
    project = root / "DEMO-B1-001"
    mapping = {
        "Galileo": "DEMO-B1-001_control.xlsx",
        "Documenti": "DEMO-B1-001_contract.pdf",
        "Outlook": "DEMO-B1-001_payment_followup.eml",
    }
    for folder, filename in mapping.items():
        target = project / folder
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ASSETS / filename, target / filename)


def test_b1_end_to_end_source_to_review(tmp_path):
    with configured_source_root(tmp_path), TestClient(app) as client:
        client.post("/api/demo/reset")
        created = client.post(
            "/projects",
            data={"code": "DEMO-B1-001", "pm_username": "pm_greco", "sales_username": "sales_riva"},
            follow_redirects=False,
        )
        assert created.status_code == 303
        _copy_sources(tmp_path)

        assert client.post("/project/DEMO-B1-001/sources/refresh", follow_redirects=False).status_code == 303
        page = client.get("/project/DEMO-B1-001").text
        assert "DEMO-B1-001_control.xlsx" in page
        assert "DEMO-B1-001_contract.pdf" in page
        assert "DEMO-B1-001_payment_followup.eml" in page

        assert client.post("/project/DEMO-B1-001/sources/galileo/import", follow_redirects=False).status_code == 303
        assert client.post("/project/DEMO-B1-001/sources/DOCUMENT/read", follow_redirects=False).status_code == 303
        assert client.post("/project/DEMO-B1-001/sources/OUTLOOK/read", follow_redirects=False).status_code == 303
        assert client.post("/project/DEMO-B1-001/ai/analyze", follow_redirects=False).status_code == 303

        payload = client.get("/api/projects/DEMO-B1-001").json()
        assert payload["extracted_summary"]["sources_analyzed"] == 3
        assert payload["control"]["operational_budget"] == 360000
        assert payload["finance"]["overdue"] == 200000
        fields = {item["field_key"]: item for item in payload["extracted_fields"]}
        assert fields["customer_name"]["extracted_value"] == "Demo Process Industries S.p.A."
        assert fields["penalty_cap"]["operational_value"] is None
        titles = {item["title"] for item in payload["ai_analysis"]["findings"]}
        assert "Email collegata al pagamento rilevata" in titles

        for key in ("customer_name", "contract_value"):
            response = client.post(
                f"/api/extracted-fields/{fields[key]['id']}/review",
                data={"status": "CONFIRMED", "return_to": "/project/DEMO-B1-001#ai-analysis"},
                follow_redirects=False,
            )
            assert response.status_code == 303
        client.post(
            f"/api/extracted-fields/{fields['penalty_cap']['id']}/review",
            data={"status": "TO_VERIFY"},
        )

        final_payload = client.get("/api/projects/DEMO-B1-001").json()
        assert final_payload["customer"] == "Demo Process Industries S.p.A."
        assert final_payload["order_value"] == 500000
        assert next(item for item in final_payload["extracted_fields"] if item["field_key"] == "penalty_cap")["operational_value"] is None

        # PM creates the financial follow-up and hands it to Administration.
        client.post("/login", data={"username": "pm_greco"}, follow_redirects=False)
        pm_payload = client.get("/api/projects/DEMO-B1-001").json()
        overdue = next(item for item in pm_payload["alerts"] if item["type"] == "OVERDUE_INVOICE")
        created = client.post(f"/api/alerts/{overdue['id']}/create-action")
        assert created.status_code == 200
        action_id = created.json()["action_id"]
        pm_after = client.get("/api/projects/DEMO-B1-001").json()
        action = next(item for item in pm_after["actions"] if item["id"] == action_id)
        assert action["owner"] == "Amministrazione"
        client.post(
            f"/api/actions/{action_id}/messages",
            data={"body": "Verifica lo stato dell'incasso della fattura INV-DEMO-001 e conferma l'esito."},
        )

        # Administration sees the assigned project, takes the task and replies internally.
        client.post("/login", data={"username": "admin_demo"}, follow_redirects=False)
        assert client.get("/project/DEMO-B1-001").status_code == 200
        assert client.post(f"/api/actions/{action_id}/status", data={"status": "IN_PROGRESS"}).status_code == 200
        reply = client.post(
            f"/api/actions/{action_id}/response",
            data={"body": "Verifica eseguita: EUR 200.000 restano aperti. Ho avviato il sollecito."},
        )
        assert reply.status_code == 200
        assert client.post(f"/api/actions/{action_id}/validate").status_code == 403

        # PM validates the response. Closing the task does not hide the still-valid financial alert.
        client.post("/login", data={"username": "pm_greco"}, follow_redirects=False)
        assert client.post(f"/api/actions/{action_id}/validate").status_code == 200
        completed = client.get("/api/projects/DEMO-B1-001").json()
        closed = next(item for item in completed["actions"] if item["id"] == action_id)
        assert closed["status"] == "CLOSED"
        assert any(item["id"] == overdue["id"] for item in completed["alerts"])
