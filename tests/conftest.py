import os
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
TEST_DATA_ROOT = (REPOSITORY_ROOT / "data" / "test").resolve()
TEST_DATABASE_PATH = (TEST_DATA_ROOT / f"brofind_test_{os.getpid()}.db").resolve()

try:
    TEST_DATABASE_PATH.relative_to(TEST_DATA_ROOT)
except ValueError as exc:
    raise RuntimeError("Pytest fail-closed: test database is outside data/test.") from exc

if TEST_DATABASE_PATH.suffix.lower() != ".db":
    raise RuntimeError("Pytest fail-closed: test database is not a SQLite .db file.")

os.environ["BROFIND_RUNTIME"] = "test"
os.environ["BROFIND_DATABASE_PATH"] = str(TEST_DATABASE_PATH)
os.environ.pop("DATABASE_URL", None)

TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)
TEST_DATABASE_PATH.unlink(missing_ok=True)


def pytest_sessionfinish(session, exitstatus):
    try:
        from app.db import engine

        engine.dispose()
    finally:
        TEST_DATABASE_PATH.unlink(missing_ok=True)

