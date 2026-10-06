from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from .confidence import confidence_summary
from .control import control_summary
from .models import Alert, Project

SEVERITY_WEIGHT = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}
DATA_ACQUISITION_STATUS = "ACQUISIZIONE_DATI"


def is_data_acquisition(project: Project) -> bool:
    """True while the commessa is incomplete; acquired domains may still be evaluated."""
    return project.status == DATA_ACQUISITION_STATUS


def has_control_data(project: Project) -> bool:
    """A valid B1 snapshot unlocks only Economy and Finance during acquisition."""
    return bool(project.control_snapshots)


@dataclass
class Candidate:
    fingerprint: str
    alert_type: str
    dimension: str
    severity: str
    title: str
    description: str
    source_kind: str = "RULE"
    source_ref: str | None = None
    confidence: float | None = None
    data_status: str = "CALCULATED"


def budget_summary(project: Project):
    if is_data_acquisition(project) and not has_control_data(project):
        return dict(budget=0.0, actual=0.0, committed=0.0, etc=0.0, forecast=0.0, variance=0.0, variance_pct=0.0)
    budget = sum(x.budget for x in project.budget_lines)
    actual = sum(x.actual for x in project.budget_lines)
    committed = sum(x.committed for x in project.budget_lines)
    etc = sum(x.etc for x in project.budget_lines)
    forecast = actual + committed + etc
    variance = forecast - budget
    variance_pct = (variance / budget * 100) if budget else 0
    return dict(
        budget=budget,
        actual=actual,
        committed=committed,
        etc=etc,
        forecast=forecast,
        variance=variance,
        variance_pct=variance_pct,
    )


def finance_summary(project: Project, today: date):
    if is_data_acquisition(project) and not has_control_data(project):
        return dict(invoiced=0.0, collected=0.0, overdue=0.0, unbilled=0.0)
    invoiced = sum(i.amount for i in project.invoices)
    collected = sum(i.paid_amount for i in project.invoices)
    overdue = sum(
        max(i.amount - i.paid_amount, 0) for i in project.invoices if i.due_date < today and i.paid_amount < i.amount
    )
    return dict(
        invoiced=invoiced, collected=collected, overdue=overdue, unbilled=max(project.order_value - invoiced, 0)
    )


def severity_for_budget(var_abs: float, var_pct: float):
    if var_abs <= 0:
        return None
    if var_pct >= 10 or var_abs >= 75000:
        return "CRITICAL"
    if var_pct >= 7 or var_abs >= 50000:
        return "HIGH"
    if var_pct >= 3 or var_abs >= 15000:
        return "MEDIUM"
    return None


