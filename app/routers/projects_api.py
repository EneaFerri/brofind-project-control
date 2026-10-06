"""API JSON di commessa, intelligence sulle comunicazioni, finding e comandi demo."""

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Base, SessionLocal, engine, get_db
from ..intelligence import analyze_all_projects, analyze_project
from ..models import AgentFinding, Communication, Project
from ..rules import recompute_alerts
from ..security import current_user, visible_projects_query
from ..seed import seed
from ..serializers import project_card, project_detail
from ..workflow import apply_finding

router = APIRouter()


def _visible_project(db: Session, request: Request, code: str) -> Project:
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Project not found or not visible")
    return p


@router.get("/api/projects")
def api_projects(request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    return [project_card(p, date.today()) for p in visible_projects_query(db, user).all()]


@router.get("/api/projects/{code}")
def api_project(code: str, request: Request, db: Session = Depends(get_db)):
    recompute_alerts(db)
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return project_detail(p, date.today())


@router.post("/api/recompute")
def api_recompute(db: Session = Depends(get_db)):
    recompute_alerts(db)
    return {"ok": True}


@router.post("/api/demo/reset")
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


@router.post("/api/projects/{code}/intelligence/analyze")
def run_intelligence(code: str, request: Request, db: Session = Depends(get_db)):
    p = _visible_project(db, request, code)
    result = analyze_project(db, p)
    recompute_alerts(db)
    return {
        "ok": True,
        **result,
        "message": f"Analisi completata: {result['messages']} comunicazioni controllate, {result['created']} nuovi segnali, {result['updated']} già conosciuti aggiornati.",
    }


@router.post("/api/findings/{finding_id}/status")
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


@router.post("/api/findings/{finding_id}/apply")
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
        raise HTTPException(409, str(exc)) from exc
    recompute_alerts(db)
    return result


@router.post("/api/projects/{code}/communications/analyze")
def add_and_analyze_communication(
    code: str,
    request: Request,
    subject: str = Form(...),
    body: str = Form(...),
    sender: str = Form("client@example.com"),
    direction: str = Form("INBOUND"),
    db: Session = Depends(get_db),
):
    p = _visible_project(db, request, code)
    direction = direction.upper()
    if direction not in {"INBOUND", "OUTBOUND"}:
        raise HTTPException(400, "Invalid direction")
    recipient = "brofind@demo.local" if direction == "INBOUND" else "client@demo.local"
    comm = Communication(
        project_id=p.id,
        date=date.today(),
        direction=direction,
        sender=sender.strip() or "client@example.com",
        recipient=recipient,
        subject=subject.strip(),
        body=body.strip(),
        topic="Live demo",
        responded=(direction == "OUTBOUND"),
        reminders_count=0,
        source_ref=None,
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
