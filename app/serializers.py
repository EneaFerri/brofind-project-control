from datetime import date

from .rules import budget_summary, finance_summary, project_health, attention_score, is_data_acquisition
from .workflow import application_preview
from .control import control_summary
from .confidence import confidence_summary
from .source_center import source_summary
from .ai_analysis import FIELD_LABELS, analysis_insights
from .analytics import (
    closing_summary,
    project_exposure,
    priority_summary,
    suggested_action,
    timeline,
    DIMENSION_LABELS,
    STATUS_LABELS,
)


def _phase_summary(p, control):
    mapping = {
        "ENGINEERING": ("Engineering", "Definizione tecnica e documentazione"),
        "PROCUREMENT": ("Procurement", "Acquisti e forniture"),
        "EXECUTION": ("In costruzione", "Costruzione / procurement in corso"),
        "DELIVERY": ("In consegna", "Preparazione e spedizione"),
        "INSTALLATION": ("In installazione", "Montaggio in sito"),
        "COMMISSIONING": ("Commissioning", "Avviamento e performance test"),
        "CLOSING": ("Closing", "Chiusura tecnica/economica"),
    }
    label, detail = mapping.get(p.status, (p.status.replace("_", " ").title(), "Fase da classificare"))
    if p.status == "EXECUTION" and getattr(p, "delivery_window", "UNKNOWN") in ("NEAR", "IMMINENT"):
        detail = "Costruzione in corso · consegna prossima"
    procurement = control.get("procurement") if control else None
    progress = None
    if procurement:
        progress = f"{procurement['closed_count']} concluse · {procurement['not_started_count']} non avviate · {procurement['open_or_unknown_count']} da chiudere"
    return {"label": label, "detail": detail, "procurement_progress": progress}


def _health_recaps(p, health):
    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    aliases = {
        "FINANCE": {"FINANCE"},
        "BUDGET": {"BUDGET"},
        "TECHNICAL": {"TECHNICAL", "PROJECT", "COMMUNICATION"},
        "SCHEDULE": {"SCHEDULE"},
        "CONTRACT": {"CONTRACT", "COMMERCIAL"},
    }
    active = [a for a in p.alerts if a.status in ("OPEN", "ACKNOWLEDGED")]
    out = {}
    for dim, state in health.items():
        candidates = sorted([a for a in active if a.dimension in aliases.get(dim, {dim})], key=lambda a: severity_rank.get(a.severity, 9))
        if candidates:
            a = candidates[0]
            desc = (a.description or "").strip().replace("\n", " ")
            first = desc.split(".")[0].strip()
            if len(first) > 92:
                first = first[:89].rstrip() + "…"
            out[dim] = a.title if not first else f"{a.title}\n{first}."
        elif state in ("ND", "PARTIAL"):
            out[dim] = "Dati insufficienti o valutazione non completa per questo dominio."
        else:
            out[dim] = "Nessuna anomalia deterministica aperta nel dominio."
    return out


