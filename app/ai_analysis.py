from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Iterable

from sqlalchemy.orm import Session

from .models import CockpitDecision, CustomerOrder, Project, ProjectExtractedField, ProjectSourceContent
from .control import control_summary
from .rules import finance_summary


FIELD_LABELS = {
    "customer_name": "Cliente",
    "order_number": "Numero ordine / contratto",
    "order_date": "Data ordine",
    "contract_value": "Valore contratto",
    "currency": "Valuta",
    "payment_terms": "Condizioni di pagamento",
    "milestone_order_ack": "Milestone · Order acknowledgement",
    "milestone_fat": "Milestone · FAT",
    "milestone_delivery": "Milestone · Delivery",
    "milestone_sat_take_over": "Milestone · SAT / Take Over",
    "contractual_delivery_date": "Data consegna contrattuale",
    "penalties": "Penali per ritardo",
    "penalty_cap": "Cap penali",
    "incoterm": "Incoterm",
    "warranty": "Garanzia",
    "payment_update": "Aggiornamento pagamento da email",
}

CONTRACT_DECISION_KEYS = {
    "order_number",
    "order_date",
    "currency",
    "payment_terms",
    "contractual_delivery_date",
    "penalties",
    "penalty_cap",
    "incoterm",
    "warranty",
    "milestone_order_ack",
    "milestone_fat",
    "milestone_delivery",
    "milestone_sat_take_over",
}

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _english_date_to_iso(value: str) -> str:
    match = re.fullmatch(r"\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*", value or "")
    if not match:
        return _clean(value)
    month = MONTHS.get(match.group(2).lower())
    if not month:
        return _clean(value)
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _money(value: str) -> float:
    cleaned = re.sub(r"[^0-9,.-]", "", value or "").replace(",", "")
    return float(cleaned)


def _extract_contract_fields(text: str) -> list[tuple[str, str, float]]:
    fields: list[tuple[str, str, float]] = []

    def add(pattern: str, key: str, confidence: float = 0.96, flags: int = re.I, transform=None):
        match = re.search(pattern, text, flags)
        if match:
            value = _clean(match.group(1))
            if transform:
                value = transform(value)
            if value:
                fields.append((key, value, confidence))

    add(r"^Customer:\s*(.+)$", "customer_name", 0.99, re.I | re.M)
    add(r"^Purchase order number:\s*(.+)$", "order_number", 0.99, re.I | re.M)
    add(r"^Order date:\s*(.+)$", "order_date", 0.99, re.I | re.M, _english_date_to_iso)
    match = re.search(r"total net contract value is\s+([A-Z]{3})\s+([\d,.]+)", text, re.I)
    if match:
        fields.append(("contract_value", f"{_money(match.group(2)):.2f}", 0.99))
        fields.append(("currency", match.group(1).upper(), 0.99))
    else:
        add(r"^Currency:\s*([A-Z]{3})", "currency", 0.98, re.I | re.M)
    add(r"PAYMENT TERMS\s+(.+?)(?=\n\s*CONTRACTUAL AND BILLING MILESTONES)", "payment_terms", 0.97, re.I | re.S)

    milestone_patterns = [
        ("milestone_order_ack", r"1\.\s*Order acknowledgement\s*-\s*(.+?)\.?\s*$"),
        ("milestone_fat", r"2\.\s*Factory Acceptance Test \(FAT\)\s*-\s*(.+?)\.?\s*$"),
        ("milestone_delivery", r"3\.\s*Delivery\s*-\s*(.+?)\.?\s*$"),
        ("milestone_sat_take_over", r"4\.\s*Site Acceptance Test \(SAT\) and Take Over\s*-\s*(.+?)\.?\s*$"),
    ]
    for key, pattern in milestone_patterns:
        add(pattern, key, 0.96, re.I | re.M)

    add(r"Contractual delivery date:\s*(.+?)\.?\s*$", "contractual_delivery_date", 0.98, re.I | re.M, _english_date_to_iso)
    add(r"penalty equal to\s*(.+?)\.\s*The aggregate penalty cap", "penalties", 0.95, re.I | re.S)
    add(r"aggregate penalty cap is\s*([^\.]+(?:%[^\.]*)?)\.", "penalty_cap", 0.72, re.I | re.S)
    add(r"Delivery term:\s*(.+?)\.\s*$", "incoterm", 0.96, re.I | re.M)
    add(r"Warranty:\s*(.+?)\.\s*$", "warranty", 0.95, re.I | re.M)
    return fields


