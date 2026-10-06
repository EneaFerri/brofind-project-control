from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from math import ceil

from .control import control_summary
from .models import Alert, Project
from .rules import (
    attention_score,
    budget_summary,
    finance_summary,
    has_control_data,
    is_data_acquisition,
    project_health,
)

ACTIVE_ALERT_STATUSES = ("OPEN", "ACKNOWLEDGED")

DIMENSION_LABELS = {
    "FINANCE": "Finanza",
    "BUDGET": "Budget",
    "TECHNICAL": "Tecnica",
    "SCHEDULE": "Tempi",
    "CONTRACT": "Contratto",
    "PROCUREMENT": "Acquisti",
}

STATUS_LABELS = {
    "GREEN": "Regolare",
    "YELLOW": "Attenzione",
    "RED": "Critico",
    "ND": "N/D",
    "PARTIAL": "Dati parziali",
}


def active_alerts(project: Project) -> list[Alert]:
    return [a for a in project.alerts if a.status in ACTIVE_ALERT_STATUSES]


def priority_summary(project: Project) -> dict:
    if is_data_acquisition(project) and not has_control_data(project):
        return {
            "key": "NO_DATA",
            "label": "Acquisizione dati",
            "tone": "neutral",
            "score": 0,
            "meaning": "Le fonti dati non sono ancora collegate o importate.",
        }
    alerts = active_alerts(project)
    score = attention_score(project)
    severities = {a.severity for a in alerts}
    if "CRITICAL" in severities or score >= 20:
        return {
            "key": "CRITICAL",
            "label": "Critica",
            "tone": "critical",
            "score": score,
            "meaning": "Oltre la normale recuperabilità: richiede escalation o decisione direzionale.",
        }
    if "HIGH" in severities or score >= 8:
        return {
            "key": "HIGH",
            "label": "Da intervenire",
            "tone": "intervene",
            "score": score,
            "meaning": "Problema concreto ma ancora recuperabile con un intervento tempestivo.",
        }
    if alerts:
        return {
            "key": "MEDIUM",
            "label": "Da presidiare",
            "tone": "amber",
            "score": score,
            "meaning": "Rischio o incertezza significativa da presidiare.",
        }
    health = project_health(project)
    if not any(v == "GREEN" for v in health.values()):
        return {
            "key": "NO_DATA",
            "label": "Dati insufficienti",
            "tone": "neutral",
            "score": score,
            "meaning": "Le evidenze disponibili non consentono una valutazione affidabile.",
        }
    return {
        "key": "OK",
        "label": "Sotto controllo",
        "tone": "green",
        "score": score,
        "meaning": "Valutato e senza anomalie rilevanti aperte.",
    }


def unbilled_milestones(project: Project) -> list:
    invoice_milestones = {i.milestone_name for i in project.invoices if i.milestone_name}
    return [
        m
        for m in project.milestones
        if m.invoice_required and m.actual_date and m.invoice_value > 0 and m.name not in invoice_milestones
    ]


def project_exposure(project: Project, today: date) -> dict:
    if is_data_acquisition(project) and not has_control_data(project):
        return {
            "overdue": 0.0,
            "unbilled": 0.0,
            "budget_overrun": 0.0,
            "control_overcommit": 0.0,
            "uncovered_changes": 0.0,
            "ld_count": 0,
            "indicative_ld": 0.0,
            "ld_milestones": [],
        }
    finance = finance_summary(project, today)
    budget = budget_summary(project)
    unbilled = sum(m.invoice_value for m in unbilled_milestones(project))
    extra_budget = max(budget["variance"], 0)
    control = control_summary(project)
    control_overcommit = (
        sum(max(r["committed_cost"] - r["operational_budget"], 0) for r in control["vda_rows"]) if control else 0.0
    )
    uncovered_changes = sum(
        (c.quoted_value if c.quoted_value > 0 else c.estimated_cost) for c in project.changes if not c.order_received
    )
    ld_milestones = []
    indicative_ld = 0.0
    for m in project.milestones:
        if not (m.ld_applicable and m.contract_date and m.forecast_date and not m.actual_date):
            continue
        if m.forecast_date <= m.contract_date:
            continue
        delay = (m.forecast_date - m.contract_date).days
        weeks = max(1, ceil(delay / 7))
        indicative = project.order_value * (m.ld_rate_weekly_pct / 100) * weeks
        indicative_ld += indicative
        ld_milestones.append({"name": m.name, "delay_days": delay, "indicative": indicative})
    return {
        "overdue": finance["overdue"],
        "unbilled": unbilled,
        "budget_overrun": extra_budget,
        "control_overcommit": control_overcommit,
        "uncovered_changes": uncovered_changes,
        "ld_count": len(ld_milestones),
        "indicative_ld": indicative_ld,
        "ld_milestones": ld_milestones,
    }