def _contract_baseline(p, control):
    orders = control.get("contract", {}).get("orders", []) if control else []
    net = (control.get("contract", {}).get("net_total") or p.order_value) if control else p.order_value
    complete = bool(orders) and all(o.get("document_status") == "COMPLETE" for o in orders)
    decisions = {
        d.decision_key: d for d in getattr(p, "cockpit_decisions", [])
        if d.decision_type == "CONTRACT_CONDITION" and d.status != "REVOKED"
    }

    def editable_condition(key, name, default_value, note):
        d = decisions.get(key)
        if d and d.status == "FROZEN":
            return {
                "key": key, "name": name, "value": d.value or default_value, "status": "FROZEN",
                "note": d.note or note, "source_ref": d.source_ref, "editable": True,
                "validated_by": d.created_by, "validated_at": d.updated_at,
            }
        return {
            "key": key, "name": name, "value": (d.value if d and d.value else default_value),
            "status": "TO_CLARIFY", "note": (d.note if d and d.note else note),
            "source_ref": d.source_ref if d else None, "editable": True,
            "validated_by": d.created_by if d else None, "validated_at": d.updated_at if d else None,
        }

    conditions = [
        {"key": "contract_package", "name": "Pacchetto contrattuale", "value": "Completo" if complete else "Da completare", "status": "FROZEN" if complete else "OPEN", "note": "PO/Agreement + clarification table + CGA + offerta acquisiti.", "source_ref": "contract:PO-PILOT-001", "editable": False, "validated_by": None, "validated_at": None},
        {"key": "order_value", "name": "Valore ordini cliente", "value": f"€ {net:,.0f}" if net else "N/D", "status": "FROZEN" if net else "OPEN", "note": "PO base + extra formalizzati, valori netti.", "source_ref": "contract:orders", "editable": False, "validated_by": None, "validated_at": None},
    ]
    if p.code == "9028":
        conditions += [
            editable_condition("effective_date", "Data di efficacia", "Da congelare", "Distinguere data Agreement/PO e revisione successiva."),
            editable_condition("delivery_date", "Data consegna contrattuale", "Da congelare", "La data planning corrente non è ancora strutturata come fonte autorevole."),
            editable_condition("payment_terms", "Termini di pagamento", "Da chiarire", "Nel dossier esistono formulazioni differenti: serve chiarimento e freeze della condizione applicabile."),
            editable_condition("incoterm", "Incoterm / consegna", "Da chiarire", "Fonti contrattuali e offerta non sono ancora congelate in una Contract Baseline unica."),
            editable_condition("penalties", "Penali / milestone", "Da estrarre e congelare", "Le condizioni vanno tradotte in milestone operative validate, non inferite automaticamente."),
        ]

    reviewed_condition_names = {
        "order_number": "Numero ordine / contratto",
        "order_date": "Data ordine",
        "currency": "Valuta",
        "payment_terms": "Termini di pagamento",
        "contractual_delivery_date": "Data consegna contrattuale",
        "penalties": "Penali per ritardo",
        "penalty_cap": "Cap penali",
        "incoterm": "Incoterm / consegna",
        "warranty": "Garanzia",
        "milestone_order_ack": "Milestone Order acknowledgement",
        "milestone_fat": "Milestone FAT",
        "milestone_delivery": "Milestone Delivery",
        "milestone_sat_take_over": "Milestone SAT / Take Over",
    }
    existing_keys = {item["key"] for item in conditions}
    for key, name in reviewed_condition_names.items():
        if key in existing_keys:
            continue
        decision = decisions.get(key)
        if decision and decision.status == "FROZEN":
            conditions.append({
                "key": key, "name": name, "value": decision.value or "N/D", "status": "FROZEN",
                "note": decision.note or "Dato revisionato e confermato.", "source_ref": decision.source_ref,
                "editable": True, "validated_by": decision.created_by, "validated_at": decision.updated_at,
            })

    dismissed_requirements = {
        d.decision_key for d in getattr(p, "cockpit_decisions", [])
        if d.decision_type == "REQUIREMENT_DISPOSITION" and d.status == "ACTIVE" and (d.value or "").upper() == "DISMISSED"
    }
    pending_scope = [r for r in p.requirements if r.status == "TO_VERIFY" and r.requirement_key not in dismissed_requirements]
    potential_changes = []
    for r in pending_scope:
        f = next((x for x in p.agent_findings if x.source_ref and x.source_ref == r.source_ref and x.status not in ("DISMISSED", "APPLIED")), None)
        potential_changes.append({
            "requirement_id": r.id, "requirement_key": r.requirement_key, "title": r.title,
            "vda_code": r.vda_code, "source_kind": r.source_kind, "source_ref": r.source_ref,
            "note": r.note, "finding_id": f.id if f else None,
            "finding_status": f.status if f else None, "finding_summary": f.summary if f else None,
        })
    return {
        "documentation_complete": complete,
        "conditions": conditions,
        "frozen_count": sum(1 for c in conditions if c["status"] == "FROZEN"),
        "clarify_count": sum(1 for c in conditions if c["status"] == "TO_CLARIFY"),
        "potential_change_count": len(potential_changes),
        "potential_changes": potential_changes,
        "formalized_change_count": sum(1 for c in p.changes if c.order_received),
    }