def _extract_email_fields(content: ProjectSourceContent) -> list[tuple[str, str, float]]:
    try:
        metadata = json.loads(content.metadata_json or "{}")
    except json.JSONDecodeError:
        metadata = {}
    subject = _clean(str(metadata.get("subject") or ""))
    body = _clean(content.extracted_text)
    sample = f"{subject} {body}"
    if not re.search(r"\b(payment|paid|invoice|incasso|pagamento|fattura)\b", sample, re.I):
        return []
    sender = _clean(str(metadata.get("sender") or ""))
    value = f"{subject or 'Email pagamento'}"
    if sender:
        value += f" · {sender}"
    if body:
        value += f" · {body[:500]}"
    return [("payment_update", value, 0.78)]


def _upsert_field(db: Session, project: Project, content: ProjectSourceContent, key: str, value: str, confidence: float) -> tuple[ProjectExtractedField, bool]:
    field = db.query(ProjectExtractedField).filter_by(
        project_id=project.id,
        source_content_id=content.id,
        field_key=key,
    ).one_or_none()
    source_ref = f"source_content:{content.id}:{key}"
    if field is None:
        field = ProjectExtractedField(
            project_id=project.id,
            source_content_id=content.id,
            field_key=key,
            extracted_value=value,
            confidence=confidence,
            source_ref=source_ref,
        )
        db.add(field)
        return field, True
    if field.extracted_value != value:
        field.extracted_value = value
        field.confidence = confidence
        field.source_ref = source_ref
        field.review_status = "NEW"
        field.corrected_value = None
        field.operational_value = None
    else:
        field.confidence = confidence
        field.source_ref = source_ref
    return field, False


def analyze_project_sources(project: Project, db: Session) -> dict:
    created = 0
    touched = 0
    analyzed_sources = 0
    for content in sorted(project.source_contents, key=lambda item: item.id or 0):
        extracted: Iterable[tuple[str, str, float]] = []
        if content.content_kind == "DOCUMENT" and content.content_type in {"CONTRACT", "CUSTOMER_ORDER"}:
            extracted = _extract_contract_fields(content.extracted_text)
        elif content.content_kind == "EMAIL":
            extracted = _extract_email_fields(content)
        else:
            continue
        extracted = list(extracted)
        if not extracted:
            continue
        analyzed_sources += 1
        for key, value, confidence in extracted:
            _, was_created = _upsert_field(db, project, content, key, value, confidence)
            created += int(was_created)
            touched += 1
    db.commit()
    return {"sources": analyzed_sources, "fields": touched, "created": created}


def _decision_upsert(db: Session, project: Project, key: str, value: str, source_ref: str | None, created_by: str | None) -> CockpitDecision:
    decision = db.query(CockpitDecision).filter_by(
        project_id=project.id,
        decision_type="CONTRACT_CONDITION",
        decision_key=key,
    ).one_or_none()
    if decision is None:
        decision = CockpitDecision(project_id=project.id, decision_type="CONTRACT_CONDITION", decision_key=key)
        db.add(decision)
    decision.value = value
    decision.status = "FROZEN"
    decision.note = "Dato confermato tramite Analisi AI e review umana."
    decision.source_ref = source_ref
    decision.created_by = created_by
    return decision


def _operational_values(project: Project) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in project.extracted_fields:
        if field.review_status in {"CONFIRMED", "CORRECTED"} and field.operational_value:
            values[field.field_key] = field.operational_value
    return values


