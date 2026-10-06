from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import Alert, Project


def _create(client, code="CS4-TEST", pm="pm_sala", sales="sales_riva"):
    return client.post(
        "/projects",
        data={"code": code, "pm_username": pm, "sales_username": sales},
        follow_redirects=False,
    )


def test_director_can_create_minimal_project_and_is_redirected():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        response = _create(client, "CS4-DIRECTOR")
        assert response.status_code == 303
        assert response.headers["location"] == "/project/CS4-DIRECTOR"

        with SessionLocal() as db:
            project = db.query(Project).filter_by(code="CS4-DIRECTOR").one()
            assert project.customer == "__PENDING__"
            assert project.order_value == 0
            assert project.status == "ACQUISIZIONE_DATI"
            assert project.pm_owner == "P. Sala"
            assert project.sales_owner == "S. Riva"
            assert not project.invoices
            assert not project.budget_lines


def test_acquisition_project_hides_placeholders_and_has_unconnected_sources():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        assert _create(client, "CS4-HTML").status_code == 303
        response = client.get("/project/CS4-HTML")
        assert response.status_code == 200
        assert "__PENDING__" not in response.text
        assert "Acquisizione dati" in response.text
        assert "La commessa è stata creata. Ora collega o importa le fonti dati." in response.text
        assert response.text.count("Da acquisire") >= 3
        for source in ("Galileo", "Documenti", "Outlook"):
            assert source in response.text
        assert response.text.count("Non configurato") == 3


def test_acquisition_project_has_no_placeholder_derived_alert_or_exposure():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        assert _create(client, "CS4-NO-ALERT").status_code == 303
        detail = client.get("/api/projects/CS4-NO-ALERT")
        assert detail.status_code == 200
        payload = detail.json()
        assert payload["alerts"] == []
        assert payload["attention"] == 0
        assert payload["priority"]["label"] == "Acquisizione dati"
        assert all(value == 0 for key, value in payload["exposure"].items() if key not in {"ld_milestones"})
        with SessionLocal() as db:
            project = db.query(Project).filter_by(code="CS4-NO-ALERT").one()
            assert db.query(Alert).filter(Alert.project_id == project.id, Alert.status.in_(["OPEN", "ACKNOWLEDGED"])).count() == 0


def test_creation_validation_rejects_missing_and_duplicate_values():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        assert _create(client, "CS4-VALID").status_code == 303
        duplicate = _create(client, "CS4-VALID")
        assert duplicate.status_code == 400
        assert "Esiste già una commessa" in duplicate.text
        missing_code = _create(client, "")
        assert missing_code.status_code == 400
        assert "codice commessa è obbligatorio" in missing_code.text
        missing_pm = _create(client, "CS4-MISSING-PM", "", "sales_riva")
        assert missing_pm.status_code == 400
        assert "Project Manager valido" in missing_pm.text
        missing_sales = _create(client, "CS4-MISSING-SALES", "pm_sala", "")
        assert missing_sales.status_code == 400
        assert "Commerciale valido" in missing_sales.text


def test_only_director_can_access_or_submit_new_project():
    with TestClient(app) as client:
        client.post("/login", data={"username": "sales_riva"}, follow_redirects=False)
        assert client.get("/projects/new").status_code == 403
        assert _create(client, "CS4-DENIED").status_code == 403
        client.post("/login", data={"username": "pm_sala"}, follow_redirects=False)
        assert client.get("/projects/new").status_code == 403