def _action_escalation(a, today):
    if not a.due_date or a.status in ("CLOSED", "RESOLVED") or a.due_date >= today:
        return {"active": False, "level": 0, "target": None, "label": "Nessuna escalation"}
    days = (today - a.due_date).days
    if days >= 7 or a.priority == "BLOCKING":
        return {"active": True, "level": 2, "target": "Direzione", "label": f"Escalation Direzione · scaduta da {days} gg"}
    if days >= 3 or a.priority == "HIGH":
        target = "Responsabile reparto" if a.owner_kind == "USER" else "Responsabile del reparto assegnato"
        return {"active": True, "level": 1, "target": target, "label": f"Escalation reparto · scaduta da {days} gg"}
    return {"active": True, "level": 0, "target": a.owner, "label": f"Reminder scadenza · {days} gg"}


def _linked_action(p, alert_id):
    marker = f"ALERT:{alert_id}"
    return next((a for a in p.actions if a.source == marker and a.status not in ("CLOSED", "RESOLVED")), None)


def _primary_attention(p, today: date):
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    alerts = [a for a in p.alerts if a.status in ("OPEN", "ACKNOWLEDGED")]
    alerts.sort(key=lambda a: (severity_order.get(a.severity, 9), a.id or 0))
    if alerts:
        alert = alerts[0]
        linked = _linked_action(p, alert.id)
        next_step = linked.title if linked else suggested_action(alert, p, today)["title"]
        owner = linked.owner if linked else suggested_action(alert, p, today)["owner"]
        due_date = linked.due_date if linked else suggested_action(alert, p, today)["due_date"]
        return {
            "title": alert.title,
            "dimension": DIMENSION_LABELS.get(alert.dimension, alert.dimension.title()),
            "next_step": next_step,
            "owner": owner,
            "due_date": due_date,
            "has_alert": True,
        }
    open_actions = [a for a in p.actions if a.status not in ("CLOSED", "RESOLVED")]
    open_actions.sort(key=lambda a: (a.due_date or date.max, a.id or 0))
    if open_actions:
        action = open_actions[0]
        return {
            "title": "Attività aperta",
            "dimension": "Operatività",
            "next_step": action.title,
            "owner": action.owner,
            "due_date": action.due_date,
            "has_alert": False,
        }
    return {
        "title": "Nessun punto prioritario",
        "dimension": "Stato",
        "next_step": "Proseguire con il normale monitoraggio",
        "owner": p.pm_owner,
        "due_date": None,
        "has_alert": False,
    }


def _extracted_display_value(field_key, value):
    if field_key == "contract_value":
        try:
            return f"€ {float(value):,.0f}"
        except (TypeError, ValueError):
            return value
    if field_key in {"order_date", "contractual_delivery_date"}:
        try:
            return date.fromisoformat(value).strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return value
    return value


def _extracted_field_rows(p):
    rows = []
    for field in sorted(getattr(p, "extracted_fields", []), key=lambda item: (item.id or 0)):
        status = field.review_status
        if status in ("CONFIRMED", "CORRECTED") and field.operational_value is not None:
            provenance = "OPERATIONAL"
        elif status in ("CONFIRMED", "CORRECTED", "TO_VERIFY"):
            provenance = "REVIEWED"
        else:
            provenance = "EXTRACTED"
        content = field.source_content
        chain = ["SOURCE", "EXTRACTED"]
        if status in ("CONFIRMED", "CORRECTED", "TO_VERIFY"):
            chain.append("REVIEWED")
        if field.operational_value is not None:
            chain.append("OPERATIONAL")
        rows.append({
            "id": field.id,
            "source_content_id": field.source_content_id,
            "source_file_name": content.source_file.file_name if content and content.source_file else "",
            "field_key": field.field_key,
            "field_label": FIELD_LABELS.get(field.field_key, field.field_key.replace("_", " ").title()),
            "extracted_value": field.extracted_value,
            "display_value": _extracted_display_value(field.field_key, field.extracted_value),
            "confidence": field.confidence,
            "confidence_pct": int(round(field.confidence * 100)),
            "review_status": status,
            "corrected_value": field.corrected_value,
            "operational_value": field.operational_value,
            "source_ref": field.source_ref,
            "provenance": provenance,
            "provenance_chain": chain,
        })
    return rows


