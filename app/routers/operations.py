"""Layer operativo: alert, attività e messaggi delle attività."""

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from ..analytics import suggested_action
from ..clock import utcnow
from ..db import get_db
from ..models import Action, ActionMessage, Alert, Project, User
from ..security import current_user, visible_projects_query
from ..web import DEPARTMENTS, can_answer_action, can_validate_action

router = APIRouter()


def _visible_action(db: Session, user: User, action_id: int) -> Action:
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(404, "Attività non trovata")
    if not visible_projects_query(db, user).filter(Project.id == action.project_id).first():
        raise HTTPException(403, "Non sei autorizzato su questa commessa")
    return action


@router.post("/api/alerts/{alert_id}/status")
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
        raise HTTPException(
            409, "Questo alert deriva da una regola deterministica: si risolve solo quando cambia il dato sorgente."
        )
    alert.status = status
    db.commit()
    return {
        "ok": True,
        "status": status,
        "message": f"Alert aggiornato a {status}. La condizione sorgente resta invariata.",
    }


@router.post("/api/alerts/{alert_id}/create-action")
def create_action_from_alert(alert_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    p = visible_projects_query(db, user).filter(Project.id == alert.project_id).first()
    if not p:
        raise HTTPException(403, "Not authorized")
    marker = f"ALERT:{alert.id}"
    existing = (
        db.query(Action)
        .filter(Action.project_id == p.id, Action.source == marker, Action.status.notin_(["CLOSED", "RESOLVED"]))
        .first()
    )
    if existing:
        return {
            "ok": True,
            "action_id": existing.id,
            "existing": True,
            "message": "Esiste già un'attività aperta collegata a questa criticità.",
        }
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
    return {
        "ok": True,
        "action_id": action.id,
        "existing": False,
        "message": f"Attività creata e assegnata a {action.owner} con scadenza {action.due_date}. L'alert resta aperto finché la condizione sorgente non si risolve.",
    }


@router.post("/api/actions/{action_id}/status")
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
    # AD-001: la transizione verso CLOSED non verifica ancora la validazione del richiedente.
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


@router.post("/api/actions/{action_id}/assign")
def assign_action(action_id: int, owner: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = _visible_action(db, user, action_id)
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
    subject = title[0].lower() + title[1:] if title else "questa attività"
    return (
        f"Ciao {action.owner}, puoi occuparti di {subject}? Ti chiedo un aggiornamento entro {due}; "
        "se ci sono blocchi, indicameli direttamente qui. Grazie."
    )


@router.get("/api/actions/{action_id}/suggest-message")
def suggest_action_message(action_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = _visible_action(db, user, action_id)
    return {
        "ok": True,
        "text": _suggest_task_message(action),
        "message": "Testo proposto per invio manuale. Puoi copiarlo/modificarlo; il cockpit non invia comunicazioni.",
    }


@router.post("/api/actions/{action_id}/messages")
def add_action_message(action_id: int, body: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = _visible_action(db, user, action_id)
    text = body.strip()
    if not text:
        raise HTTPException(400, "Scrivi un messaggio prima di aggiungerlo al task")
    msg = ActionMessage(action_id=action.id, author=user.display_name, body=text, source="MANUAL")
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"ok": True, "message_id": msg.id, "message": "Messaggio aggiunto al task e visibile a chi lo gestisce."}


@router.post("/api/actions/{action_id}/outbound")
def register_outbound_message(
    action_id: int, body: str = Form(...), request: Request = None, db: Session = Depends(get_db)
):
    """Registra un testo preparato/inviato manualmente fuori dal cockpit. Nessun invio esterno."""
    user = current_user(request, db)
    action = _visible_action(db, user, action_id)
    text = body.strip()
    if not text:
        raise HTTPException(400, "Scrivi il testo da inviare")
    msg = ActionMessage(action_id=action.id, author=user.display_name, body=text, source="OUTBOUND")
    db.add(msg)
    if action.status == "OPEN":
        action.status = "IN_PROGRESS"
    db.commit()
    db.refresh(msg)
    return {
        "ok": True,
        "message_id": msg.id,
        "message": "Testo registrato come comunicazione in uscita manuale. Il cockpit non ha inviato alcun messaggio.",
    }


@router.post("/api/actions/{action_id}/response")
def submit_action_response(
    action_id: int, body: str = Form(...), request: Request = None, db: Session = Depends(get_db)
):
    user = current_user(request, db)
    action = _visible_action(db, user, action_id)
    if not can_answer_action(user, action):
        raise HTTPException(403, "Solo il responsabile assegnato può inviare la risposta al richiedente")
    text = body.strip()
    if not text:
        raise HTTPException(400, "Inserisci la risposta da sottoporre al richiedente")
    db.add(ActionMessage(action_id=action.id, author=user.display_name, body=text, source="RESPONSE"))
    action.response_summary = text
    action.status = "PENDING_VALIDATION"
    db.commit()
    return {
        "ok": True,
        "message": "Risposta inviata al richiedente. L'attività resta aperta finché il richiedente non la valida.",
    }


@router.post("/api/actions/{action_id}/validate")
def validate_action_response(action_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = _visible_action(db, user, action_id)
    if action.status != "PENDING_VALIDATION":
        raise HTTPException(409, "Non c'è una risposta in attesa di validazione")
    if not can_validate_action(user, action):
        raise HTTPException(403, "La risposta deve essere validata dal richiedente o dalla Direzione")
    action.status = "CLOSED"
    action.validated_by = user.display_name
    action.validated_at = utcnow()
    db.commit()
    return {
        "ok": True,
        "message": "Risposta validata e attività chiusa. L'alert sorgente verrà ricalcolato sui dati strutturati.",
    }


@router.post("/api/actions/{action_id}/clarify")
def request_action_clarification(action_id: int, request: Request = None, db: Session = Depends(get_db)):
    user = current_user(request, db)
    action = _visible_action(db, user, action_id)
    if not can_validate_action(user, action):
        raise HTTPException(403, "Solo il richiedente o la Direzione possono chiedere un chiarimento")
    action.status = "IN_PROGRESS"
    action.validated_by = None
    action.validated_at = None
    db.add(
        ActionMessage(
            action_id=action.id,
            author=user.display_name,
            body="Richiesto ulteriore chiarimento prima della chiusura.",
            source="VALIDATION",
        )
    )
    db.commit()
    return {"ok": True, "message": "Richiesto chiarimento: l'attività torna In corso."}