def portfolio_exposure(projects: Iterable[Project], today: date) -> dict:
    out = {
        "overdue": 0.0,
        "unbilled": 0.0,
        "budget_overrun": 0.0,
        "control_overcommit": 0.0,
        "uncovered_changes": 0.0,
        "ld_projects": 0,
        "critical_projects": 0,
    }
    for p in projects:
        e = project_exposure(p, today)
        out["overdue"] += e["overdue"]
        out["unbilled"] += e["unbilled"]
        out["budget_overrun"] += e["budget_overrun"]
        out["control_overcommit"] += e["control_overcommit"]
        out["uncovered_changes"] += e["uncovered_changes"]
        out["ld_projects"] += 1 if e["ld_count"] else 0
        out["critical_projects"] += 1 if priority_summary(p)["key"] in ("CRITICAL", "HIGH") else 0
    return out


def closing_summary(project: Project, today: date) -> dict:
    finance = finance_summary(project, today)
    unbilled = unbilled_milestones(project)
    blocking_docs = [i for i in project.issues if i.status == "OPEN" and i.category == "DOCUMENTATION" and i.blocking]
    uncovered_changes = [
        c for c in project.changes if not c.order_received and (c.work_started or c.estimated_cost > 0)
    ]
    acceptance_candidates = [
        m
        for m in project.milestones
        if any(k in m.name.lower() for k in ("acceptance", "take over", "take-over", "sat"))
    ]
    acceptance_done = any(m.actual_date for m in acceptance_candidates)

    technical = {
        "tone": "green" if project.technical_status == "CLOSED" else "amber",
        "label": "Completato" if project.technical_status == "CLOSED" else "In corso",
    }
    documentation = {
        "tone": "red" if blocking_docs else ("green" if project.technical_status == "CLOSED" else "amber"),
        "label": "Bloccante"
        if blocking_docs
        else ("Completa" if project.technical_status == "CLOSED" else "Da completare"),
    }
    invoicing = {
        "tone": "red" if unbilled else ("green" if project.technical_status == "CLOSED" else "amber"),
        "label": f"€ {sum(m.invoice_value for m in unbilled):,.0f} da fatturare"
        if unbilled
        else ("Completa" if project.technical_status == "CLOSED" else "In corso"),
    }
    payments = {
        "tone": "red" if finance["overdue"] > 0 else "green",
        "label": f"€ {finance['overdue']:,.0f} scaduti" if finance["overdue"] > 0 else "Regolare",
    }
    acceptance = {
        "tone": "green" if acceptance_done else ("amber" if acceptance_candidates else "neutral"),
        "label": "Ottenuta" if acceptance_done else ("Da ottenere" if acceptance_candidates else "N/D"),
    }
    variations = {
        "tone": "red" if uncovered_changes else "green",
        "label": f"{len(uncovered_changes)} aperte" if uncovered_changes else "Regolare",
    }

    checks = {
        "technical": technical,
        "documentation": documentation,
        "invoicing": invoicing,
        "payments": payments,
        "acceptance": acceptance,
        "variations": variations,
    }
    blockers = []
    if project.technical_status != "CLOSED":
        blockers.append("chiusura tecnica non completata")
    if blocking_docs:
        blockers.append("documentazione bloccante aperta")
    if unbilled:
        blockers.append("milestone completate non fatturate")
    if finance["overdue"] > 0:
        blockers.append("incassi scaduti ancora aperti")
    if uncovered_changes:
        blockers.append("extra/varianti non formalizzati")
    if acceptance_candidates and not acceptance_done:
        blockers.append("acceptance/SAT non completata")

    closeable = project.technical_status == "CLOSED" and not blockers
    return {
        "closeable": closeable,
        "label": "CHIUDIBILE" if closeable else "NON CHIUDIBILE",
        "tone": "green" if closeable else "red",
        "checks": checks,
        "blockers": blockers,
    }