def _extracted_field_summary(project, rows):
    source_types = {
        field.source_content.source_file.source_type
        for field in getattr(project, "extracted_fields", [])
        if field.source_content and field.source_content.source_file
    }
    source_types.update(
        item.source_type for item in getattr(project, "source_imports", []) if item.status == "SUCCESS"
    )
    # The UI recap reports connected evidence streams, not only text fields.
    # This keeps Galileo visible alongside Documenti and Outlook once the source
    # has been discovered in the Source Center.
    source_types.update(
        item.source_type for item in getattr(project, "source_files", []) if item.is_present
    )
    return {
        "sources_analyzed": len(source_types),
        "found": len(rows),
        "confirmed": sum(1 for row in rows if row["review_status"] in ("CONFIRMED", "CORRECTED")),
        "to_verify": sum(1 for row in rows if row["review_status"] == "TO_VERIFY"),
    }
def project_card(p, today: date):
    acquisition_data = is_data_acquisition(p)
    health = project_health(p)
    control = control_summary(p)
    confidence = confidence_summary(p, today)
    priority = priority_summary(p)
    commercial_data_pending = p.customer == "__PENDING__"
    return {
        "code": p.code,
        "customer": "Da acquisire" if commercial_data_pending else p.customer,
        "sales_owner": p.sales_owner,
        "pm_owner": p.pm_owner,
        "order_value": p.order_value,
        "status": p.status,
        "is_data_acquisition": acquisition_data,
        "has_economic_data": bool(control),
        "commercial_data_pending": commercial_data_pending,
        "contract_value_known": not commercial_data_pending and p.order_value > 0,
        "technical_status": p.technical_status,
        "country": p.country,
        "sources": source_summary(p),
        "source_contents": [{"source_type": item.source_file.source_type, "file_name": item.source_file.file_name, "content_type": item.content_type, "content_kind": item.content_kind, "extracted_at": item.extracted_at} for item in p.source_contents],
        "extracted_fields": _extracted_field_rows(p),
        "extracted_summary": _extracted_field_summary(p, _extracted_field_rows(p)),
        "health": health,
        "health_labels": {k: STATUS_LABELS[v] for k, v in health.items()},
        "health_recap": _health_recaps(p, health),
        "dimension_labels": DIMENSION_LABELS,
        "attention": attention_score(p),
        "priority": priority,
        "primary_attention": _primary_attention(p, today),
        "phase": _phase_summary(p, control),
        "confidence": confidence,
        "finance": finance_summary(p, today),
        "budget": budget_summary(p),
        "control": control,
        "exposure": project_exposure(p, today),
        "open_alerts": sum(1 for a in p.alerts if a.status in ("OPEN", "ACKNOWLEDGED")),
        "open_actions": sum(1 for a in p.actions if a.status not in ("CLOSED", "RESOLVED")),
        "ai_findings_new": sum(1 for f in p.agent_findings if f.status == "NEW"),
        "ai_findings_validated": sum(1 for f in p.agent_findings if f.status == "VALIDATED"),
        "ai_findings_applied": sum(1 for f in p.agent_findings if f.status == "APPLIED"),
    }


def _alert_summary_lines(alert, control, confidence):
    if alert.alert_type == "CONTROL_BUDGET_POSITION" and control:
        overruns = []
        for r in control.get("vda_rows", []):
            delta = r["committed_cost"] - r["operational_budget"]
            if delta > 0.01:
                overruns.append((delta, r["vda_name"]))
        overruns.sort(reverse=True)
        top = " · ".join(f"{name} +€{amount:,.0f}" for amount, name in overruns[:3])
        return [
            ("Sforamenti locali", f"€{control['budget_health']['gross_overrun']:,.0f}"),
            ("Saving candidato", f"€{control['saving']['candidate']:,.0f}"),
            ("Principali scostamenti", top or "Nessuno"),
        ]
    if alert.alert_type == "PROCUREMENT_MATURITY" and control:
        p = control["procurement"]
        top = " · ".join(f"{x['vda_name']} €{x['budget']:,.0f}" for x in p.get("top_watch", [])[:3])
        return [
            ("Senza ordini", f"{p['not_started_count']} VdA"),
            ("Chiusura da verificare", f"{p['open_or_unknown_count']} VdA"),
            ("Priorità", top or "Nessuna"),
        ]
    if alert.alert_type == "CONFIDENCE_REVIEW" and confidence:
        review = confidence.get("review_domains", [])
        labels = " · ".join(f"{x['label']}: {x['level_label']}" for x in review[:3])
        return [
            ("Affidabilità complessiva", confidence["overall"]["level_label"]),
            ("Domini da recuperare", labels or "Nessuno"),
            ("Aree da migliorare", str(confidence.get("improvement_count", confidence.get("gap_count", 0)))),
        ]
    desc = (alert.description or "").strip().replace("\n", " ")
    parts = [x.strip() for x in desc.split(".") if x.strip()]
    return [("Sintesi", x + ".") for x in parts[:2]]


