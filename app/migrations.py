"""Preparazione dello schema all'avvio.

- runtime test: schema creato direttamente dai modelli (database usa e getta);
- runtime demo/development: migrazioni Alembic fino all'ultima revisione.
  Un database creato prima dell'introduzione di Alembic (<= v0.3.8.1) viene
  completato con le eventuali tabelle mancanti, come faceva il vecchio avvio,
  e marcato sulla revisione iniziale, che corrisponde allo schema v0.3.8.1.
"""

from alembic.config import Config
from sqlalchemy import inspect

from alembic import command

from .config import settings
from .db import Base, engine

BASELINE_REVISION = "0001_baseline_v0381"


def alembic_config() -> Config:
    return Config(str(settings.project_root / "alembic.ini"))


def prepare_schema() -> None:
    if settings.runtime == "test":
        Base.metadata.create_all(bind=engine)
        return
    tables = set(inspect(engine).get_table_names())
    config = alembic_config()
    if tables and "alembic_version" not in tables:
        Base.metadata.create_all(bind=engine)
        command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")