def candidates_for_project(project: Project, today: date):
    # A just-created project has technical placeholders only. They are not business evidence.
    if is_data_acquisition(project) and not has_control_data(project):
        return []
    out = []
    # Finance: overdue invoices
    for inv in project.invoices:
        open_amt = max(inv.amount - inv.paid_amount, 0)
        if inv.due_date < today and open_amt > 0:
            days = (today - inv.due_date).days
            sev = "CRITICAL" if days >= 45 else "HIGH" if days >= 15 else "MEDIUM"
            closed = project.technical_status == "CLOSED"
            title = (
                "Commessa chiusa tecnicamente, ma resta un incasso aperto" if closed else "Pagamento cliente in ritardo"
            )
            out.append(
                Candidate(
                    f"OVERDUE:{inv.id}",
                    "OVERDUE_INVOICE",
                    "FINANCE",
                    sev,
                    title,
                    f"La fattura {inv.number} ha ancora €{open_amt:,.0f} da incassare ed è scaduta da {days} giorni.",
                    source_ref=f"invoice:{inv.number}",
                    data_status="CONFIRMED",
                )
            )

    # Finance: completed milestone but no invoice
    invoice_milestones = {i.milestone_name for i in project.invoices if i.milestone_name}
    for ms in project.milestones:
        if ms.invoice_required and ms.actual_date and ms.invoice_value > 0 and ms.name not in invoice_milestones:
            days = (today - ms.actual_date).days
            sev = "HIGH" if days >= 7 else "MEDIUM"
            out.append(
                Candidate(
                    f"UNBILLED:{ms.id}",
                    "UNBILLED_MILESTONE",
                    "FINANCE",
                    sev,
                    "Attività completata, ma la fattura non risulta emessa",
                    f"{ms.name} risulta completata il {ms.actual_date.strftime('%d/%m/%Y')}. Il sistema non trova la fattura prevista di circa €{ms.invoice_value:,.0f}.",
                    source_ref=f"milestone:{ms.id}",
                    data_status="CALCULATED",
                )
            )

    # Budget. If a Galileo control snapshot exists, do not use the legacy/manual ETC model.
    control = control_summary(project)
    if not control:
        b = budget_summary(project)
        sev = severity_for_budget(b["variance"], b["variance_pct"])
        if sev:
            out.append(
                Candidate(
                    f"BUDGET:{project.id}",
                    "FORECAST_OVERRUN",
                    "BUDGET",
                    sev,
                    "La commessa sta andando oltre il budget previsto",
                    f"Il forecast è €{b['forecast']:,.0f} contro un budget di €{b['budget']:,.0f}: +€{b['variance']:,.0f} ({b['variance_pct']:.1f}%).",
                    source_ref="budget:forecast",
                    data_status="CALCULATED",
                )
            )
    else:
        # Control-data rules use objective spend/commitment data and a conservative project-level
        # budget position. Local VdA overruns remain visible in the control table, while the
        # executive alert reflects whether the project-level position is covered or exposed.
        bh = control["budget_health"]
        if bh["gross_overrun"] > 0.01:
            overruns = []
            for row in control["vda_rows"]:
                over = row["committed_cost"] - row["operational_budget"]
                if over > 0.01:
                    overruns.append((over, row["vda_name"], row["purchases_closed"]))
            overruns.sort(reverse=True)
            top = ", ".join(f"{name} +€{amount:,.0f}" for amount, name, _ in overruns[:3])
            if bh["key"] == "CRITICAL":
                sev = "CRITICAL" if bh["uncovered_overrun"] >= 50000 else "HIGH"
                title = "Budget di commessa esposto: sforamento netto non coperto"
                description = (
                    f"Sforamenti già sostenuti/impegnati €{bh['gross_overrun']:,.0f}; residui su VdA con acquisti conclusi "
                    f"€{bh['closed_headroom']:,.0f}; esposizione netta €{bh['uncovered_overrun']:,.0f}. "
                    f"I residui non compensano automaticamente gli sforamenti e richiedono qualifica come saving/riallocazione. "
                    f"Principali scostamenti: {top}."
                )
            else:
                sev = "MEDIUM"
                title = "Sforamenti locali da presidiare; saving ancora da qualificare"
                description = (
                    f"Sforamenti identificati €{bh['gross_overrun']:,.0f}; residui su VdA con acquisti conclusi €{bh['closed_headroom']:,.0f}. "
                    f"Questi residui sono saving candidati, non copertura automatica. Eventuali riallocazioni devono essere esplicite. "
                    f"Principali scostamenti: {top}."
                )
            out.append(
                Candidate(
                    f"CONTROL_BUDGET:{project.id}",
                    "CONTROL_BUDGET_POSITION",
                    "BUDGET",
                    sev,
                    title,
                    description,
                    source_ref="control:budget-health",
                    data_status="CALCULATED",
                )
            )

        # Procurement maturity. This is deliberately conservative: without a reliable required-by date
        # the system raises a watch signal, not a red late-purchase conclusion.
        procurement = control.get("procurement", {})
        if procurement.get("delivery_window") in ("NEAR", "IMMINENT") and procurement.get("not_started_count", 0) > 0:
            top = procurement.get("not_started", [])[:4]
            top_text = ", ".join(f"{x['vda_name']} (€{x['budget']:,.0f})" for x in top)
            desc = (
                f"La commessa è indicata come prossima alla consegna e risultano {procurement['not_started_count']} VdA di acquisto diretto "
                f"con budget ma senza ordini identificati. {procurement.get('open_or_unknown_count', 0)} ulteriori VdA dirette hanno acquisti "
                f"non dichiarati conclusi. Da verificare: {top_text}. Il segnale non afferma che il materiale manchi: può essere incluso in package, "
                f"classificato altrove o non più richiesto."
            )
            out.append(
                Candidate(
                    f"PROCUREMENT_MATURITY:{project.id}",
                    "PROCUREMENT_MATURITY",
                    "PROCUREMENT",
                    "MEDIUM",
                    "Procurement da verificare prima della consegna",
                    desc,
                    source_ref="control:procurement",
                    data_status="CALCULATED",
                )
            )

    # Confidence Review pilot. It evaluates evidence coverage, not project performance.
    # Enabled for projects with a real/control foundation so missing demo data do not flood the portfolio.
    if project.control_snapshots:
        conf = confidence_summary(project, today)
        if conf["review_required"]:
            domains = ", ".join(f"{d['label']} {d['level_label']}" for d in conf["review_domains"])
            top_gaps = "; ".join(g["text"] for g in conf["gaps"][:4])
            out.append(
                Candidate(
                    f"CONFIDENCE_REVIEW:{project.id}",
                    "CONFIDENCE_REVIEW",
                    "PROJECT",
                    "MEDIUM",
                    "Confidence Review richiesta",
                    f"La qualità delle evidenze non consente un controllo pienamente affidabile in: {domains}. "
                    f"Principali gap: {top_gaps}. Avviare un ciclo interno coordinato dal Responsabile Tecnico con visibilità Direzione.",
                    source_ref="confidence:review",
                    data_status="CALCULATED",
                )
            )

    # Schedule + contract
    for ms in project.milestones:
        if ms.contract_date and ms.forecast_date and ms.forecast_date > ms.contract_date and not ms.actual_date:
            delay = (ms.forecast_date - ms.contract_date).days
            sev = "HIGH" if delay >= 15 else "MEDIUM"
            out.append(
                Candidate(
                    f"SCHEDULE:{ms.id}",
                    "SCHEDULE_DELAY",
                    "SCHEDULE",
                    sev,
                    f"{ms.name} prevista {delay} giorni oltre la data concordata",
                    f"Data contrattuale {ms.contract_date.strftime('%d/%m/%Y')}; previsione attuale {ms.forecast_date.strftime('%d/%m/%Y')}.",
                    source_ref=f"milestone:{ms.id}",
                    data_status="CALCULATED",
                )
            )
            if ms.ld_applicable:
                out.append(
                    Candidate(
                        f"LD:{ms.id}",
                        "LD_EXPOSURE",
                        "CONTRACT",
                        "CRITICAL" if delay >= 15 else "HIGH",
                        "Il ritardo può avere un impatto contrattuale",
                        f"{ms.name} è prevista con {delay} giorni di ritardo e risulta soggetta a penali contrattuali ({ms.ld_rate_weekly_pct:.2f}%/settimana).",
                        source_ref=f"milestone:{ms.id}",
                        data_status="CALCULATED",
                    )
                )

    # Actions
    for act in project.actions:
        if act.status not in ("CLOSED", "RESOLVED") and act.due_date and act.due_date < today:
            days = (today - act.due_date).days
            sev = "HIGH" if days >= 10 else "MEDIUM"
            out.append(
                Candidate(
                    f"ACTION:{act.id}",
                    "OVERDUE_ACTION",
                    "PROJECT",
                    sev,
                    "Azione scaduta senza chiusura",
                    f"{act.title} — owner {act.owner}, scaduta da {days} giorni.",
                    source_ref=f"action:{act.id}",
                    data_status="CONFIRMED",
                )
            )

    # Issues. Communication/document issues are aggregated for the executive view:
    # granular evidence remains available in the operational workspace.
    open_issues = [i for i in project.issues if i.status == "OPEN"]
    doc_issues = [
        i for i in open_issues if i.category == "DOCUMENTATION" and i.severity in ("MEDIUM", "HIGH", "CRITICAL")
    ]
    comm_issues = [
        i for i in open_issues if i.category == "COMMUNICATION" and i.severity in ("MEDIUM", "HIGH", "CRITICAL")
    ]
    if doc_issues and comm_issues:
        severity = "CRITICAL" if any(i.severity == "CRITICAL" for i in doc_issues + comm_issues) else "HIGH"
        source = next((i.source_ref for i in comm_issues + doc_issues if i.source_ref), None)
        out.append(
            Candidate(
                f"CUSTOMER_FOLLOWUP:{project.id}",
                "CUSTOMER_FOLLOWUP",
                "PROJECT",
                severity,
                "Cliente in attesa: documentazione e risposta da completare",
                "La corrispondenza mostra un sollecito cliente e resta aperta una richiesta documentale. Apri le fonti per vedere il messaggio che ha generato il blocco e l'attività assegnata.",
                source_ref=source or f"issue:{comm_issues[0].id}",
                data_status="CONFIRMED",
            )
        )
    else:
        for issue in doc_issues:
            sev = "HIGH" if issue.severity in ("HIGH", "CRITICAL") or issue.blocking else "MEDIUM"
            out.append(
                Candidate(
                    f"DOC:{issue.id}",
                    "DOCUMENT_ISSUE",
                    "PROJECT",
                    sev,
                    "Documentazione ancora da completare",
                    issue.title,
                    source_ref=issue.source_ref or f"issue:{issue.id}",
                    data_status="CONFIRMED",
                )
            )
        for issue in comm_issues:
            out.append(
                Candidate(
                    f"COMM:{issue.id}",
                    "COMMUNICATION_ISSUE",
                    "PROJECT",
                    "HIGH" if issue.severity in ("HIGH", "CRITICAL") else "MEDIUM",
                    "Cliente in attesa di risposta",
                    issue.title,
                    source_ref=issue.source_ref or f"issue:{issue.id}",
                    data_status="CONFIRMED",
                )
            )

    for issue in open_issues:
        if issue.category == "TECHNICAL" and issue.severity in ("HIGH", "CRITICAL"):
            out.append(
                Candidate(
                    f"TECH:{issue.id}",
                    "TECHNICAL_ISSUE",
                    "TECHNICAL",
                    issue.severity,
                    "Problema tecnico da chiudere",
                    issue.title,
                    source_ref=issue.source_ref or f"issue:{issue.id}",
                    data_status="CONFIRMED",
                )
            )

    # Change requests
    for change in project.changes:
        if not change.order_received and (change.work_started or change.estimated_cost > 0):
            age = (today - change.requested_date).days
            sev = "HIGH" if change.work_started else "MEDIUM"
            out.append(
                Candidate(
                    f"CHANGE:{change.id}",
                    "UNCOVERED_CHANGE",
                    "COMMERCIAL",
                    sev,
                    "Modifica richiesta dal cliente senza ordine formalizzato",
                    f"{change.description}. Costo stimato €{change.estimated_cost:,.0f}; dopo {age} giorni non risulta ancora un ordine cliente.",
                    source_ref=f"change:{change.id}",
                    data_status="INFERRED" if change.work_started else "CONFIRMED",
                )
            )

    # Project Intelligence findings are deliberately NOT converted into alerts here.
    # A finding is only a proposal extracted from free text. It must first be human-validated
    # and then explicitly applied to a controlled project object (forecast, issue, change, action).
    # Only the resulting structured project data can trigger deterministic alerts.

    return out


