from datetime import date, datetime, timedelta
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal, get_db
from .models import User, Project, Alert, Action, ActionMessage, AgentFinding, Communication, ProjectControlLine, CockpitDecision, ProjectRequirement, ProjectSourceContent, ProjectSourceImport, ProjectExtractedField
from .seed import seed
from .rules import recompute_alerts
from .security import current_user, visible_projects_query
from .serializers import project_card, project_detail
from .analytics import portfolio_exposure, suggested_action
from .importer import import_workbook
from .b1_control_adapter import B1ImportError, import_b1_control_workbook, is_b1_workbook_candidate
from .template_builder import build_template
from .intelligence import analyze_all_projects, analyze_project
from .workflow import apply_finding
from .confidence import confidence_summary
from .config import settings
from .source_readers import SourceReadError, read_source_content
from .source_center import SourceCenterError, refresh_project_sources, resolve_galileo_import_candidate, resolve_source_file_content, source_update_message
from .ai_analysis import analyze_project_sources, apply_reviewed_field

BASE = settings.project_root
VERSION = "0.3.8.1"

DEPARTMENTS = {"Responsabile Tecnico", "Acquisti", "Amministrazione", "Commerciale", "Direzione"}


def _is_action_owner(user: User, action: Action) -> bool:
    return bool(user and user.owner_key and action.owner == user.owner_key)


def _is_action_requester(user: User, action: Action) -> bool:
    return bool(user and action.requester and action.requester == user.display_name)


def _can_answer_action(user: User, action: Action) -> bool:
    return user.role == "DIRECTOR" or _is_action_owner(user, action)


def _can_validate_action(user: User, action: Action) -> bool:
    return user.role == "DIRECTOR" or _is_action_requester(user, action)


def initialize_app():
    settings.data_root.mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
        analyze_all_projects(db)
        recompute_alerts(db)
    template_path = BASE / "data" / "BROFIND_PROJECT_IMPORT.xlsx"
    if not template_path.exists():
        build_template(template_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_app()
    yield


app = FastAPI(title="Brofind Project Control", version=VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    project_rows = visible_projects_query(db, user).all()
    priority_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "NO_DATA": 3, "OK": 4}
    cards = sorted([project_card(p, date.today()) for p in project_rows], key=lambda x: (priority_rank.get(x["priority"]["key"], 9), -x["attention"], x["code"]))
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


def _new_project_form(request: Request, user: User, db: Session, values=None, error: str | None = None, status_code: int = 200):
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


@app.get("/projects/new", response_class=HTMLResponse)
def new_project_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if user.role != "DIRECTOR":
        raise HTTPException(403, "Solo la Direzione può creare una nuova commessa.")
    return _new_project_form(request, user, db)


@app.post("/projects")
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

@app.get("/project/{code}", response_class=HTMLResponse)
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
                source_update_message(detail["sources"]) if request.query_params.get("sources_updated")
                else "Dati Galileo importati correttamente" if request.query_params.get("galileo_imported")
                else None
            ),
            "users": db.query(User).all(),
            "version": VERSION,
        },
    )