def suggested_action(alert: Alert, project: Project, today: date) -> dict:
    pm = project.pm_owner if project.pm_owner != "N/D" else "Responsabile Tecnico"
    sales = project.sales_owner if project.sales_owner != "N/D" else "Commerciale"
    mapping = {
        "OVERDUE_INVOICE": ("Verificare incasso e confermare il prossimo follow-up", "Amministrazione", "VERIFY"),
        "UNBILLED_MILESTONE": ("Confermare la milestone e richiedere l'emissione della fattura", sales, "VERIFY"),
        "FORECAST_OVERRUN": ("Aggiornare ETC e definire un recovery plan sul budget", pm, "INTERVENTION"),
        "CONTROL_OVERCOMMIT": ("Verificare lo sforamento della VdA e gli ordini ancora aperti", pm, "VERIFY"),
        "CONTROL_BUDGET_POSITION": (
            "Verificare gli scostamenti locali e qualificare i residui come budget residuo, saving candidato o saving consolidato",
            pm,
            "VERIFY",
        ),
        "PROCUREMENT_MATURITY": (
            "Verificare le VdA procurement segnalate e confermare cosa manca realmente da acquistare",
            pm,
            "VERIFY",
        ),
        "CONFIDENCE_REVIEW": (
            "Avviare un ciclo interno di Project Confidence Review e recuperare le evidenze mancanti",
            "Responsabile Tecnico",
            "VERIFY",
        ),
        "SCHEDULE_DELAY": ("Aggiornare recovery plan e forecast della milestone", pm, "INTERVENTION"),
        "LD_EXPOSURE": ("Verificare posizione contrattuale e recovery plan", pm, "DECISION"),
        "OVERDUE_ACTION": ("Chiudere o ripianificare l'azione scaduta", pm, "INTERVENTION"),
        "DOCUMENT_BLOCKER": ("Definire data di rilascio della documentazione bloccante", pm, "INTERVENTION"),
        "TECHNICAL_ISSUE": ("Definire piano tecnico, owner e data di chiusura", pm, "INTERVENTION"),
        "UNCOVERED_CHANGE": (
            "Verificare se esiste un ordine/extra e aggiornare lo stato contrattuale",
            sales,
            "VERIFY",
        ),
        "COMMUNICATION_RISK": ("Rispondere al cliente e riallineare impegni e scadenze", pm, "INTERVENTION"),
        "AGENT_CUSTOMER_ESCALATION": (
            "Verificare il thread e rispondere al cliente riallineando impegni e prossima data",
            pm,
            "VERIFY",
        ),
        "AGENT_SCHEDULE_RISK": ("Verificare la nuova data e aggiornare il forecast solo dopo conferma", pm, "VERIFY"),
        "AGENT_PAYMENT_PROMISE": (
            "Verificare la promessa di pagamento e pianificare il follow-up sull'incasso",
            sales,
            "VERIFY",
        ),
        "AGENT_DOCUMENT_REQUEST": ("Confermare owner e data di rilascio della documentazione richiesta", pm, "VERIFY"),
        "AGENT_CHANGE_REQUEST": (
            "Verificare lo scope e formalizzare eventuale variante/offerta extra",
            sales,
            "VERIFY",
        ),
        "AGENT_TECHNICAL_RISK": ("Aprire verifica tecnica e definire risposta al cliente", pm, "VERIFY"),
    }
    text, owner, action_type = mapping.get(
        alert.alert_type, ("Verificare la criticità e definire la prossima azione", pm, "VERIFY")
    )
    days = 1 if alert.severity == "CRITICAL" else 3 if alert.severity == "HIGH" else 5
    priority = "BLOCKING" if alert.severity == "CRITICAL" else "HIGH" if alert.severity == "HIGH" else "NORMAL"
    return {
        "title": text,
        "owner": owner,
        "due_date": today + timedelta(days=days),
        "action_type": action_type,
        "priority": priority,
    }