def _sync_customer_order(project: Project, db: Session) -> None:
    values = _operational_values(project)
    required = {"order_number", "order_date", "contract_value", "currency", "payment_terms"}
    if not required.issubset(values):
        return
    try:
        order_date = date.fromisoformat(values["order_date"])
        amount = float(values["contract_value"])
    except (TypeError, ValueError):
        return
    order = db.query(CustomerOrder).filter_by(project_id=project.id, order_number=values["order_number"]).one_or_none()
    if order is None:
        order = CustomerOrder(project_id=project.id, order_number=values["order_number"], order_date=order_date)
        db.add(order)
    order.order_date = order_date
    order.order_kind = "BASE"
    order.net_value = amount
    order.tax_value = 0
    order.gross_value = amount
    order.currency = values["currency"]
    order.payment_terms = values["payment_terms"]
    order.incoterm = values.get("incoterm")
    order.source_ref = "ai-review:contract"
    order.document_status = "RECEIVED"
    order.document_note = "Documento acquisito e campi principali revisionati; verifica contrattuale completa ancora in corso."


def apply_reviewed_field(field: ProjectExtractedField, db: Session, created_by: str | None = None) -> None:
    if field.review_status not in {"CONFIRMED", "CORRECTED"} or not field.operational_value:
        return
    project = field.project
    value = field.operational_value.strip()
    if field.field_key == "customer_name":
        project.customer = value
    elif field.field_key == "contract_value":
        try:
            project.order_value = float(value)
        except ValueError:
            return
    if field.field_key in CONTRACT_DECISION_KEYS:
        _decision_upsert(db, project, field.field_key, value, field.source_ref, created_by)
    _sync_customer_order(project, db)


def _email_signal(project: Project) -> dict | None:
    for content in sorted(project.source_contents, key=lambda item: item.id or 0, reverse=True):
        if content.content_kind != "EMAIL":
            continue
        text = _clean(content.extracted_text)
        try:
            metadata = json.loads(content.metadata_json or "{}")
        except json.JSONDecodeError:
            metadata = {}
        subject = _clean(str(metadata.get("subject") or ""))
        if re.search(r"\b(payment|paid|invoice|incasso|pagamento|fattura)\b", f"{subject} {text}", re.I):
            return {
                "kind": "OUTLOOK",
                "title": "Email collegata al pagamento rilevata",
                "detail": subject or text[:180],
                "action": "Confrontare la comunicazione con lo stato della fattura e verificare il follow-up.",
            }
    return None


def analysis_insights(project: Project, today: date) -> dict:
    control = control_summary(project)
    finance = finance_summary(project, today)
    findings: list[dict] = []
    suggestions: list[str] = []
    if control and control.get("budget_health", {}).get("gross_overrun", 0) > 0:
        amount = control["budget_health"]["gross_overrun"]
        findings.append({"kind": "GALILEO", "title": "Sforamento economico rilevato", "detail": f"Sforamenti locali complessivi € {amount:,.0f}."})
        suggestions.append("Verificare le VdA in sforamento e la copertura residua del budget.")
    if finance.get("overdue", 0) > 0:
        findings.append({"kind": "GALILEO", "title": "Incasso scaduto", "detail": f"Residuo scaduto € {finance['overdue']:,.0f}."})
        suggestions.append("Verificare con Amministrazione lo stato dell'incasso e il prossimo follow-up.")
    email = _email_signal(project)
    if email:
        findings.append({"kind": email["kind"], "title": email["title"], "detail": email["detail"]})
        suggestions.append(email["action"])
    penalty = next((f for f in project.extracted_fields if f.field_key == "penalty_cap"), None)
    if penalty and penalty.review_status not in {"CONFIRMED", "CORRECTED"}:
        findings.append({"kind": "DOCUMENT", "title": "Cap penali da verificare", "detail": f"Valore estratto: {penalty.extracted_value}. Non è ancora operativo."})
        suggestions.append("Confermare o correggere il cap penali prima di usarlo nei controlli contrattuali.")
    return {
        "findings": findings,
        "inconsistencies": sum(1 for item in findings if "verific" in item["title"].lower()),
        "suggestions": list(dict.fromkeys(suggestions)),
    }
