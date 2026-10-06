"""Pagine HTML: Portfolio, superfici di commessa V1, creazione commessa, login demo, import e health."""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from .. import cockpit_views as views
from ..b1_control_adapter import import_b1_control_workbook, is_b1_workbook_candidate
from ..config import settings
from ..db import get_db
from ..importer import import_workbook
from ..intelligence import analyze_all_projects
from ..models import Project, User
from ..rules import recompute_alerts
from ..security import current_user, visible_projects_query
from ..serializers import project_detail
from ..source_center import source_update_message
from ..template_builder import build_template
from ..web import DEPARTMENTS, VERSION, can_answer_action, can_validate_action, templates

router = APIRouter()

TEMPLATE_PATH = settings.project_root / "data" / "BROFIND_PROJECT_IMPORT.xlsx"


def _base_context(request: Request, db: Session, user: User, **extra) -> dict:
    return {
        "request": request,
        "user": user,
        "users": db.query(User).order_by(User.display_name).all(),
        "destructive_reset_enabled": settings.destructive_reset_enabled,
        "version": VERSION,
        **extra,
    }


@router.get("/", response_class=HTMLResponse)
def portfolio_page(request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    projects = visible_projects_query(db, user).all()
    pf = views.portfolio(projects)
    pms = sorted({r["pm"] for r in pf["rows"] if r["pm"] != "N/D"})
    sales = sorted({r["sales"] for r in pf["rows"] if r["sales"] != "N/D"})
    return templates.TemplateResponse(
        request=request,
        name="portfolio.html",
        context=_base_context(request, db, user, pf=pf, pms=pms, sales=sales, active_global="portfolio"),
    )


@router.get("/portfolio.csv")
def portfolio_export(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    pf = views.portfolio(visible_projects_query(db, user).all())
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";")
    writer.writerow(["Commessa", "Cliente", "Fase", *[label for _, label in pf["domains"]], "Principale esposizione"])
    for r in pf["rows"]:
        writer.writerow(
            [
                r["code"],
                r["customer"],
                r["phase_label"],
                *[d["state_label"] for d in r["domains"]],
                r["exposure"]["title"],
            ]
        )
    return Response(
        content="﻿" + out.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="portfolio_commesse.csv"'},
    )


def _new_project_form(
    request: Request, user: User, db: Session, values=None, error: str | None = None, status_code: int = 200
):
    return templates.TemplateResponse(
        request=request,
        name="project_new.html",
        context=_base_context(
            request,
            db,
            user,
            pm_users=db.query(User).filter(User.role == "PM").order_by(User.display_name).all(),
            sales_users=db.query(User).filter(User.role == "SALES").order_by(User.display_name).all(),
            values=values or {"code": "", "pm_username": "", "sales_username": ""},
            error=error,
            active_global="new",
        ),
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


# ------------------------------------------------------------ superfici commessa

SURFACES = {
    "overview": "overview.html",
    "master": "master.html",
    "technical": "technical.html",
    "procurement": "procurement.html",
    "documents": "documents.html",
    "economics": "economics.html",
    "billing": "billing.html",
    "criticita": "criticita.html",
    "attivita": "attivita.html",
    "conversazioni": "conversazioni.html",
    "storico": "storico.html",
}


def _surface_data(surface: str, p: Project, detail: dict, user: User, db: Session) -> dict:
    today = date.today()
    control = detail.get("control")
    if surface == "overview":
        return {"ov": views.overview(p, today)}
    if surface == "master":
        return {"ms": views.master(p, today)}
    if surface == "technical":
        return {"tc": views.technical(p, today)}
    if surface == "procurement":
        return {"pr": views.procurement(p, control)}
    if surface == "documents":
        return {"dc": views.documents(p, today)}
    if surface == "economics":
        return {"ec": views.economics(p, control, today)}
    if surface == "billing":
        return {"bp": views.billing(p, control, today)}
    if surface == "criticita":
        return {"cr": views.criticita(p)}
    if surface in ("attivita", "conversazioni"):
        by_id = {a.id: a for a in p.actions}
        actions = []
        for a in sorted(
            detail["actions"], key=lambda x: (x["status"] in ("CLOSED", "RESOLVED"), x["due_date"] or date.max)
        ):
            model = by_id[a["id"]]
            actions.append(
                {
                    **a,
                    "open": a["status"] not in ("CLOSED", "RESOLVED"),
                    "can_answer": can_answer_action(user, model),
                    "can_validate": can_validate_action(user, model),
                }
            )
        owners = sorted({u.owner_key for u in db.query(User).all() if u.owner_key} | DEPARTMENTS)
        return {"actions": actions, "owners": owners}
    if surface == "storico":
        return {"events": views.storico(p, today)}
    return {}


def _project_page(code: str, surface: str, request: Request, db: Session):
    recompute_alerts(db)
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Project not found or not visible")
    detail = project_detail(p, date.today())
    sources_message = (
        source_update_message(detail["sources"])
        if request.query_params.get("sources_updated")
        else "Dati Galileo importati correttamente"
        if request.query_params.get("galileo_imported")
        else None
    )
    context = _base_context(
        request,
        db,
        user,
        project=detail,
        h=views.project_header(p),
        nav=views.project_nav(p, surface),
        sources_message=sources_message,
        current_path=request.url.path,
        **_surface_data(surface, p, detail, user, db),
    )
    return templates.TemplateResponse(request=request, name=SURFACES[surface], context=context)


@router.get("/project/{code}", response_class=HTMLResponse)
def project_overview(code: str, request: Request, db: Session = Depends(get_db)):
    return _project_page(code, "overview", request, db)


@router.get("/project/{code}/{surface}", response_class=HTMLResponse)
def project_surface(code: str, surface: str, request: Request, db: Session = Depends(get_db)):
    if surface not in SURFACES or surface == "overview":
        raise HTTPException(404, "Pagina non trovata")
    return _project_page(code, surface, request, db)


# ----------------------------------------------------------------------- varie


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
    try:
        stats = (
            import_b1_control_workbook(content, db)
            if is_b1_workbook_candidate(content)
            else import_workbook(content, db)
        )
        analyze_all_projects(db)
        recompute_alerts(db)
    except Exception as e:
        context = _base_context(request, db, user, ok=False, message=str(e))
        return templates.TemplateResponse(request=request, name="import_result.html", context=context)
    context = _base_context(request, db, user, ok=True, message=f"Import completato: {stats}")
    return templates.TemplateResponse(request=request, name="import_result.html", context=context)


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
