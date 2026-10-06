"""Decisioni operative del cockpit: saving, Contract Baseline, change potenziali, piano confidence.

Tutte scrivono solo nel layer operativo (CockpitDecision / Action): le fonti restano invariate.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from ..confidence import confidence_summary
from ..db import get_db
from ..models import Action, CockpitDecision, Project, ProjectControlLine, ProjectRequirement
from ..security import current_user, visible_projects_query

router = APIRouter()

CONTRACT_CONDITION_KEYS = {"effective_date", "delivery_date", "payment_terms", "incoterm", "penalties"}


def _visible_project(db: Session, request: Request, code: str):
    user = current_user(request, db)
    p = visible_projects_query(db, user).filter(Project.code == code).first()
    if not p:
        raise HTTPException(404, "Commessa non trovata")
    return user, p


def _decision(db: Session, project_id: int, decision_type: str, key: str) -> CockpitDecision | None:
    return (
        db.query(CockpitDecision)
        .filter(
            CockpitDecision.project_id == project_id,
            CockpitDecision.decision_type == decision_type,
            CockpitDecision.decision_key == key,
        )
        .first()
    )


@router.post("/api/projects/{code}/vda/{vda_code}/saving")
def set_vda_saving(
    code: str, vda_code: str, confirmed: str = Form(...), request: Request = None, db: Session = Depends(get_db)
):
    """Classifica il saving di una VdA nel layer operativo; gli snapshot sorgente restano invariati."""
    user, p = _visible_project(db, request, code)
    if confirmed not in {"true", "false"}:
        raise HTTPException(400, "Valore non valido")
    if not p.control_snapshots:
        raise HTTPException(409, "Nessuno snapshot di controllo disponibile")
    snap = max(p.control_snapshots, key=lambda x: (x.captured_at, x.id or 0))
    lines = (
        db.query(ProjectControlLine)
        .filter(ProjectControlLine.snapshot_id == snap.id, ProjectControlLine.vda_code == vda_code)
        .all()
    )
    if not lines:
        raise HTTPException(404, "VdA non trovata")
    decision = _decision(db, p.id, "VDA_SAVING", vda_code)
    if confirmed == "true":
        if not decision:
            decision = CockpitDecision(project_id=p.id, decision_type="VDA_SAVING", decision_key=vda_code)
            db.add(decision)
        decision.value = "CONSOLIDATED"
        decision.status = "ACTIVE"
        decision.note = (
            "Saving confermato nel margine di commessa; non modifica il budget delle altre VdA né i dati Galileo."
        )
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


@router.post("/api/projects/{code}/contract-condition/{condition_key}")
def set_contract_condition(
    code: str,
    condition_key: str,
    value: str = Form(...),
    note: str = Form(""),
    source_ref: str = Form(""),
    freeze: str = Form("true"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    user, p = _visible_project(db, request, code)
    if condition_key not in CONTRACT_CONDITION_KEYS:
        raise HTTPException(400, "Condizione non modificabile dal cockpit")
    clean = value.strip()
    if not clean:
        raise HTTPException(400, "Inserisci il valore operativo da validare")
    decision = _decision(db, p.id, "CONTRACT_CONDITION", condition_key)
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
        "ok": True,
        "status": decision.status,
        "message": "Condizione congelata nella Contract Baseline."
        if decision.status == "FROZEN"
        else "Bozza salvata nel layer operativo del cockpit.",
    }


@router.post("/api/projects/{code}/contract-condition/{condition_key}/reopen")
def reopen_contract_condition(
    code: str, condition_key: str, reason: str = Form(...), request: Request = None, db: Session = Depends(get_db)
):
    user, p = _visible_project(db, request, code)
    decision = _decision(db, p.id, "CONTRACT_CONDITION", condition_key)
    if not decision:
        raise HTTPException(404, "Condizione non congelata")
    if not reason.strip():
        raise HTTPException(400, "Indica il motivo della riapertura")
    decision.status = "REOPENED"
    decision.note = (
        (decision.note + " | ") if decision.note else ""
    ) + f"Riaperta da {user.display_name}: {reason.strip()}"
    decision.created_by = user.display_name
    db.commit()
    return {"ok": True, "message": "Chiarimento riaperto. La fonte contrattuale originale non è stata modificata."}


@router.post("/api/projects/{code}/requirements/{requirement_id}/create-commercial-review")
def create_requirement_commercial_review(
    code: str, requirement_id: int, request: Request, db: Session = Depends(get_db)
):
    user, p = _visible_project(db, request, code)
    req = (
        db.query(ProjectRequirement)
        .filter(ProjectRequirement.id == requirement_id, ProjectRequirement.project_id == p.id)
        .first()
    )
    if not req:
        raise HTTPException(404, "Requisito non trovato")
    marker = f"REQ:{req.id}"
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
            "message": "Esiste già una verifica commerciale aperta per questo change potenziale.",
        }
    has_sales_owner = p.sales_owner != "N/D"
    action = Action(
        project_id=p.id,
        title=f"Verificare copertura contrattuale/economica: {req.title}",
        owner=p.sales_owner if has_sales_owner else "Commerciale",
        owner_kind="USER" if has_sales_owner else "DEPARTMENT",
        requester=user.display_name,
        due_date=date.today() + timedelta(days=3),
        status="OPEN",
        source=marker,
        action_type="VERIFY",
        priority="HIGH",
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return {
        "ok": True,
        "action_id": action.id,
        "existing": False,
        "message": "Verifica commerciale creata. Nessun dato contrattuale è stato modificato.",
    }


@router.post("/api/projects/{code}/requirements/{requirement_id}/disposition")
def set_requirement_disposition(
    code: str, requirement_id: int, disposition: str = Form(...), request: Request = None, db: Session = Depends(get_db)
):
    user, p = _visible_project(db, request, code)
    req = (
        db.query(ProjectRequirement)
        .filter(ProjectRequirement.id == requirement_id, ProjectRequirement.project_id == p.id)
        .first()
    )
    if not req:
        raise HTTPException(404, "Requisito non trovato")
    if disposition not in {"DISMISSED", "CONFIRMED"}:
        raise HTTPException(400, "Disposizione non valida")
    decision = _decision(db, p.id, "REQUIREMENT_DISPOSITION", req.requirement_key)
    if not decision:
        decision = CockpitDecision(
            project_id=p.id, decision_type="REQUIREMENT_DISPOSITION", decision_key=req.requirement_key
        )
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
    message = (
        "Finding scartato nel layer operativo; la fonte tecnica non è stata modificata."
        if disposition == "DISMISSED"
        else "Finding confermato nel layer operativo."
    )
    return {"ok": True, "message": message}


@router.post("/api/projects/{code}/confidence-plan")
def create_confidence_plan(code: str, request: Request, db: Session = Depends(get_db)):
    user, p = _visible_project(db, request, code)
    conf = confidence_summary(p, date.today())
    created = []
    existing_ids = []
    for domain in conf["ordered"]:
        if domain["level"] not in ("LOW", "INSUFFICIENT"):
            continue
        marker = f"CONFIDENCE:{domain['key']}"
        existing = (
            db.query(Action)
            .filter(Action.project_id == p.id, Action.source == marker, Action.status.notin_(["CLOSED", "RESOLVED"]))
            .first()
        )
        if existing:
            existing_ids.append(existing.id)
            continue
        owner = domain["recovery_owner"].split(" /")[0]
        action = Action(
            project_id=p.id,
            title=f"Recuperare confidence {domain['label']}: {domain['level_label']} → {domain['target_level_label']}",
            owner=owner,
            owner_kind="DEPARTMENT",
            requester=user.display_name,
            due_date=date.today() + timedelta(days=5),
            status="OPEN",
            source=marker,
            action_type="VERIFY",
            priority="HIGH" if domain["level"] == "INSUFFICIENT" else "NORMAL",
        )
        db.add(action)
        db.flush()
        created.append(action.id)
    db.commit()
    return {
        "ok": True,
        "created": created,
        "existing": existing_ids,
        "message": f"Piano confidence: {len(created)} azioni create, {len(existing_ids)} già presenti.",
    }
