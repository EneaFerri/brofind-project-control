"""Applicazione FastAPI: avvio, migrazioni, file statici e registrazione dei router."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import SessionLocal
from .intelligence import analyze_all_projects
from .migrations import prepare_schema
from .routers import decisions, operations, pages, projects_api, sources
from .rules import recompute_alerts
from .seed import seed
from .template_builder import build_template
from .version import VERSION


def initialize_app():
    settings.data_root.mkdir(exist_ok=True)
    prepare_schema()
    with SessionLocal() as db:
        seed(db)
        analyze_all_projects(db)
        recompute_alerts(db)
    template_path = settings.project_root / "data" / "BROFIND_PROJECT_IMPORT.xlsx"
    if not template_path.exists():
        build_template(template_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_app()
    yield


app = FastAPI(title="Brofind Project Control", version=VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=settings.project_root / "static"), name="static")

for module in (pages, sources, operations, decisions, projects_api):
    app.include_router(module.router)