def recompute_alerts(db: Session, today: date | None = None):
    today = today or date.today()
    active_fingerprints = set()
    for project in db.query(Project).all():
        for cand in candidates_for_project(project, today):
            active_fingerprints.add(cand.fingerprint)
            existing = db.query(Alert).filter(Alert.fingerprint == cand.fingerprint).first()
            if existing:
                existing.alert_type = cand.alert_type
                existing.dimension = cand.dimension
                existing.severity = cand.severity
                existing.title = cand.title
                existing.description = cand.description
                existing.source_kind = cand.source_kind
                existing.source_ref = cand.source_ref
                existing.confidence = cand.confidence
                existing.data_status = cand.data_status
                if existing.status == "AUTO_RESOLVED":
                    existing.status = "OPEN"
            else:
                db.add(
                    Alert(
                        project_id=project.id,
                        fingerprint=cand.fingerprint,
                        alert_type=cand.alert_type,
                        dimension=cand.dimension,
                        severity=cand.severity,
                        title=cand.title,
                        description=cand.description,
                        source_kind=cand.source_kind,
                        source_ref=cand.source_ref,
                        confidence=cand.confidence,
                        data_status=cand.data_status,
                    )
                )
    for alert in db.query(Alert).all():
        if alert.fingerprint not in active_fingerprints and alert.status in ("OPEN", "ACKNOWLEDGED"):
            alert.status = "AUTO_RESOLVED"
    db.commit()


