from __future__ import annotations

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from .models import Action, AgentFinding, ChangeRequest, Issue, Project


def _communication_text(finding: AgentFinding) -> str:
    c = finding.communication
    if not c:
        return ""
    return f"{c.subject or ''} {c.topic or ''} {c.body or ''}".lower()


def _select_milestone(project: Project, finding: AgentFinding):
    text = _communication_text(finding)
    # Prefer explicit milestone terms found in the communication.
    aliases = {
        "fat": ("fat",),
        "sat": ("sat",),
        "delivery": ("delivery", "shipment", "consegna", "livraison"),
        "acceptance": ("acceptance", "take over", "take-over", "reception", "réception"),
        "commissioning": ("commissioning", "avviamento", "mise en service"),
    }
    for key, terms in aliases.items():
        if any(t in text for t in terms):
            for m in project.milestones:
                if key in m.name.lower() or any(t in m.name.lower() for t in terms):
                    return m
    if len(project.milestones) == 1:
        return project.milestones[0]
    return None


def application_preview(finding: AgentFinding, project: Project) -> dict:
    """Describe the controlled consequence available after human validation."""
    ft = finding.finding_type
    if ft == "AGENT_SCHEDULE_RISK":
        date_txt = finding.extracted_date.strftime("%d/%m/%Y") if finding.extracted_date else "data da verificare"
        return {
            "action": "CREATE_ACTION",
            "label": f"Verifica con il PM la nuova data ({date_txt})",
            "effect": "Il cockpit crea una verifica operativa. Il planning/forecast ufficiale resta read-only e si aggiornerà dalla sorgente autorevole.",
        }
    if ft == "AGENT_PAYMENT_PROMISE":
        return {
            "action": "CREATE_ACTION",
            "label": "Crea un controllo sull'incasso / promessa di pagamento",
            "effect": "Il cockpit crea un follow-up operativo. Fatture, incassi e comunicazioni sorgente non vengono modificati.",
        }
    if ft == "AGENT_DOCUMENT_REQUEST":
        return {
            "action": "CREATE_DOCUMENT_ISSUE",
            "label": "Registra la documentazione ancora da completare",
            "effect": "La richiesta viene registrata come criticità di commessa e diventa visibile nel riepilogo principale se richiede presidio.",
        }
    if ft == "AGENT_CHANGE_REQUEST":
        return {
            "action": "CREATE_CHANGE",
            "label": "Registra una possibile variante / extra",
            "effect": "La richiesta viene registrata come variante non ancora ordinata e resta sotto controllo finché non viene formalizzata.",
        }
    if ft == "AGENT_TECHNICAL_RISK":
        return {
            "action": "CREATE_TECHNICAL_ISSUE",
            "label": "Registra il problema tecnico",
            "effect": "Il problema diventa una criticità strutturata della commessa e viene mostrato nel riepilogo finché resta aperto.",
        }
    if ft == "AGENT_CUSTOMER_ESCALATION":
        return {
            "action": "CREATE_COMMUNICATION_ISSUE",
            "label": "Registra il sollecito e assegna una risposta",
            "effect": "Il sollecito diventa una criticità visibile della commessa e viene creata un'attività di risposta con owner e scadenza.",
        }
    return {
        "action": "CREATE_ACTION",
        "label": "Crea attività di verifica",
        "effect": "Viene creata un'attività operativa senza modificare dati ufficiali.",
    }


def _existing_action(db: Session, project_id: int, finding_id: int):
    marker = f"FINDING:{finding_id}"
    return db.query(Action).filter(Action.project_id == project_id, Action.source == marker).first()


def apply_finding(db: Session, finding: AgentFinding, project: Project, today: date | None = None) -> dict:
    today = today or date.today()
    if finding.status != "VALIDATED":
        raise ValueError("Il finding deve essere validato prima di poter essere applicato alla commessa.")
    if finding.applied_kind or finding.status == "APPLIED":
        return {
            "ok": True,
            "already_applied": True,
            "kind": finding.applied_kind,
            "ref": finding.applied_ref,
            "summary": finding.applied_summary,
        }

    preview = application_preview(finding, project)
    action = preview["action"]
    ref = None
    summary = None

    if action == "CREATE_DOCUMENT_ISSUE":
        issue = Issue(
            project_id=project.id,
            category="DOCUMENTATION",
            title=finding.title,
            severity=finding.severity,
            status="OPEN",
            blocking="blocking" in (finding.summary or "").lower() or "cannot" in (finding.evidence or "").lower(),
            due_date=finding.extracted_date,
            source_ref=finding.source_ref,
        )
        db.add(issue)
        db.flush()
        ref = f"issue:{issue.id}"
        summary = f"Issue documentale #{issue.id} creata."

    elif action == "CREATE_TECHNICAL_ISSUE":
        issue = Issue(
            project_id=project.id,
            category="TECHNICAL",
            title=finding.title,
            severity=finding.severity,
            status="OPEN",
            blocking=finding.severity in ("HIGH", "CRITICAL"),
            due_date=finding.extracted_date,
            source_ref=finding.source_ref,
        )
        db.add(issue)
        db.flush()
        ref = f"issue:{issue.id}"
        summary = f"Issue tecnica #{issue.id} creata."

    elif action == "CREATE_COMMUNICATION_ISSUE":
        issue = Issue(
            project_id=project.id,
            category="COMMUNICATION",
            title="Cliente in attesa di risposta: " + finding.title,
            severity=finding.severity,
            status="OPEN",
            blocking=False,
            due_date=finding.extracted_date,
            source_ref=finding.source_ref,
        )
        db.add(issue)
        db.flush()
        task = _existing_action(db, project.id, finding.id)
        if not task:
            due = today + timedelta(days=2)
            task = Action(
                project_id=project.id,
                title=finding.suggested_action,
                owner=finding.suggested_owner,
                due_date=due,
                status="OPEN",
                source=f"FINDING:{finding.id}",
            )
            db.add(task)
            db.flush()
        ref = f"issue:{issue.id};action:{task.id}"
        summary = f"Sollecito cliente registrato come criticità #{issue.id}; attività #{task.id} assegnata a {task.owner}."

    elif action == "CREATE_CHANGE":
        requested = finding.communication.date if finding.communication else today
        change = ChangeRequest(
            project_id=project.id,
            description=finding.title,
            requested_date=requested,
            estimated_cost=finding.extracted_amount or 0,
            quoted_value=0,
            order_received=False,
            work_started=False,
        )
        db.add(change)
        db.flush()
        ref = f"change:{change.id}"
        summary = f"Variante/extra #{change.id} aperta da verificare."

    else:  # CREATE_ACTION — cockpit operational layer only
        existing = _existing_action(db, project.id, finding.id)
        if existing:
            ref = f"action:{existing.id}"
            summary = f"Attività #{existing.id} già presente."
        else:
            due = today + timedelta(days=3)
            task = Action(
                project_id=project.id,
                title=finding.suggested_action,
                owner=finding.suggested_owner,
                due_date=due,
                status="OPEN",
                source=f"FINDING:{finding.id}",
            )
            db.add(task)
            db.flush()
            ref = f"action:{task.id}"
            summary = f"Attività #{task.id} creata per {task.owner}. Nessun dato sorgente è stato modificato."

    finding.status = "APPLIED"
    finding.applied_kind = action
    finding.applied_ref = ref
    finding.applied_summary = summary
    finding.applied_at = datetime.utcnow()
    db.commit()

    return {"ok": True, "already_applied": False, "kind": action, "ref": ref, "summary": summary}
