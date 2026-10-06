import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
DEVELOPMENT_DATA_ROOT = DATA_ROOT / "development"
DEMO_DATA_ROOT = DATA_ROOT / "demo"
TEST_DATA_ROOT = DATA_ROOT / "test"
SUPPORTED_RUNTIME_MODES = {"development", "demo", "test"}


def _env_bool(environment: Mapping[str, str], name: str, default: bool) -> bool:
    raw = environment.get(name)
    if raw is None:
        return default
    return raw.strip().lower() == "true"


def _resolved_repo_path(raw_path: str) -> Path:
    candidate = Path(os.path.expandvars(raw_path)).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def _sqlite_url(database_path: Path) -> str:
    return f"sqlite:///{database_path.as_posix()}"


def _sqlite_path_from_url(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw_path = database_url[len(prefix):]
    if not raw_path or raw_path == ":memory:":
        return None
    return _resolved_repo_path(raw_path)


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory.resolve())
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class Settings:
    runtime: str
    database_url: str
    database_path: Path | None
    app_secret: str
    technical_document_findings_enabled: bool
    project_root: Path = PROJECT_ROOT
    data_root: Path = DATA_ROOT
    source_root: Path = PROJECT_ROOT / "data_sources"

    @property
    def demo_mode(self) -> bool:
        return self.runtime == "demo"

    @property
    def destructive_reset_enabled(self) -> bool:
        return self.runtime in {"development", "test"}

    @property
    def database_label(self) -> str:
        if self.database_path is not None:
            return self.database_path.name
        return "external-database"


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if environment is None else environment
    runtime = env.get("BROFIND_RUNTIME", "development").strip().lower()
    if runtime not in SUPPORTED_RUNTIME_MODES:
        allowed = ", ".join(sorted(SUPPORTED_RUNTIME_MODES))
        raise RuntimeError(f"BROFIND_RUNTIME non valido: {runtime!r}. Valori ammessi: {allowed}.")

    configured_path = env.get("BROFIND_DATABASE_PATH", "").strip()
    inherited_url = env.get("DATABASE_URL", "").strip()

    if runtime == "test":
        if not configured_path:
            raise RuntimeError(
                "Runtime test fail-closed: BROFIND_DATABASE_PATH deve indicare esplicitamente "
                "un file SQLite sotto data/test. DATABASE_URL e fallback non sono ammessi."
            )
        database_path = _resolved_repo_path(configured_path)
        if database_path.suffix.lower() != ".db" or not _is_within(database_path, TEST_DATA_ROOT):
            raise RuntimeError(
                "Runtime test rifiutato: il database deve essere un file .db sotto data/test."
            )
        database_url = _sqlite_url(database_path)
    elif runtime == "demo":
        database_path = _resolved_repo_path(
            configured_path or str(DEMO_DATA_ROOT / "brofind_demo.db")
        )
        if database_path.suffix.lower() != ".db" or not _is_within(database_path, DEMO_DATA_ROOT):
            raise RuntimeError(
                "Runtime demo rifiutato: il database deve essere un file .db sotto data/demo."
            )
        database_url = _sqlite_url(database_path)
    elif configured_path:
        database_path = _resolved_repo_path(configured_path)
        database_url = _sqlite_url(database_path)
    elif inherited_url:
        database_url = inherited_url
        database_path = _sqlite_path_from_url(database_url)
        if database_path is not None:
            database_url = _sqlite_url(database_path)
    else:
        database_path = (DEVELOPMENT_DATA_ROOT / "brofind_control_dev.db").resolve()
        database_url = _sqlite_url(database_path)

    return Settings(
        runtime=runtime,
        database_url=database_url,
        database_path=database_path,
        app_secret=env.get("APP_SECRET", "brofind-demo-secret"),
        source_root=_resolved_repo_path(env.get("BROFIND_SOURCE_ROOT", "data_sources")),
        technical_document_findings_enabled=_env_bool(
            env, "TECHNICAL_DOCUMENT_FINDINGS_ENABLED", True
        ),
    )


settings = load_settings()