def project_health(project: Project):
    if is_data_acquisition(project) and not has_control_data(project):
        return {"FINANCE": "ND", "BUDGET": "ND", "TECHNICAL": "ND", "SCHEDULE": "ND", "CONTRACT": "ND"}
    # Missing data is not green. Each dimension becomes GREEN only when a usable source exists.
    has_finance = bool(project.invoices) or any(m.invoice_required for m in project.milestones)
    has_budget = bool(project.control_snapshots) or bool(project.budget_lines)
    has_technical = (
        any(i.category == "TECHNICAL" for i in project.issues)
        or project.technical_status == "CLOSED"
        or project.status in ("COMMISSIONING", "CLOSING")
    )
    has_schedule = bool(project.milestones)
    customer_orders = list(getattr(project, "customer_orders", []) or [])
    has_contract_full = bool(customer_orders) and all(
        getattr(o, "document_status", None) == "COMPLETE" for o in customer_orders
    )
    has_contract_partial = bool(customer_orders) or bool(project.changes)

    dims = {
        "FINANCE": "GREEN" if has_finance else "ND",
        "BUDGET": "GREEN" if has_budget else "ND",
        "TECHNICAL": "GREEN" if has_technical else "ND",
        "SCHEDULE": "GREEN" if has_schedule else "ND",
        "CONTRACT": "GREEN" if has_contract_full else ("PARTIAL" if has_contract_partial else "ND"),
    }
    rank = {"ND": -1, "PARTIAL": 0, "GREEN": 1, "YELLOW": 2, "RED": 3}
    for a in project.alerts:
        if a.status in ("RESOLVED", "IGNORED", "AUTO_RESOLVED"):
            continue
        # Data-confidence alerts are governance alerts: they must not turn a project-performance domain yellow/red.
        if a.alert_type == "CONFIDENCE_REVIEW":
            continue
        dim = a.dimension
        if dim not in dims:
            if dim in ("PROJECT", "COMMUNICATION"):
                dim = "TECHNICAL"
            elif dim == "COMMERCIAL":
                dim = "CONTRACT"
            else:
                continue
        color = "RED" if a.severity in ("CRITICAL", "HIGH") else "YELLOW"
        if rank[color] > rank[dims[dim]]:
            dims[dim] = color
    return dims


def attention_score(project: Project):
    if is_data_acquisition(project) and not has_control_data(project):
        return 0
    return sum(SEVERITY_WEIGHT.get(a.severity, 0) for a in project.alerts if a.status in ("OPEN", "ACKNOWLEDGED"))
