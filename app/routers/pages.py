"""Pagine HTML: portfolio, commessa, creazione commessa, login demo, import e health."""

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..analytics import portfolio_exposure
from ..b1_control_adapter import import_b1_control_workbook, is_b1_workbook_candidate
from ..config import settings
from ..db import get_db
from ..importer import import_workbook
from ..intelligence import analyze_all_projects
from ..models import Project, User
from ..rules import recompute_alerts
from ..security import current_user, visible_projects_query
from ..serializers import project_card, project_detail
from ..source_center import source_update_message
from ..template_builder import build_template
from ..web import VERSION, templates

router = APIRouter()

TEMPLATE_PATH = settings.project_root / "data" / "BROFIND_PROJECT_IMPORT.xlsx"


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    project_rows = visible_projects_query(db, user).all()
    priority_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "NO_DATA": 3, "OK": 4}
    cards = sorted(
        [project_card(p, date.today()) for p in project_rows],
        key=lambda x: (priority_rank.get(x["priority"]["key"], 9), -x["attention"], x["code"]),
    )
    users = db.query(User).all()
    total_value = sum(x["order_value"] for x in cards)
    exposure = portfolio_exposure(project_rows, date.today())
    attention = sum(x["open_alerts"] for x in cards)
    ai_findings = sum(x["ai_findings_new"] for x in cards)
    portfolio_status = {
        "critical": sum(1 for x in cards if x["priority"]["key"] == "CRITICAL"),
        "intervene": sum(1 for x in cards if x["priority"]["key"] == "HIGH"),
        "monitor": sum(1 for x in cards if x["priority"]["key"] == "MEDIUM"),
        "regular": sum(1 for x in cards if x["priority"]["key"] == "OK"),
        "no_data": sum(1 for x in cards if x["priority"]["key"] == "NO_DATA"),
    }
    filters = {
        "sales": sorted({x["sales_owner"] for x in cards}),
        "pms": sorted({x["pm_owner"] for x in cards}),
        "statuses": sorted({x["status"] for x in cards}),
    }
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "users": users,
            "projects": cards,
            "total_value": total_value,
            "exposure": exposure,
            "attention": attention,
            "ai_findings": ai_findings,
            "portfolio_status": portfolio_status,
            "filters": filters,
            "destructive_reset_enabled": settings.destructive_reset_enabled,
            "version": VERSION,
        },
    )


def _new_project_form(
    request: Request, user: User, db: Session, values=None, error: str | None = None, status_code: int = 200
):
    return templates.TemplateResponse(
        request=request,
        name="project_new.html",
        context={
            "user": user,
            "pm_users": db.query(User).filter(User.role == "PM").order_by(User.display_name).all(),
            "sales_users": db.query(User).filter(User.role == "SALES").order_by(User.display_name).all(),
            "values": values or {"code": "", "pm_username": "", "sales_username": ""},
            "error": error,
            "version": VERSION,
        },
        status_code=status_code,
    )


@router.get("/projects/new", response_class=HTMLResponse)
def new_project_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if user.role != "DIRECTOR":
        raise HTTPException(403, "Solo la Direzione può creare una nuova commessa.")
    return _new_project_form(request, user, db)


@router.post("/projects")
def create_project(
    request: Request,
    code: str = Form(""),
    pm_username: str = Form(""),
    sales_username: str = Form(""),
    db: Session = Depends(get_db),
):
    user = current_user(request, db)
    if user.role != "DIRECTOR":
        raise HTTPException(403, "Solo la Direzione può creare una nuova commessa.")

    values = {"code": code.strip(), "pm_username": pm_username, "sales_username": sales_username}
    if not values["code"]:
        return _new_project_form(request, user, db, values, "Il codice commessa è obbligatorio.", 400)
    if db.query(Project).filter(Project.code == values["code"]).first():
        return _new_project_form(request, user, db, values, "Esiste già una commessa con questo codice.", 400)

    pm = db.query(User).filter(User.username == pm_username, User.role == "PM").first()
    if not pm:
        return _new_project_form(request, user, db, values, "Seleziona un Project Manager valido.", 400)
    sales = db.query(User).filter(User.username == sales_username, User.role == "SALES").first()
    if not sales:
        return _new_project_form(request, user, db, values, "Seleziona un Commerciale valido.", 400)

    project = Project(
        code=values["code"],
        customer="__PENDING__",
        order_value=0,
        pm_owner=pm.owner_key,
        sales_owner=sales.owner_key,
        status="ACQUISIZIONE_DATI",
    )
    db.add(project)
    db.commit()
    return RedirectResponse(url=f"/project/{project.code}", status_code=303)


@router.get("/project/{code}", response_class=HTMLResponse)
def project_page(code: str, request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Project not found or not visible")
    detail = project_detail(p, date.today())
    return templates.TemplateResponse(
        request=request,
        name="project.html",
        context={
            "user": user,
            "project": detail,
            "sources_message": (
                source_update_message(detail["sources"])
                if request.query_params.get("sources_updated")
                else "Dati Galileo importati correttamente"
                if request.query_params.get("galileo_imported")
                else None
            ),
            "users": db.query(User).all(),
            "version": VERSION,
        },
    )


@router.post("/login")
def login(username: str = Form(...)):
    r = RedirectResponse(url="/", status_code=303)
    r.set_cookie("demo_user", username, httponly=True, samesite="lax")
    return r


@router.post("/import", response_class=HTMLResponse)
async def excel_import(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if user.role != "DIRECTOR":
        raise HTTPException(403, "Only Director can import in demo")
    content = await file.read()
    context = {"users": db.query(User).all(), "user": user, "version": VERSION}
    try:
        stats = (
            import_b1_control_workbook(content, db)
            if is_b1_workbook_candidate(content)
            else import_workbook(content, db)
        )
        analyze_all_projects(db)
        recompute_alerts(db)
    except Exception as e:
        return templates.TemplateResponse(
            request=request, name="import_result.html", context={"ok": False, "message": str(e), **context}
        )
    return templates.TemplateResponse(
        request=request,
        name="import_result.html",
        context={"ok": True, "message": f"Import completato: {stats}", **context},
    )


@router.get("/download/template")
def download_template():
    if not TEMPLATE_PATH.exists():
        build_template(TEMPLATE_PATH)
    return FileResponse(TEMPLATE_PATH, filename="BROFIND_PROJECT_IMPORT.xlsx")


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "runtime": settings.runtime,
        "database": settings.database_label,
    }
