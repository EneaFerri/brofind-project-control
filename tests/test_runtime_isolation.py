from pathlib import Path
import importlib

import pytest
from fastapi.testclient import TestClient

from app.config import (
    DEMO_DATA_ROOT,
    DEVELOPMENT_DATA_ROOT,
    TEST_DATA_ROOT,
    load_settings,
    settings,
)
from app.db import engine
from app.main import app


def test_pytest_engine_is_fail_closed_under_data_test():
    assert settings.runtime == "test"
    assert settings.database_path is not None
    assert settings.database_path.suffix.lower() == ".db"
    settings.database_path.resolve().relative_to(TEST_DATA_ROOT.resolve())
    assert engine.url.get_backend_name() == "sqlite"
    assert Path(engine.url.database).resolve() == settings.database_path.resolve()


def test_test_runtime_rejects_missing_explicit_path():
    with pytest.raises(RuntimeError, match="fail-closed"):
        load_settings(
            {
                "BROFIND_RUNTIME": "test",
                "DATABASE_URL": "sqlite:///./data/demo/should-never-be-used.db",
            }
        )


@pytest.mark.parametrize(
    "forbidden_path",
    [
        DEMO_DATA_ROOT / "brofind_demo.db",
        DEVELOPMENT_DATA_ROOT / "brofind_control_dev.db",
        DEVELOPMENT_DATA_ROOT.parent / "brofind_control_v038.db",
    ],
)
def test_test_runtime_rejects_non_test_database(forbidden_path):
    with pytest.raises(RuntimeError, match="data/test"):
        load_settings(
            {
                "BROFIND_RUNTIME": "test",
                "BROFIND_DATABASE_PATH": str(forbidden_path),
            }
        )


def test_database_fallback_is_independent_from_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved = load_settings({})
    assert resolved.runtime == "development"
    assert resolved.database_path == (
        DEVELOPMENT_DATA_ROOT / "brofind_control_dev.db"
    ).resolve()


def test_demo_database_is_confined_to_demo_directory():
    resolved = load_settings({"BROFIND_RUNTIME": "demo"})
    assert resolved.database_path == (DEMO_DATA_ROOT / "brofind_demo.db").resolve()
    assert resolved.database_url.startswith("sqlite:///")

    with pytest.raises(RuntimeError, match="data/demo"):
        load_settings(
            {
                "BROFIND_RUNTIME": "demo",
                "BROFIND_DATABASE_PATH": str(TEST_DATA_ROOT / "not-a-demo.db"),
            }
        )


def test_demo_runtime_hides_and_blocks_destructive_reset(monkeypatch):
    main_module = importlib.import_module("app.main")
    demo_settings = load_settings({"BROFIND_RUNTIME": "demo"})
    monkeypatch.setattr(main_module, "settings", demo_settings)

    with TestClient(app) as client:
        dashboard = client.get("/")
        assert dashboard.status_code == 200
        assert 'showModal()">Ripristina demo</button>' not in dashboard.text

        reset = client.post("/api/demo/reset", follow_redirects=False)
        assert reset.status_code == 403
        assert "disabilitato" in reset.json()["detail"]