def project_detail(p, today: date):
    d = project_card(p, today)
    d["contract_baseline"] = _contract_baseline(p, d.get("control"))
    d["ai_analysis"] = analysis_insights(p, today)
    alert_rows = []
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    for a in sorted(p.alerts, key=lambda x: severity_order.get(x.severity, 4)):
        if a.status not in ("OPEN", "ACKNOWLEDGED"):
            continue
        suggested = suggested_action(a, p, today)
        linked = _linked_action(p, a.id)
        alert_rows.append({
            "id": a.id,
            "type": a.alert_type,
            "dimension": a.dimension,
            "dimension_label": DIMENSION_LABELS.get(a.dimension, {"PROJECT":"Project","COMMUNICATION":"Comunicazione","COMMERCIAL":"Commerciale","PROCUREMENT":"Acquisti"}.get(a.dimension, a.dimension.title())),
            "severity": a.severity,
            "severity_label": {"CRITICAL":"Critica","HIGH":"Alta","MEDIUM":"Da presidiare","LOW":"Bassa"}.get(a.severity, a.severity),
            "title": a.title,
            "description": a.description,
            "summary_lines": _alert_summary_lines(a, d.get("control"), d.get("confidence")),
            "status": a.status,
            "source_kind": a.source_kind,
            "source_ref": a.source_ref,
            "confidence": a.confidence,
            "data_status": a.data_status,
            "suggested_action": suggested,
            "linked_action": {"id": linked.id, "title": linked.title, "owner": linked.owner, "due_date": linked.due_date, "status": linked.status} if linked else None,
        })
    d.update({
        "description": p.description,
        "milestones": [{"id": m.id, "name": m.name, "contract_date": m.contract_date, "forecast_date": m.forecast_date, "actual_date": m.actual_date, "invoice_value": m.invoice_value, "invoice_required": m.invoice_required, "ld_applicable": m.ld_applicable, "ld_rate_weekly_pct": m.ld_rate_weekly_pct} for m in p.milestones],
        "budget_lines": [{"category": b.category, "budget": b.budget, "actual": b.actual, "committed": b.committed, "etc": b.etc, "forecast": b.actual+b.committed+b.etc, "variance": (b.actual+b.committed+b.etc)-b.budget, "etc_source": b.etc_source} for b in p.budget_lines],
        "invoices": [{"number": i.number, "milestone": i.milestone_name, "issue_date": i.issue_date, "due_date": i.due_date, "amount": i.amount, "paid_amount": i.paid_amount, "open_amount": max(i.amount-i.paid_amount,0), "overdue": i.due_date < today and i.paid_amount < i.amount} for i in p.invoices],
        "actions": [{"id": a.id, "title": a.title, "owner": a.owner, "owner_kind": a.owner_kind, "requester": a.requester, "action_type": a.action_type, "priority": a.priority, "due_date": a.due_date, "status": a.status, "source": a.source, "response_summary": a.response_summary, "validated_by": a.validated_by, "validated_at": a.validated_at, "overdue": bool(a.due_date and a.due_date < today and a.status not in ("CLOSED", "RESOLVED")), "escalation": _action_escalation(a, today), "messages": [{"id": m.id, "author": m.author, "body": m.body, "source": m.source, "created_at": m.created_at} for m in sorted(a.messages, key=lambda x: x.created_at)]} for a in p.actions],
        "issues": [{"id": i.id, "category": i.category, "title": i.title, "severity": i.severity, "status": i.status, "blocking": i.blocking, "due_date": i.due_date, "source_ref": i.source_ref} for i in p.issues],
        "changes": [{"id": c.id, "description": c.description, "requested_date": c.requested_date, "estimated_cost": c.estimated_cost, "quoted_value": c.quoted_value, "order_received": c.order_received, "work_started": c.work_started, "source_ref": c.source_ref} for c in p.changes],
        "customer_orders": [{"number": o.order_number, "date": o.order_date, "kind": o.order_kind, "quote_ref": o.quote_ref, "net_value": o.net_value, "tax_value": o.tax_value, "gross_value": o.gross_value, "currency": o.currency, "payment_terms": o.payment_terms, "incoterm": o.incoterm, "scope_summary": o.scope_summary, "source_ref": o.source_ref, "note": o.note, "document_status": o.document_status, "document_note": o.document_note} for o in sorted(p.customer_orders, key=lambda x: x.order_date)],
        "requirements": [{"id": r.id, "key": r.requirement_key, "title": r.title, "vda_code": r.vda_code, "status": r.status, "source_kind": r.source_kind, "source_ref": r.source_ref, "source_date": r.source_date, "quantity": r.quantity, "procurement_mode": r.procurement_mode, "confidence": r.confidence, "note": r.note} for r in sorted(p.requirements, key=lambda x: (x.vda_code or "", x.id or 0))],
        "delivery_window": p.delivery_window,
        "delivery_context": p.delivery_context,
        "communications": [{"id": c.id, "date": c.date, "direction": c.direction, "sender": c.sender, "recipient": c.recipient, "subject": c.subject, "body": c.body, "topic": c.topic, "responded": c.responded, "reminders_count": c.reminders_count, "promised_date": c.promised_date, "source_ref": c.source_ref} for c in sorted(p.communications, key=lambda x: x.date, reverse=True)],
        "findings": [{
            "id": f.id, "type": f.finding_type, "dimension": f.dimension, "severity": f.severity,
            "title": f.title, "summary": f.summary, "evidence": f.evidence,
            "extracted_date": f.extracted_date, "extracted_amount": f.extracted_amount,
            "suggested_action": f.suggested_action, "suggested_owner": f.suggested_owner,
            "confidence": f.confidence, "status": f.status, "status_label": {"NEW":"Da verificare","VALIDATED":"Confermato","APPLIED":"Registrato","DISMISSED":"Scartato"}.get(f.status, f.status), "source_ref": f.source_ref,
            "communication_id": f.communication_id,
            "communication_subject": f.communication.subject if f.communication else None,
            "communication_date": f.communication.date if f.communication else None,
            "application": application_preview(f, p) if f.status == "VALIDATED" else None,
            "applied_kind": f.applied_kind, "applied_ref": f.applied_ref,
            "applied_summary": f.applied_summary, "applied_at": f.applied_at,
        } for f in sorted(p.agent_findings, key=lambda x: ({"NEW":0,"VALIDATED":1,"APPLIED":2,"DISMISSED":3}.get(x.status, 4), -x.confidence, x.id))],
        "agent_runs": [{
            "id": r.id, "engine": r.engine, "status": r.status, "messages": r.messages_analyzed,
            "created": r.findings_created, "updated": r.findings_updated, "completed_at": r.completed_at,
        } for r in sorted(p.agent_runs, key=lambda x: x.id, reverse=True)[:5]],
        "intelligence": {
            "new": sum(1 for f in p.agent_findings if f.status == "NEW"),
            "validated": sum(1 for f in p.agent_findings if f.status == "VALIDATED"),
            "dismissed": sum(1 for f in p.agent_findings if f.status == "DISMISSED"),
            "applied": sum(1 for f in p.agent_findings if f.status == "APPLIED"),
            "messages": len(p.communications),
            "last_run": max((r.completed_at for r in p.agent_runs), default=None),
        },
        "alerts": alert_rows,
        "procurement_alert_id": next((a["id"] for a in alert_rows if a["type"] == "PROCUREMENT_MATURITY"), None),
        "confidence_alert_id": next((a["id"] for a in alert_rows if a["type"] == "CONFIDENCE_REVIEW"), None),
        "closing": closing_summary(p, today),
        "timeline": timeline(p, today),
    })
    return d