@app.post("/project/{code}/sources/refresh")
def refresh_sources(code: str, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    project = visible_projects_query(db, user).filter(Project.code == code).first()
    if not project:
        raise HTTPException(404, "Project not found or not visible")
    try:
        refresh_project_sources(db, project, settings.source_root)
        db.commit()
    except SourceCenterError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    anchor = "#sources-drawer" if project.control_snapshots else "#sources"
    return RedirectResponse(url=f"/project/{project.code}?sources_updated=1{anchor}", status_code=303)


@app.post("/project/{code}/sources/galileo/import")
def import_galileo_source(code: str, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    project = visible_projects_query(db, user).filter(Project.code == code).first()
    if not project:
        raise HTTPException(404, "Project not found or not visible")

    candidate = None
    try:
        candidate = resolve_galileo_import_candidate(project, settings.source_root)
        import_b1_control_workbook(
            candidate.content,
            db,
            expected_project_code=project.code,
            commit=False,
        )
        db.add(ProjectSourceImport(
            project_id=project.id,
            source_type="GALILEO",
            source_file_id=candidate.source_file.id,
            source_hash=candidate.source_file.sha256,
            processor="B1_CONTROL_ADAPTER",
            status="SUCCESS",
        ))
        recompute_alerts(db)
    except Exception as exc:
        db.rollback()
        message = str(exc) if isinstance(exc, (SourceCenterError, B1ImportError)) else "Errore durante l'import Galileo."
        if candidate is not None:
            db.add(ProjectSourceImport(
                project_id=project.id,
                source_type="GALILEO",
                source_file_id=candidate.source_file.id,
                source_hash=candidate.source_file.sha256,
                processor="B1_CONTROL_ADAPTER",
                status="ERROR",
                error_message=message,
            ))
            db.commit()
        return RedirectResponse(url=f"/project/{project.code}?galileo_import_error=1#sources", status_code=303)
    return RedirectResponse(url=f"/project/{project.code}?galileo_imported=1#sources-drawer", status_code=303)

def _read_project_source_type(project: Project, source_type: str, db: Session) -> tuple[int, int]:
    processed = errors = 0
    files = sorted((item for item in project.source_files if item.is_present and item.source_type == source_type), key=lambda item: item.file_name.lower())
    for source_file in files:
        try:
            if db.query(ProjectSourceContent).filter_by(project_id=project.id, source_file_id=source_file.id, source_hash=source_file.sha256).first():
                continue
            parsed = read_source_content(resolve_source_file_content(project, settings.source_root, source_file), source_file.file_name, source_type)
            db.add(ProjectSourceContent(project_id=project.id, source_file_id=source_file.id, source_hash=source_file.sha256, content_kind=parsed.content_kind, content_type=parsed.content_type, extracted_text=parsed.extracted_text, metadata_json=parsed.metadata_json))
            db.add(ProjectSourceImport(project_id=project.id, source_type=source_type, source_file_id=source_file.id, source_hash=source_file.sha256, processor="SOURCE_CONTENT_READER", status="SUCCESS"))
            processed += 1
        except Exception as exc:
            message = str(exc) if isinstance(exc, (SourceCenterError, SourceReadError)) else "Errore durante la lettura della fonte."
            db.add(ProjectSourceImport(project_id=project.id, source_type=source_type, source_file_id=source_file.id, source_hash=source_file.sha256, processor="SOURCE_CONTENT_READER", status="ERROR", error_message=message))
            errors += 1
    db.commit()
    return processed, errors


@app.post("/project/{code}/sources/{source_type}/read")
def read_source_type(code: str, source_type: str, request: Request, db: Session = Depends(get_db)):
    if source_type not in {"DOCUMENT", "OUTLOOK"}:
        raise HTTPException(404, "Source not supported")
    user = current_user(request, db)
    project = visible_projects_query(db, user).filter(Project.code == code).first()
    if not project:
        raise HTTPException(404, "Project not found or not visible")
    _read_project_source_type(project, source_type, db)
    anchor = "#sources-drawer" if project.control_snapshots else "#sources"
    return RedirectResponse(url=f"/project/{project.code}?source_read={source_type}{anchor}", status_code=303)

@app.post("/api/projects/{code}/extracted-fields")
def create_extracted_field(code: str, request: Request, source_content_id: int = Form(...), field_key: str = Form(...), extracted_value: str = Form(...), confidence: float = Form(0.0), source_ref: str = Form(""), db: Session = Depends(get_db)):
    user = current_user(request, db)
    project = visible_projects_query(db, user).filter(Project.code == code).first()
    if not project:
        raise HTTPException(404, "Project not found or not visible")
    content = db.query(ProjectSourceContent).filter_by(id=source_content_id, project_id=project.id).one_or_none()
    if content is None:
        raise HTTPException(404, "Source content not found")
    field_key = field_key.strip()
    extracted_value = extracted_value.strip()
    if not field_key or not extracted_value or confidence < 0 or confidence > 1:
        raise HTTPException(400, "Invalid extracted field")
    field = db.query(ProjectExtractedField).filter_by(project_id=project.id, source_content_id=content.id, field_key=field_key).one_or_none()
    if field is None:
        field = ProjectExtractedField(project_id=project.id, source_content_id=content.id, field_key=field_key, extracted_value=extracted_value, confidence=confidence, source_ref=source_ref.strip() or f"source_content:{content.id}")
        db.add(field)
        db.commit()
        db.refresh(field)
        created = True
    else:
        created = False
    return {"ok": True, "id": field.id, "created": created, "review_status": field.review_status, "operational_value": field.operational_value, "provenance": "EXTRACTED" if field.operational_value is None else "OPERATIONAL"}


@app.post("/api/extracted-fields/{field_id}/review")
def review_extracted_field(field_id: int, request: Request, status: str = Form(...), corrected_value: str = Form(""), return_to: str = Form(""), db: Session = Depends(get_db)):
    user = current_user(request, db)
    field = db.query(ProjectExtractedField).filter_by(id=field_id).one_or_none()
    if field is None:
        raise HTTPException(404, "Extracted field not found")
    project = visible_projects_query(db, user).filter(Project.id == field.project_id).first()
    if project is None:
        raise HTTPException(403, "Not authorized")
    status = status.upper()
    if status not in {"CONFIRMED", "CORRECTED", "TO_VERIFY"}:
        raise HTTPException(400, "Invalid review status")
    corrected_value = corrected_value.strip()
    if status == "CORRECTED" and not corrected_value:
        raise HTTPException(400, "Corrected value is required")
    field.review_status = status
    field.corrected_value = corrected_value or None
    field.operational_value = field.extracted_value if status == "CONFIRMED" else corrected_value if status == "CORRECTED" else None
    apply_reviewed_field(field, db, user.display_name)
    db.commit()
    recompute_alerts(db)
    if return_to.startswith(f"/project/{project.code}"):
        return RedirectResponse(url=return_to, status_code=303)
    return {"ok": True, "id": field.id, "review_status": field.review_status, "operational_value": field.operational_value, "provenance": "OPERATIONAL" if field.operational_value is not None else "REVIEWED"}


@app.post("/project/{code}/ai/analyze")
def analyze_project_ai(code: str, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    project = visible_projects_query(db, user).filter(Project.code == code).first()
    if project is None:
        raise HTTPException(404, "Project not found or not visible")
    analyze_project_sources(project, db)
    anchor = "#ai-review" if project.control_snapshots else "#ai-analysis"
    return RedirectResponse(url=f"/project/{project.code}?ai_analyzed=1{anchor}", status_code=303)
@app.post("/login")
def login(username: str = Form(...)):
    r = RedirectResponse(url="/", status_code=303)
    r.set_cookie("demo_user", username, httponly=True, samesite="lax")
    return r


@app.get("/api/projects")
def api_projects(request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    return [project_card(p, date.today()) for p in visible_projects_query(db, user).all()]


@app.get("/api/projects/{code}")
def api_project(code: str, request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return project_detail(p, date.today())


@app.post("/api/alerts/{alert_id}/status")
def alert_status(alert_id: int, status: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    allowed = {"OPEN", "ACKNOWLEDGED", "RESOLVED", "IGNORED"}
    if status not in allowed:
        raise HTTPException(400, "Invalid status")
    user = current_user(request, db)
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    p = visible_projects_query(db, user).filter(Project.id == alert.project_id).first()
    if not p:
        raise HTTPException(403, "Not authorized")
    if alert.source_kind == "RULE" and status in {"RESOLVED", "IGNORED"}:
        raise HTTPException(409, "Questo alert deriva da una regola deterministica: si risolve solo quando cambia il dato sorgente.")
    alert.status = status
    db.commit()
    return {"ok": True, "status": status, "message": f"Alert aggiornato a {status}. La condizione sorgente resta invariata."}


@app.post("/api/alerts/{alert_id}/create-action")
def create_action_from_alert(alert_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    p = visible_projects_query(db, user).filter(Project.id == alert.project_id).first()
    if not p:
        raise HTTPException(403, "Not authorized")
    marker = f"ALERT:{alert.id}"
    existing = db.query(Action).filter(Action.project_id == p.id, Action.source == marker, Action.status.notin_(["CLOSED", "RESOLVED"])).first()
    if existing:
        return {"ok": True, "action_id": existing.id, "existing": True, "message": "Esiste già un'attività aperta collegata a questa criticità."}
    suggestion = suggested_action(alert, p, date.today())
    action = Action(
        project_id=p.id,
        title=suggestion["title"],
        owner=suggestion["owner"],
        owner_kind="DEPARTMENT" if suggestion["owner"] in DEPARTMENTS else "USER",
        requester=user.display_name,
        action_type=suggestion.get("action_type", "VERIFY"),
        priority=suggestion.get("priority", "NORMAL"),
        due_date=suggestion["due_date"],
        status="OPEN",
        source=marker,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return {"ok": True, "action_id": action.id, "existing": False, "message": f"Attività creata e assegnata a {action.owner} con scadenza {action.due_date}. L'alert resta aperto finché la condizione sorgente non si risolve."}


@app.post("/api/actions/{action_id}/status")
def action_status(action_id: int, status: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    allowed = {"OPEN", "IN_PROGRESS", "PENDING_VALIDATION", "CLOSED", "RESOLVED"}
    if status not in allowed:
        raise HTTPException(400, "Invalid status")
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Action not found")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Not authorized")
    action.status = status
    db.commit()
    messages = {
        "OPEN": "Attività riaperta.",
        "IN_PROGRESS": "Attività avviata e impostata In corso.",
        "PENDING_VALIDATION": "Risposta ricevuta: in attesa di validazione del richiedente.",
        "CLOSED": "Attività chiusa dopo validazione. Eventuali alert collegati restano attivi finché il dato sorgente non cambia.",
        "RESOLVED": "Attività completata.",
    }
    return {"ok": True, "status": status, "message": messages[status]}


@app.post("/api/actions/{action_id}/assign")
def assign_action(action_id: int, owner: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    allowed = {u.owner_key for u in db.query(User).all() if u.owner_key}
    allowed.update(DEPARTMENTS)
    if owner not in allowed:
        raise HTTPException(400, "Utente non disponibile per l'assegnazione")
    old = action.owner
    action.owner = owner
    action.owner_kind = "DEPARTMENT" if owner in DEPARTMENTS else "USER"
    db.commit()
    return {"ok": True, "owner": owner, "message": f"Attività riassegnata: {old} → {owner}."}


def _suggest_task_message(action: Action) -> str:
    due = action.due_date.strftime("%d/%m") if action.due_date else "appena possibile"
    title = action.title.rstrip(".")
    return f"Ciao {action.owner}, puoi occuparti di {title[0].lower() + title[1:] if title else 'questa attività'}? Ti chiedo un aggiornamento entro {due}; se ci sono blocchi, indicameli direttamente qui. Grazie."


@app.get("/api/actions/{action_id}/suggest-message")
def suggest_action_message(action_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    return {"ok": True, "text": _suggest_task_message(action), "message": "Testo proposto per invio manuale. Puoi copiarlo/modificarlo; il cockpit non invia comunicazioni."}


@app.post("/api/actions/{action_id}/messages")
def add_action_message(action_id: int, body: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    text = body.strip()
    if not text:
        raise HTTPException(400, "Scrivi un messaggio prima di aggiungerlo al task")
    msg = ActionMessage(action_id=action.id, author=user.display_name, body=text, source="MANUAL")
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"ok": True, "message_id": msg.id, "message": f"Messaggio aggiunto al task e visibile a chi lo gestisce."}


@app.post("/api/actions/{action_id}/outbound")
def register_outbound_message(action_id: int, body: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    """Register text prepared/sent manually outside the cockpit. No external send occurs."""
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    text = body.strip()
    if not text:
        raise HTTPException(400, "Scrivi il testo da inviare")
    msg = ActionMessage(action_id=action.id, author=user.display_name, body=text, source="OUTBOUND")
    db.add(msg)
    if action.status == "OPEN":
        action.status = "IN_PROGRESS"
    db.commit()
    db.refresh(msg)
    return {"ok": True, "message_id": msg.id, "message": "Testo registrato come comunicazione in uscita manuale. Il cockpit non ha inviato alcun messaggio."}

@app.post("/api/actions/{action_id}/response")
def submit_action_response(action_id: int, body: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    if not _can_answer_action(user, action):
        raise HTTPException(403, "Solo il responsabile assegnato può inviare la risposta al richiedente")
    text = body.strip()
    if not text:
        raise HTTPException(400, "Inserisci la risposta da sottoporre al richiedente")
    db.add(ActionMessage(action_id=action.id, author=user.display_name, body=text, source="RESPONSE"))
    action.response_summary = text
    action.status = "PENDING_VALIDATION"
    db.commit()
    return {"ok": True, "message": "Risposta inviata al richiedente. L'attività resta aperta finché il richiedente non la valida."}


@app.post("/api/actions/{action_id}/validate")
def validate_action_response(action_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    if action.status != "PENDING_VALIDATION":
        raise HTTPException(409, "Non c'è una risposta in attesa di validazione")
    if not _can_validate_action(user, action):
        raise HTTPException(403, "La risposta deve essere validata dal richiedente o dalla Direzione")
    action.status = "CLOSED"
    action.validated_by = user.display_name
    action.validated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Risposta validata e attività chiusa. L'alert sorgente verrà ricalcolato sui dati strutturati."}


@app.post("/api/actions/{action_id}/clarify")
def request_action_clarification(action_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    p = visible_projects_query(db, user).filter(Project.id == action.project_id).first()
    if not p:
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    if not _can_validate_action(user, action):
        raise HTTPException(403, "Solo il richiedente o la Direzione possono chiedere un chiarimento")
    action.status = "IN_PROGRESS"
    action.validated_by = None
    action.validated_at = None
    db.add(ActionMessage(action_id=action.id, author=user.display_name, body="Richiesto ulteriore chiarimento prima della chiusura.", source="VALIDATION"))
    db.commit()
    return {"ok": True, "message": "Richiesto chiarimento: l'attività torna In corso."}


@app.post("/api/projects/{code}/vda/{vda_code}/saving")
def set_vda_saving(code: str, vda_code: str, confirmed: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    """Classify a VdA saving in the cockpit operational layer; source snapshots remain untouched."""
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Commessa non trovata")
    if confirmed not in {"true", "false"}:
        raise HTTPException(400, "Valore non valido")
    if not p.control_snapshots:
        raise HTTPException(409, "Nessuno snapshot di controllo disponibile")
    snap = max(p.control_snapshots, key=lambda x: (x.captured_at, x.id or 0))
    lines = db.query(ProjectControlLine).filter(ProjectControlLine.snapshot_id == snap.id, ProjectControlLine.vda_code == vda_code).all()
    if not lines:
        raise HTTPException(404, "VdA non trovata")
    decision = db.query(CockpitDecision).filter(
        CockpitDecision.project_id == p.id,
        CockpitDecision.decision_type == "VDA_SAVING",
        CockpitDecision.decision_key == vda_code,
    ).first()
    if confirmed == "true":
        if not decision:
            decision = CockpitDecision(project_id=p.id, decision_type="VDA_SAVING", decision_key=vda_code)
            db.add(decision)
        decision.value = "CONSOLIDATED"
        decision.status = "ACTIVE"
        decision.note = "Saving confermato nel margine di commessa; non modifica il budget delle altre VdA né i dati Galileo."
        decision.created_by = user.display_name
        message = "Saving confermato nel margine di commessa. Nessun dato Galileo è stato modificato."
    else:
        if decision:
            decision.status = "REVOKED"
            decision.note = "Consolidamento revocato; la VdA torna da qualificare."
            decision.created_by = user.display_name
        message = "Conferma saving revocata; la voce torna da qualificare. Nessun dato sorgente è stato modificato."
    db.commit()
    return {"ok": True, "message": message}


CONTRACT_CONDITION_KEYS = {"effective_date", "delivery_date", "payment_terms", "incoterm", "penalties"}

@app.post("/api/projects/{code}/contract-condition/{condition_key}")
def set_contract_condition(
    code: str, condition_key: str, value: str = Form(...), note: str = Form(""),
    source_ref: str = Form(""), freeze: str = Form("true"), request: Request = None, db: Session = Depends(get_db)
):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Commessa non trovata")
    if condition_key not in CONTRACT_CONDITION_KEYS:
        raise HTTPException(400, "Condizione non modificabile dal cockpit")
    clean = value.strip()
    if not clean:
        raise HTTPException(400, "Inserisci il valore operativo da validare")
    decision = db.query(CockpitDecision).filter(
        CockpitDecision.project_id == p.id, CockpitDecision.decision_type == "CONTRACT_CONDITION", CockpitDecision.decision_key == condition_key
    ).first()
    if not decision:
        decision = CockpitDecision(project_id=p.id, decision_type="CONTRACT_CONDITION", decision_key=condition_key)
        db.add(decision)
    decision.value = clean
    decision.note = note.strip() or None
    decision.source_ref = source_ref.strip() or None
    decision.status = "FROZEN" if freeze == "true" else "DRAFT"
    decision.created_by = user.display_name
    db.commit()
    return {
        "ok": True, "status": decision.status,
        "message": "Condizione congelata nella Contract Baseline." if decision.status == "FROZEN" else "Bozza salvata nel layer operativo del cockpit.",
    }

@app.post("/api/projects/{code}/contract-condition/{condition_key}/reopen")
def reopen_contract_condition(code: str, condition_key: str, reason: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Commessa non trovata")
    decision = db.query(CockpitDecision).filter(
        CockpitDecision.project_id == p.id, CockpitDecision.decision_type == "CONTRACT_CONDITION", CockpitDecision.decision_key == condition_key
    ).first()
    if not decision:
        raise HTTPException(404, "Condizione non congelata")
    if not reason.strip():
        raise HTTPException(400, "Indica il motivo della riapertura")
    decision.status = "REOPENED"
    decision.note = ((decision.note + " | ") if decision.note else "") + f"Riaperta da {user.display_name}: {reason.strip()}"
    decision.created_by = user.display_name
    db.commit()
    return {"ok": True, "message": "Chiarimento riaperto. La fonte contrattuale originale non è stata modificata."}

@app.post("/api/projects/{code}/requirements/{requirement_id}/create-commercial-review")
def create_requirement_commercial_review(code: str, requirement_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Commessa non trovata")
    req = db.query(ProjectRequirement).filter(ProjectRequirement.id == requirement_id, ProjectRequirement.project_id == p.id).first()
    if not req:
        raise HTTPException(404, "Requisito non trovato")
    marker = f"REQ:{req.id}"
    existing = db.query(Action).filter(Action.project_id == p.id, Action.source == marker, Action.status.notin_(["CLOSED", "RESOLVED"])).first()
    if existing:
        return {"ok": True, "action_id": existing.id, "existing": True, "message": "Esiste già una verifica commerciale aperta per questo change potenziale."}
    action = Action(
        project_id=p.id, title=f"Verificare copertura contrattuale/economica: {req.title}",
        owner=p.sales_owner if p.sales_owner != "N/D" else "Commerciale", owner_kind="USER" if p.sales_owner != "N/D" else "DEPARTMENT",
        requester=user.display_name, due_date=date.today() + timedelta(days=3), status="OPEN", source=marker,
        action_type="VERIFY", priority="HIGH",
    )
    db.add(action)
    db.commit(); db.refresh(action)
    return {"ok": True, "action_id": action.id, "existing": False, "message": "Verifica commerciale creata. Nessun dato contrattuale è stato modificato."}

@app.post("/api/projects/{code}/requirements/{requirement_id}/disposition")
def set_requirement_disposition(code: str, requirement_id: int, disposition: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Commessa non trovata")
    req = db.query(ProjectRequirement).filter(ProjectRequirement.id == requirement_id, ProjectRequirement.project_id == p.id).first()
    if not req:
        raise HTTPException(404, "Requisito non trovato")
    if disposition not in {"DISMISSED", "CONFIRMED"}:
        raise HTTPException(400, "Disposizione non valida")
    decision = db.query(CockpitDecision).filter(
        CockpitDecision.project_id == p.id, CockpitDecision.decision_type == "REQUIREMENT_DISPOSITION", CockpitDecision.decision_key == req.requirement_key
    ).first()
    if not decision:
        decision = CockpitDecision(project_id=p.id, decision_type="REQUIREMENT_DISPOSITION", decision_key=req.requirement_key)
        db.add(decision)
    decision.value = disposition
    decision.status = "ACTIVE"
    decision.note = f"Finding tecnico {disposition.lower()} nel cockpit; la fonte {req.source_ref or req.source_kind} resta invariata."
    decision.source_ref = req.source_ref
    decision.created_by = user.display_name
    if disposition == "DISMISSED":
        for finding in p.agent_findings:
            if finding.source_ref == req.source_ref and finding.status in ("NEW", "VALIDATED"):
                finding.status = "DISMISSED"
    db.commit()
    return {"ok": True, "message": "Finding scartato nel layer operativo; la fonte tecnica non è stata modificata." if disposition == "DISMISSED" else "Finding confermato nel layer operativo."}

@app.post("/api/projects/{code}/confidence-plan")
def create_confidence_plan(code: str, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Commessa non trovata")
    conf = confidence_summary(p, date.today())
    created = []
    existing_ids = []
    for domain in conf["ordered"]:
        if domain["level"] not in ("LOW", "INSUFFICIENT"):
            continue
        marker = f"CONFIDENCE:{domain['key']}"
        existing = db.query(Action).filter(Action.project_id == p.id, Action.source == marker, Action.status.notin_(["CLOSED", "RESOLVED"])).first()
        if existing:
            existing_ids.append(existing.id); continue
        owner = domain["recovery_owner"].split(" /")[0]
        action = Action(
            project_id=p.id, title=f"Recuperare confidence {domain['label']}: {domain['level_label']} → {domain['target_level_label']}",
            owner=owner, owner_kind="DEPARTMENT", requester=user.display_name, due_date=date.today() + timedelta(days=5),
            status="OPEN", source=marker, action_type="VERIFY", priority="HIGH" if domain["level"] == "INSUFFICIENT" else "NORMAL",
        )
        db.add(action); db.flush(); created.append(action.id)
    db.commit()
    return {"ok": True, "created": created, "existing": existing_ids, "message": f"Piano confidence: {len(created)} azioni create, {len(existing_ids)} già presenti."}


@app.post("/api/recompute")
def api_recompute(db: Session = Depends(get_db)):
    recompute_alerts(db)
    return {"ok": True}


@app.post("/api/demo/reset")
def reset_demo(request: Request, db: Session = Depends(get_db)):
    if not settings.destructive_reset_enabled:
        raise HTTPException(403, "Il reset distruttivo e disabilitato nel runtime demo")
    user = current_user(request, db)
    if user.role != "DIRECTOR":
        raise HTTPException(403, "Only Director can reset demo")
    db.close()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as fresh:
        seed(fresh)
        analyze_all_projects(fresh)
        recompute_alerts(fresh)
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/projects/{code}/intelligence/analyze")
def run_intelligence(code: str, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Project not found or not visible")
    result = analyze_project(db, p)
    recompute_alerts(db)
    return {"ok": True, **result, "message": f"Analisi completata: {result['messages']} comunicazioni controllate, {result['created']} nuovi segnali, {result['updated']} già conosciuti aggiornati."}


@app.post("/api/findings/{finding_id}/status")
def finding_status(finding_id: int, status: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    allowed = {"NEW", "VALIDATED", "DISMISSED"}
    if status not in allowed:
        raise HTTPException(400, "Invalid status")
    user = current_user(request, db)
    finding = db.query(AgentFinding).filter(AgentFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(404, "Segnale non trovato")
    p = visible_projects_query(db, user).filter(Project.id == finding.project_id).first()
    if not p:
        raise HTTPException(403, "Not authorized")
    if finding.status == "APPLIED":
        raise HTTPException(409, "Questo segnale è già stato registrato nella commessa e non può tornare in revisione.")
    finding.status = status
    db.commit()
    recompute_alerts(db)
    message = {
        "VALIDATED": "Interpretazione confermata. Ora puoi decidere se registrare l'informazione nella commessa.",
        "DISMISSED": "Segnale scartato. Non avrà alcun effetto sulla commessa.",
        "NEW": "Segnale riportato tra quelli da verificare.",
    }[status]
    return {"ok": True, "status": status, "message": message}


@app.post("/api/findings/{finding_id}/apply")
def finding_apply(finding_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    finding = db.query(AgentFinding).filter(AgentFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(404, "Segnale non trovato")
    p = visible_projects_query(db, user).filter(Project.id == finding.project_id).first()
    if not p:
        raise HTTPException(403, "Not authorized")
    try:
        result = apply_finding(db, finding, p, date.today())
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    recompute_alerts(db)
    return result


@app.post("/api/projects/{code}/communications/analyze")
def add_and_analyze_communication(
    code: str, request: Request,
    subject: str = Form(...), body: str = Form(...), sender: str = Form("client@example.com"),
    direction: str = Form("INBOUND"), db: Session = Depends(get_db)
):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Project not found or not visible")
    direction = direction.upper()
    if direction not in {"INBOUND", "OUTBOUND"}:
        raise HTTPException(400, "Invalid direction")
    recipient = "brofind@demo.local" if direction == "INBOUND" else "client@demo.local"
    comm = Communication(
        project_id=p.id, date=date.today(), direction=direction, sender=sender.strip() or "client@example.com",
        recipient=recipient, subject=subject.strip(), body=body.strip(), topic="Live demo",
        responded=(direction == "OUTBOUND"), reminders_count=0, source_ref=None
    )
    db.add(comm)
    db.flush()
    comm.source_ref = f"demo:manual-email:{comm.id}"
    db.commit()
    db.refresh(comm)
    result = analyze_project(db, p)
    recompute_alerts(db)
    return {
        "ok": True,
        "communication_id": comm.id,
        "created": result["created"],
        "updated": result["updated"],
        "message": f"Mail aggiunta e analizzata: {result['created']} nuovi finding, {result['updated']} aggiornati.",
    }


@app.post("/import", response_class=HTMLResponse)
async def excel_import(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if user.role != "DIRECTOR":
        raise HTTPException(403, "Only Director can import in demo")
    content = await file.read()
    try:
        stats = import_b1_control_workbook(content, db) if is_b1_workbook_candidate(content) else import_workbook(content, db)
        analyze_all_projects(db)
        recompute_alerts(db)
    except Exception as e:
        return templates.TemplateResponse(request=request, name="import_result.html", context={"ok": False, "message": str(e), "users": db.query(User).all(), "user": user, "version": VERSION})
    return templates.TemplateResponse(request=request, name="import_result.html", context={"ok": True, "message": f"Import completato: {stats}", "users": db.query(User).all(), "user": user, "version": VERSION})


@app.get("/download/template")
def download_template():
    path = BASE / "data" / "BROFIND_PROJECT_IMPORT.xlsx"
    if not path.exists():
        build_template(path)
    return FileResponse(path, filename="BROFIND_PROJECT_IMPORT.xlsx")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "runtime": settings.runtime,
        "database": settings.database_label,
    }
