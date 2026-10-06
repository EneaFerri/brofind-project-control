from __future__ import annotations

import hashlib
import re
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import Invoice, Project, ProjectControlSnapshot, ProjectSourceImport
from app.rules import project_health

FIXTURE = Path(__file__).resolve().parents[1] / "demo" / "b1" / "assets" / "DEMO-B1-001_control.xlsx"


@contextmanager
def configured_source_root(path):
    previous = settings.source_root
    object.__setattr__(settings, "source_root", path)
    try:
        yield
    finally:
        object.__setattr__(settings, "source_root", previous)


def create_project(client):
    response = client.post(
        "/projects",
        data={"code": "DEMO-B1-001", "pm_username": "pm_greco", "sales_username": "sales_riva"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def galileo_file(root, name="DEMO-B1-001_control.xlsx"):
    path = root / "DEMO-B1-001" / "Galileo" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(FIXTURE.read_bytes())
    return path


def refresh(client):
    assert client.post("/project/DEMO-B1-001/sources/refresh", follow_redirects=False).status_code == 303


def import_galileo(client, data=None):
    response = client.post("/project/DEMO-B1-001/sources/galileo/import", data=data or {}, follow_redirects=False)
    assert response.status_code == 303
    return response


def counts():
    with SessionLocal() as db:
        project = db.query(Project).filter_by(code="DEMO-B1-001").one()
        return (
            db.query(ProjectControlSnapshot).filter_by(project_id=project.id).count(),
            db.query(Invoice).filter_by(project_id=project.id).count(),
            db.query(ProjectSourceImport).filter_by(project_id=project.id).count(),
        )


def test_galileo_import_unlocks_only_economic_domains_and_preserves_placeholders(tmp_path):
    with configured_source_root(tmp_path), TestClient(app) as client:
        client.post("/api/demo/reset")
        create_project(client)
        source = galileo_file(tmp_path)
        before = (source.read_bytes(), source.stat().st_mtime_ns, hashlib.sha256(source.read_bytes()).hexdigest())
        refresh(client)
        assert "File disponibile" in client.get("/project/DEMO-B1-001").text
        assert "Importa dati Galileo" in client.get("/project/DEMO-B1-001").text
        imported = import_galileo(client)
        detail = client.get(imported.headers["location"])
        assert "Dati Galileo importati correttamente" in detail.text
        assert "__PENDING__" not in detail.text
        economics = client.get("/project/DEMO-B1-001/economics").text
        assert re.search(r"Valore contratto</span>\s*<strong>Da acquisire", economics)
        assert "Valore netto</span><strong>€ 0" not in detail.text
        assert (
            source.read_bytes(),
            source.stat().st_mtime_ns,
            hashlib.sha256(source.read_bytes()).hexdigest(),
        ) == before
        with SessionLocal() as db:
            project = db.query(Project).filter_by(code="DEMO-B1-001").one()
            assert project.status == "ACQUISIZIONE_DATI"
            assert project_health(project) == {
                "FINANCE": "RED",
                "BUDGET": "RED",
                "TECHNICAL": "ND",
                "SCHEDULE": "ND",
                "CONTRACT": "ND",
            }
            assert (
                db.query(ProjectSourceImport)
                .filter_by(project_id=project.id, status="SUCCESS", processor="B1_CONTROL_ADAPTER")
                .count()
                == 1
            )
        payload = client.get("/api/projects/DEMO-B1-001").json()
        assert payload["customer"] == "Da acquisire" and payload["has_economic_data"] is True
        assert payload["control"]["operational_budget"] == 360000 and payload["finance"]["overdue"] == 200000


def test_galileo_double_import_is_idempotent_and_ambiguous_files_are_not_selectable(tmp_path):
    with configured_source_root(tmp_path), TestClient(app) as client:
        client.post("/api/demo/reset")
        create_project(client)
        galileo_file(tmp_path)
        refresh(client)
        import_galileo(client)
        before = counts()
        import_galileo(client)
        assert counts() == (1, 1, before[2] + 1)
        galileo_file(tmp_path, "second.xlsx")
        refresh(client)
        page = client.get("/project/DEMO-B1-001").text
        assert "Più file Galileo disponibili" in page and "Importa dati Galileo" not in page
        import_galileo(client)
        assert counts() == (1, 1, before[2] + 1)


def test_galileo_invalid_workbook_rolls_back_and_changed_file_requires_refresh(tmp_path):
    with configured_source_root(tmp_path), TestClient(app) as client:
        client.post("/api/demo/reset")
        create_project(client)
        source = galileo_file(tmp_path)
        refresh(client)
        source.write_bytes(b"changed-after-scan")
        assert "galileo_import_error=1" in import_galileo(client).headers["location"]
        assert counts() == (0, 0, 0)
        refresh(client)
        assert (
            "galileo_import_error=1"
            in import_galileo(client, {"path": str(tmp_path.parent / "outside.xlsx")}).headers["location"]
        )
        assert counts() == (0, 0, 1)
        with SessionLocal() as db:
            project = db.query(Project).filter_by(code="DEMO-B1-001").one()
            assert project.status == "ACQUISIZIONE_DATI"
            record = db.query(ProjectSourceImport).filter_by(project_id=project.id).one()
            assert record.status == "ERROR" and "B1:" in record.error_message
