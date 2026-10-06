from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import Project, ProjectSourceFile, ProjectSourceScan
from app.source_center import SourceCenterError, refresh_project_sources, scan_project_sources


@contextmanager
def configured_source_root(path):
    previous = settings.source_root
    object.__setattr__(settings, "source_root", path)
    try:
        yield
    finally:
        object.__setattr__(settings, "source_root", previous)


def _create_project(client, code="CS5-SOURCE"):
    response = client.post(
        "/projects",
        data={"code": code, "pm_username": "pm_sala", "sales_username": "sales_riva"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return code


def _refresh(code, root):
    with SessionLocal() as db:
        project = db.query(Project).filter_by(code=code).one()
        refresh_project_sources(db, project, root)
        db.commit()
        return project.status


def _source_path(root, code, folder, filename):
    path = root / code / folder
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


def test_source_center_handles_missing_project_folder_and_empty_sources(tmp_path):
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        code = _create_project(client, "CS5-EMPTY")
        assert _refresh(code, tmp_path) == "ACQUISIZIONE_DATI"
        with SessionLocal() as db:
            scans = {
                item.source_type: item
                for item in db.query(ProjectSourceScan).join(Project).filter(Project.code == code)
            }
            assert set(scans) == {"GALILEO", "DOCUMENT", "OUTLOOK"}
            assert all(item.status == "NOT_CONFIGURED" and item.file_count == 0 for item in scans.values())

        for folder in ("Galileo", "Documenti", "Outlook"):
            (tmp_path / code / folder).mkdir(parents=True, exist_ok=True)
        _refresh(code, tmp_path)
        with SessionLocal() as db:
            scans = db.query(ProjectSourceScan).join(Project).filter(Project.code == code).all()
            assert all(item.status == "NO_FILES" and item.file_count == 0 for item in scans)


def test_source_center_detects_supported_files_ignores_temporary_files_and_keeps_originals(tmp_path):
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        code = _create_project(client, "CS5-FILES")
        galileo = _source_path(tmp_path, code, "Galileo", "control.xlsx")
        document = _source_path(tmp_path, code, "Documenti", "contratto.pdf")
        message = _source_path(tmp_path, code, "Outlook", "cliente.msg")
        email = _source_path(tmp_path, code, "Outlook", "cliente.eml")
        galileo.write_bytes(b"galileo-original")
        document.write_bytes(b"pdf-original")
        message.write_bytes(b"msg-original")
        email.write_bytes(b"eml-original")
        _source_path(tmp_path, code, "Galileo", "~$control.xlsx").write_bytes(b"lock")
        _source_path(tmp_path, code, "Documenti", ".hidden.pdf").write_bytes(b"hidden")
        _source_path(tmp_path, code, "Outlook", "draft.tmp").write_bytes(b"temp")
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in (galileo, document, message, email)}

        assert _refresh(code, tmp_path) == "ACQUISIZIONE_DATI"
        after = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in (galileo, document, message, email)}
        assert after == before

        with SessionLocal() as db:
            files = (
                db.query(ProjectSourceFile)
                .join(Project)
                .filter(Project.code == code, ProjectSourceFile.is_present.is_(True))
                .all()
            )
            assert {item.file_name for item in files} == {"control.xlsx", "contratto.pdf", "cliente.msg", "cliente.eml"}
            scans = {
                item.source_type: item
                for item in db.query(ProjectSourceScan).join(Project).filter(Project.code == code)
            }
            assert scans["GALILEO"].file_count == 1
            assert scans["DOCUMENT"].file_count == 1
            assert scans["OUTLOOK"].file_count == 2
            assert all(item.change_status == "NEW" for item in files)


def test_source_center_uses_hash_for_change_and_preserves_missing_history(tmp_path):
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        code = _create_project(client, "CS5-CHANGES")
        workbook = _source_path(tmp_path, code, "Galileo", "control.xlsx")
        workbook.write_bytes(b"version-one")
        _refresh(code, tmp_path)

        future = datetime.now().timestamp() + 120
        os.utime(workbook, (future, future))
        _refresh(code, tmp_path)
        with SessionLocal() as db:
            record = db.query(ProjectSourceFile).join(Project).filter(Project.code == code).one()
            assert record.change_status == "UNCHANGED"
            first_id = record.id
            assert record.is_present is True

        workbook.write_bytes(b"version-two")
        _refresh(code, tmp_path)
        with SessionLocal() as db:
            record = db.query(ProjectSourceFile).join(Project).filter(Project.code == code).one()
            assert record.id == first_id
            assert record.change_status == "MODIFIED"
            assert record.is_present is True

        workbook.unlink()
        _refresh(code, tmp_path)
        with SessionLocal() as db:
            record = db.query(ProjectSourceFile).join(Project).filter(Project.code == code).one()
            assert record.id == first_id
            assert record.change_status == "MISSING"
            assert record.is_present is False
            scan = (
                db.query(ProjectSourceScan)
                .join(Project)
                .filter(Project.code == code, ProjectSourceScan.source_type == "GALILEO")
                .one()
            )
            assert scan.file_count == 0

        workbook.write_bytes(b"version-two")
        _refresh(code, tmp_path)
        with SessionLocal() as db:
            record = db.query(ProjectSourceFile).join(Project).filter(Project.code == code).one()
            assert record.id == first_id
            assert record.is_present is True
            assert record.change_status == "UNCHANGED"


def test_source_center_is_confined_to_configured_root(tmp_path):
    outside = tmp_path.parent / "outside-source"
    outside.mkdir(exist_ok=True)
    sentinel = outside / "secret.xlsx"
    sentinel.write_bytes(b"outside")
    with pytest.raises(SourceCenterError):
        scan_project_sources("../outside-source", tmp_path)
    assert sentinel.read_bytes() == b"outside"


def test_source_center_ui_shows_counts_and_does_not_leave_acquisition_state(tmp_path):
    with configured_source_root(tmp_path), TestClient(app) as client:
        client.post("/api/demo/reset")
        code = _create_project(client, "CS5-UI")
        _source_path(tmp_path, code, "Galileo", "control.xlsx").write_bytes(b"xlsx")
        _source_path(tmp_path, code, "Documenti", "spec.pdf").write_bytes(b"pdf")
        _source_path(tmp_path, code, "Outlook", "mail.eml").write_bytes(b"eml")
        refreshed = client.post(f"/project/{code}/sources/refresh", follow_redirects=False)
        assert refreshed.status_code == 303
        detail = client.get(refreshed.headers["location"])
        assert detail.status_code == 200
        assert "Fonti aggiornate · 1 file Galileo · 1 documento · 1 email" in detail.text
        assert "Galileo" in detail.text and "Documenti" in detail.text and "Outlook" in detail.text
        assert "control.xlsx" in detail.text and "spec.pdf" in detail.text and "mail.eml" in detail.text
        assert "ACQUISIZIONE_DATI" not in detail.text
        assert "Acquisizione dati" in detail.text
        with SessionLocal() as db:
            assert db.query(Project).filter_by(code=code).one().status == "ACQUISIZIONE_DATI"