def timeline(project: Project, today: date) -> list[dict]:
    events: list[dict] = []
    for m in project.milestones:
        if m.contract_date:
            events.append(
                {
                    "date": m.contract_date,
                    "kind": "CONTRACT",
                    "title": f"Data contrattuale · {m.name}",
                    "detail": "Milestone contrattuale",
                    "tone": "blue",
                }
            )
        if m.actual_date:
            events.append(
                {
                    "date": m.actual_date,
                    "kind": "MILESTONE",
                    "title": f"Completata · {m.name}",
                    "detail": "Milestone consuntivata",
                    "tone": "green",
                }
            )
        elif m.forecast_date:
            tone = "red" if m.contract_date and m.forecast_date > m.contract_date else "amber"
            events.append(
                {
                    "date": m.forecast_date,
                    "kind": "FORECAST",
                    "title": f"Forecast · {m.name}",
                    "detail": "Data prevista",
                    "tone": tone,
                }
            )
    for inv in project.invoices:
        events.append(
            {
                "date": inv.issue_date,
                "kind": "INVOICE",
                "title": f"Fattura {inv.number}",
                "detail": f"€ {inv.amount:,.0f}",
                "tone": "blue",
            }
        )
        if inv.due_date < today and inv.paid_amount < inv.amount:
            events.append(
                {
                    "date": inv.due_date,
                    "kind": "PAYMENT",
                    "title": f"Scadenza {inv.number}",
                    "detail": f"Aperto € {inv.amount - inv.paid_amount:,.0f}",
                    "tone": "red",
                }
            )
    for a in project.actions:
        if a.due_date:
            tone = "red" if a.status not in ("CLOSED", "RESOLVED") and a.due_date < today else "amber"
            events.append(
                {
                    "date": a.due_date,
                    "kind": "ACTION",
                    "title": a.title,
                    "detail": f"Owner {a.owner} · {a.status}",
                    "tone": tone,
                }
            )
    for c in project.communications:
        events.append(
            {
                "date": c.date,
                "kind": "MAIL",
                "title": c.subject,
                "detail": f"{c.direction} · {c.sender}",
                "tone": "red" if not c.responded else "blue",
            }
        )
    for o in getattr(project, "customer_orders", []):
        kind = "PO EXTRA" if o.order_kind == "EXTRA" else "PO CLIENTE"
        events.append(
            {
                "date": o.order_date,
                "kind": kind,
                "title": o.order_number,
                "detail": f"€ {o.net_value:,.0f} netti · {o.quote_ref or 'riferimento offerta N/D'}",
                "tone": "green" if o.order_kind == "EXTRA" else "blue",
            }
        )
    for c in project.changes:
        events.append(
            {
                "date": c.requested_date,
                "kind": "CHANGE",
                "title": "Richiesta extra / variante",
                "detail": c.description,
                "tone": "red" if not c.order_received else "green",
            }
        )
    for i in project.issues:
        if i.due_date:
            events.append(
                {
                    "date": i.due_date,
                    "kind": "ISSUE",
                    "title": i.title,
                    "detail": f"{i.category} · {i.severity}",
                    "tone": "red" if i.status == "OPEN" else "green",
                }
            )
    # Only AI findings explicitly applied to the project enter the executive timeline.
    # NEW/VALIDATED findings remain inside the operational workspace until a user receives them.
    for f in project.agent_findings:
        if f.status != "APPLIED":
            continue
        event_date = f.extracted_date or (f.communication.date if f.communication else today)
        events.append(
            {
                "date": event_date,
                "kind": "AI RECEPITO",
                "title": f.title,
                "detail": f.applied_summary or f"Recepito · confidence {f.confidence:.0%}",
                "tone": "blue",
            }
        )

    control = control_summary(project)
    if control:
        events.append(
            {
                "date": control["captured_at"].date(),
                "kind": "CONTROL",
                "title": "Snapshot controllo economico",
                "detail": f"Budget € {control['operational_budget']:,.0f} · assorbito/impegnato € {control['absorbed_committed']:,.0f}",
                "tone": "amber" if control["budget_health"]["tone"] == "amber" else control["budget_health"]["tone"],
            }
        )

    events.sort(key=lambda e: (e["date"], e["kind"]))
    return events
