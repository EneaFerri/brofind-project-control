"""Proiezioni per l'interfaccia V1 (shell condivisa e 8 superfici dei mockup canonici).

Questo modulo NON introduce nuova semantica: adatta il modello dati v0.3.8.1 alle
superfici V1. Dove il modello non offre ancora il dato richiesto dal mockup, la
struttura resta e il valore è dichiarato `N/D` / `Non ancora disponibile`
(IMPLEMENTATION GAP: vedi docs/v1/01_BASELINE_TO_TARGET_GAP.md).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from .analytics import timeline
from .confidence import confidence_summary
from .control import control_summary
from .models import Project
from .procurement import nature_for_vda
from .rules import has_control_data, is_data_acquisition

ACTIVE = ("OPEN", "ACKNOWLEDGED")
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Domini con semaforo (Portfolio / Overview). Billing e Payment restano distinti
# ma aprono la stessa superficie (Shared UI Shell Contract §2).
DOMAINS = [
    ("master", "Master", "master"),
    ("technical", "Technical", "technical"),
    ("procurement", "Procurement", "procurement"),
    ("documents", "Documents", "documents"),
    ("economics", "Economics", "economics"),
    ("billing", "Billing", "billing"),
    ("payment", "Payment", "billing"),
]
DOMAIN_LABELS = {key: label for key, label, _ in DOMAINS}

PROJECT_NAV = [
    ("overview", "Overview", ""),
    ("master", "Master", "/master"),
    ("technical", "Technical", "/technical"),
    ("procurement", "Procurement", "/procurement"),
    ("documents", "Documents", "/documents"),
    ("economics", "Economics", "/economics"),
    ("billing", "Billing & Payment", "/billing"),
    ("criticita", "Criticità", "/criticita"),
    ("attivita", "Attività", "/attivita"),
    ("conversazioni", "Conversazioni", "/conversazioni"),
    ("storico", "Storico", "/storico"),
]

ALERT_DOMAIN = {
    "SCHEDULE_DELAY": "master",
    "LD_EXPOSURE": "master",
    "TECHNICAL_ISSUE": "technical",
    "COMMUNICATION_ISSUE": "technical",
    "PROCUREMENT_MATURITY": "procurement",
    "DOCUMENT_ISSUE": "documents",
    "CUSTOMER_FOLLOWUP": "documents",
    "FORECAST_OVERRUN": "economics",
    "CONTROL_BUDGET_POSITION": "economics",
    "UNCOVERED_CHANGE": "economics",
    "UNBILLED_MILESTONE": "billing",
    "OVERDUE_INVOICE": "payment",
}
DIMENSION_DOMAIN = {
    "SCHEDULE": "master",
    "TECHNICAL": "technical",
    "PROJECT": "technical",
    "COMMUNICATION": "technical",
    "PROCUREMENT": "procurement",
    "BUDGET": "economics",
    "FINANCE": "payment",
    "CONTRACT": "economics",
    "COMMERCIAL": "economics",
}
# Segnali che non descrivono lo stato di un dominio ma il lavoro o la qualità delle evidenze.
NON_DOMAIN_ALERTS = {"OVERDUE_ACTION", "CONFIDENCE_REVIEW"}
NON_DOMAIN_LABELS = {"OVERDUE_ACTION": "Attività", "CONFIDENCE_REVIEW": "Affidabilità dati"}

PHASES = {
    "ACQUISIZIONE_DATI": ("Acquisizione dati", "gray"),
    "HANDOVER": ("In avvio", "gray"),
    "ENGINEERING": ("Engineering", "blue"),
    "PROCUREMENT": ("Procurement", "purple"),
    "EXECUTION": ("Esecuzione", "green"),
    "DELIVERY": ("Delivery", "teal"),
    "INSTALLATION": ("Installazione", "teal"),
    "COMMISSIONING": ("Commissioning", "orange"),
    "CLOSING": ("Chiusura", "gray"),
    "CLOSED": ("Chiusa", "gray"),
}
LIFECYCLE = {
    "ACQUISIZIONE_DATI": "avvio",
    "HANDOVER": "avvio",
    "CLOSED": "chiuse",
}
MASTER_PHASES = [
    "Commerciale",
    "Engineering",
    "Procurement",
    "Manufacturing",
    "Delivery",
    "Installation",
    "Commissioning",
    "Close-out",
]

STATE_LABELS = {"RED": "Critico", "YELLOW": "In attenzione", "GREEN": "In linea", "ND": "N/D"}


# --------------------------------------------------------------------------- util


def _active_alerts(p: Project) -> list:
    alerts = [a for a in p.alerts if a.status in ACTIVE]
    alerts.sort(key=lambda a: (SEVERITY_ORDER.get(a.severity, 9), a.id or 0))
    return alerts


def alert_domain(alert) -> str | None:
    if alert.alert_type in NON_DOMAIN_ALERTS:
        return None
    return ALERT_DOMAIN.get(alert.alert_type) or DIMENSION_DOMAIN.get(alert.dimension)


def alert_tone(alert) -> str:
    return "RED" if alert.severity in ("CRITICAL", "HIGH") else "YELLOW"


def _linked_action(p: Project, alert_id: int):
    marker = f"ALERT:{alert_id}"
    return next((a for a in p.actions if a.source == marker and a.status not in ("CLOSED", "RESOLVED")), None)


def _decisions(p: Project, decision_type: str) -> dict:
    return {
        d.decision_key: d
        for d in getattr(p, "cockpit_decisions", [])
        if d.decision_type == decision_type and d.status not in ("REVOKED",)
    }


def _pct(part: float | None, whole: float | None) -> float | None:
    if part is None or not whole:
        return None
    return part / whole * 100


def _contract_value(p: Project, control: dict | None) -> float | None:
    if control and control.get("contract", {}).get("net_total"):
        return control["contract"]["net_total"]
    if p.customer == "__PENDING__" or not p.order_value:
        return None
    return p.order_value


# ------------------------------------------------------------------ shell / header


def project_header(p: Project) -> dict:
    orders = sorted(p.customer_orders, key=lambda o: o.order_date)
    decisions = _decisions(p, "CONTRACT_CONDITION")
    pending = p.customer == "__PENDING__"
    delivery = None
    frozen_delivery = decisions.get("contractual_delivery_date") or decisions.get("delivery_date")
    if frozen_delivery and frozen_delivery.status == "FROZEN" and frozen_delivery.value:
        delivery = frozen_delivery.value
        try:
            delivery = date.fromisoformat(delivery)
        except ValueError:
            pass
    if delivery is None:
        for m in sorted(p.milestones, key=lambda m: m.contract_date or date.max):
            name = m.name.lower()
            if any(k in name for k in ("delivery", "consegna", "spedizione")):
                delivery = m.forecast_date or m.contract_date
                break
    phase_label, phase_tone = PHASES.get(p.status, (p.status.replace("_", " ").title(), "gray"))
    lifecycle = LIFECYCLE.get(p.status, "corso")
    return {
        "code": p.code,
        "customer": "Da acquisire" if pending else p.customer,
        "description": p.description or "Descrizione non disponibile",
        "status_label": {"avvio": "In avvio", "corso": "In corso", "chiuse": "Chiusa"}[lifecycle],
        "status_tone": {"avvio": "gray", "corso": "green", "chiuse": "gray"}[lifecycle],
        "phase_label": phase_label,
        "phase_tone": phase_tone,
        "offer": orders[0].quote_ref if orders and orders[0].quote_ref else None,
        "pm": p.pm_owner if p.pm_owner and p.pm_owner != "N/D" else None,
        "sales": p.sales_owner if p.sales_owner and p.sales_owner != "N/D" else None,
        "contract_start": orders[0].order_date if orders else None,
        "delivery": delivery,
        "pending": pending,
        "acquisition": is_data_acquisition(p),
    }


def project_nav(p: Project, active: str) -> list[dict]:
    alerts = _active_alerts(p)
    open_actions = [a for a in p.actions if a.status not in ("CLOSED", "RESOLVED")]
    badges = {"criticita": len(alerts), "attivita": len(open_actions)}
    return [
        {
            "key": key,
            "label": label,
            "url": f"/project/{p.code}{suffix}",
            "active": key == active,
            "badge": badges.get(key),
        }
        for key, label, suffix in PROJECT_NAV
    ]


# ------------------------------------------------------------------ domain states


def _domain_has_data(p: Project) -> dict[str, bool]:
    if is_data_acquisition(p) and not has_control_data(p):
        return {key: False for key, _, _ in DOMAINS}
    doc_files = any(f.is_present and f.source_type == "DOCUMENT" for f in p.source_files)
    return {
        "master": bool(p.milestones),
        "technical": any(i.category == "TECHNICAL" for i in p.issues)
        or bool(p.requirements)
        or p.technical_status == "CLOSED"
        or p.status in ("COMMISSIONING", "CLOSING"),
        "procurement": has_control_data(p),
        "documents": doc_files or any(i.category == "DOCUMENTATION" for i in p.issues),
        "economics": has_control_data(p) or bool(p.budget_lines),
        "billing": bool(p.invoices) or any(m.invoice_required for m in p.milestones),
        "payment": bool(p.invoices),
    }


def domain_states(p: Project) -> list[dict]:
    has_data = _domain_has_data(p)
    by_domain: dict[str, list] = defaultdict(list)
    for a in _active_alerts(p):
        d = alert_domain(a)
        if d:
            by_domain[d].append(a)
    out = []
    for key, label, surface in DOMAINS:
        alerts = by_domain.get(key, [])
        if alerts:
            state = "RED" if any(alert_tone(a) == "RED" for a in alerts) else "YELLOW"
            recap = alerts[0].title
        elif has_data[key]:
            state = "GREEN"
            recap = "Nessun segnale aperto sulle fonti disponibili (freschezza dei dati non ancora monitorata)."
        else:
            state = "ND"
            recap = "Dati non disponibili: dominio non ancora alimentato per questa commessa."
        out.append(
            {
                "key": key,
                "label": label,
                "state": state,
                "state_label": STATE_LABELS[state],
                "count": len(alerts),
                "recap": recap,
                "url": f"/project/{p.code}/{surface}",
            }
        )
    return out


def _alert_row(p: Project, a) -> dict:
    d = alert_domain(a)
    linked = _linked_action(p, a.id)
    surface = dict((k, s) for k, _, s in DOMAINS).get(d) if d else None
    if a.alert_type == "OVERDUE_ACTION":
        surface = "attivita"
    elif a.alert_type == "CONFIDENCE_REVIEW":
        surface = None
    return {
        "id": a.id,
        "type": a.alert_type,
        "title": a.title,
        "description": a.description,
        "tone": alert_tone(a),
        "severity": a.severity,
        "domain": d,
        "domain_label": DOMAIN_LABELS.get(d) if d else NON_DOMAIN_LABELS.get(a.alert_type, "Commessa"),
        "source_ref": a.source_ref,
        "data_status": a.data_status,
        "url": f"/project/{p.code}/{surface}" if surface else None,
        "linked_action": (
            {"id": linked.id, "owner": linked.owner, "due_date": linked.due_date, "title": linked.title}
            if linked
            else None
        ),
    }


# --------------------------------------------------------------------- portfolio


def portfolio_row(p: Project) -> dict:
    header = project_header(p)
    domains = domain_states(p)
    alerts = _active_alerts(p)
    reds = sum(1 for d in domains if d["state"] == "RED")
    yellows = sum(1 for d in domains if d["state"] == "YELLOW")
    evaluated = sum(1 for d in domains if d["state"] != "ND")
    if reds:
        bucket = "red"
    elif yellows:
        bucket = "yellow"
    elif evaluated:
        bucket = "green"
    else:
        bucket = "inactive"
    top = alerts[0] if alerts else None
    if top:
        exposure = {"title": top.title, "tone": alert_tone(top)}
    elif bucket == "inactive":
        exposure = {"title": "In attesa di raccolta dati", "tone": "ND"}
    else:
        exposure = {"title": "Nessuna esposizione rilevante", "tone": "ND"}
    red_alerts = sum(1 for a in alerts if alert_tone(a) == "RED")
    return {
        "code": p.code,
        "customer": header["customer"],
        "description": p.description or "",
        "phase_label": header["phase_label"],
        "phase_tone": header["phase_tone"],
        "lifecycle": LIFECYCLE.get(p.status, "corso"),
        "domains": domains,
        "bucket": bucket,
        "areas": reds + yellows,
        "exposure": exposure,
        "red_alerts": red_alerts,
        "yellow_alerts": len(alerts) - red_alerts,
        "pm": header["pm"] or "N/D",
        "sales": header["sales"] or "N/D",
        "offer": header["offer"] or "",
    }


def portfolio(projects: list[Project]) -> dict:
    rows = [portfolio_row(p) for p in projects]
    rank = {"red": 0, "yellow": 1, "green": 2, "inactive": 3}
    rows.sort(key=lambda r: (rank[r["bucket"]], -r["areas"], r["code"]))
    lifecycle_counts = defaultdict(int)
    for r in rows:
        lifecycle_counts[r["lifecycle"]] += 1
    return {
        "rows": rows,
        "total": len(rows),
        "critical": sum(1 for r in rows if r["bucket"] == "red"),
        "attention": sum(1 for r in rows if r["bucket"] == "yellow"),
        "in_line": sum(1 for r in rows if r["bucket"] == "green"),
        "inactive": sum(1 for r in rows if r["bucket"] == "inactive"),
        "lifecycle": {
            "corso": lifecycle_counts["corso"],
            "avvio": lifecycle_counts["avvio"],
            "chiuse": lifecycle_counts["chiuse"],
            "archiviate": 0,
        },
        "domains": [(key, label) for key, label, _ in DOMAINS],
    }


# ---------------------------------------------------------------------- overview


def _next_gate(p: Project, today: date) -> dict | None:
    pending = [m for m in p.milestones if not m.actual_date and (m.forecast_date or m.contract_date)]
    if not pending:
        return None
    m = min(pending, key=lambda m: m.contract_date or m.forecast_date)
    delayed = bool(m.contract_date and m.forecast_date and m.forecast_date > m.contract_date)
    return {
        "name": m.name,
        "target": m.contract_date,
        "forecast": m.forecast_date,
        "delayed": delayed,
        "ld": m.ld_applicable,
    }


def overview(p: Project, today: date) -> dict:
    domains = domain_states(p)
    alerts = [_alert_row(p, a) for a in _active_alerts(p)]
    main = alerts[0] if alerts else None
    return {
        "domains": domains,
        "critical_areas": sum(1 for d in domains if d["state"] == "RED"),
        "attention_areas": sum(1 for d in domains if d["state"] == "YELLOW"),
        "main": main,
        "others": alerts[1:4],
        "more": max(len(alerts) - 4, 0),
        "gate": _next_gate(p, today),
    }


# ------------------------------------------------------------------------ master


def master(p: Project, today: date) -> dict:
    milestones = sorted(p.milestones, key=lambda m: (m.contract_date or m.forecast_date or date.max, m.id or 0))
    alerts_by_ref = defaultdict(list)
    for a in _active_alerts(p):
        if a.source_ref:
            alerts_by_ref[a.source_ref].append(a)
    rows = []
    first_delay_index = None
    for i, m in enumerate(milestones):
        reference = m.actual_date or m.forecast_date
        delta = (reference - m.contract_date).days if (reference and m.contract_date) else None
        if m.actual_date:
            state, tone = "Completata", "green"
        elif m.forecast_date and m.contract_date and m.forecast_date > m.contract_date:
            state, tone = "In ritardo", "red"
            if first_delay_index is None:
                first_delay_index = i
        elif m.contract_date and m.contract_date < today:
            state, tone = "Da verificare", "amber"
        else:
            state, tone = "In linea", "green-soft"
        causes = [a.title for a in alerts_by_ref.get(f"milestone:{m.id}", [])]
        rows.append(
            {
                "index": i + 1,
                "name": m.name,
                "phase": None,
                "target": m.contract_date,
                "forecast": m.forecast_date,
                "actual": m.actual_date,
                "delta": delta,
                "state": state,
                "tone": tone,
                "readiness": None,
                "ld": m.ld_applicable,
                "invoice_value": m.invoice_value if m.invoice_required else None,
                "causes": causes,
                "downstream_check": False,
            }
        )
    # Regola Master: un ritardo a monte rende "da verificare" le milestone a valle
    # senza spostarne le date.
    downstream = []
    if first_delay_index is not None:
        for row in rows[first_delay_index + 1 :]:
            if not row["actual"]:
                row["downstream_check"] = True
                downstream.append(row["name"])
    pending = [r for r in rows if not r["actual"]]
    next_ms = pending[0] if pending else None
    contract_milestones = [
        {"key": key, "value": d.value}
        for key, d in _decisions(p, "CONTRACT_CONDITION").items()
        if key.startswith("milestone_") and d.status == "FROZEN"
    ]
    completed = sum(1 for r in rows if r["actual"])
    return {
        "rows": rows,
        "phases": MASTER_PHASES,
        "next": next_ms,
        "downstream": downstream,
        "completed": completed,
        "total": len(rows),
        "counts": {
            "completed": completed,
            "in_line": sum(1 for r in rows if r["state"] == "In linea"),
            "attention": sum(1 for r in rows if r["state"] == "Da verificare"),
            "late": sum(1 for r in rows if r["state"] == "In ritardo"),
        },
        "contract_milestones": contract_milestones,
    }


# --------------------------------------------------------------------- technical


def technical(p: Project, today: date) -> dict:
    dispositions = _decisions(p, "REQUIREMENT_DISPOSITION")
    open_rows, confirmed = [], []
    n = 0
    for r in sorted(p.requirements, key=lambda r: r.id or 0):
        n += 1
        disp = dispositions.get(r.requirement_key)
        row = {
            "ref": f"TC-{n:03d}",
            "requirement_id": r.id,
            "topic": r.title,
            "impact": f"VdA {r.vda_code}" if r.vda_code else "Scope",
            "evidence": [r.source_kind.title()] + ([r.source_ref] if r.source_ref else []),
            "due": None,
            "who": "Interno" if r.source_kind == "ENGINEERING" else "Contratto",
            "note": r.note,
            "date": r.source_date,
        }
        if disp and (disp.value or "").upper() == "DISMISSED":
            continue
        if r.status == "TO_VERIFY" and not (disp and (disp.value or "").upper() == "CONFIRMED"):
            row.update(state="Da confermare", tone="red")
            open_rows.append(row)
        else:
            row.update(state="Confermato", tone="green")
            confirmed.append(row)
    for i in p.issues:
        if i.category != "TECHNICAL" or i.status != "OPEN":
            continue
        n += 1
        open_rows.append(
            {
                "ref": f"TC-{n:03d}",
                "requirement_id": None,
                "topic": i.title,
                "impact": "Bloccante" if i.blocking else "Da valutare",
                "evidence": [i.source_ref] if i.source_ref else [],
                "due": i.due_date,
                "who": "N/D",
                "note": None,
                "date": None,
                "state": "Da decidere",
                "tone": "amber",
            }
        )
    risks = [_alert_row(p, a) for a in _active_alerts(p) if alert_domain(a) == "technical"]
    signals = sum(1 for f in p.agent_findings if f.status == "NEW")
    source_types = {f.source_type for f in p.source_files if f.is_present}
    sources = [
        ("Mail commessa", "OUTLOOK" in source_types or bool(p.communications)),
        ("KOM", None),
        ("P&ID / layout", None),
        ("Specifiche cliente", "DOCUMENT" in source_types),
        ("Report test / emissioni", None),
    ]
    return {
        "open": open_rows,
        "confirmed": confirmed,
        "risks": risks,
        "kpi": {
            "open": len(open_rows),
            "client": None,
            "interfaces": None,
            "signals": signals,
            "confirmed": len(confirmed),
        },
        "sources": [
            {
                "label": label,
                "state": "disponibile" if ok else ("non disponibile" if ok is False else "da collegare"),
                "tone": "green" if ok else "gray",
            }
            for label, ok in sources
        ],
    }


# ------------------------------------------------------------------- procurement


def procurement(p: Project, control: dict | None) -> dict:
    if not control:
        return {"available": False}
    rows = []
    counts = defaultdict(int)
    for r in control["vda_rows"]:
        nature = nature_for_vda(r["vda_code"])
        if nature["key"] in ("INTERNAL", "RESERVE"):
            continue
        state = r["procurement_status"]
        risk = r["procurement_risk"]
        counts[(state["key"], state["label"], state["tone"])] += 1
        rows.append(
            {
                "vda_code": r["vda_code"],
                "name": r["vda_name"],
                "nature": nature["label"],
                "stage": state["label"],
                "stage_tone": state["tone"],
                "control": risk["label"] if risk["key"] != "NONE" else "Nessun segnale",
                "control_tone": risk["tone"],
                "reason": risk.get("reason"),
                "budget": r["operational_budget"],
                "ordered": r["ordered"],
                "risk_key": risk["key"],
            }
        )
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}
    rows.sort(key=lambda x: (order.get(x["risk_key"], 4), -x["budget"]))
    segments = [
        {"label": label, "count": n, "tone": tone}
        for (key, label, tone), n in sorted(counts.items(), key=lambda kv: -kv[1])
    ]
    proc = control["procurement"]
    return {
        "available": True,
        "rows": rows,
        "segments": segments,
        "total": len(rows),
        "critical": proc.get("high_risk_count", 0),
        "watch": proc.get("watch_count", 0),
        "delivery_context": proc.get("delivery_context"),
    }


# --------------------------------------------------------------------- documents


def documents(p: Project, today: date) -> dict:
    rows = []
    for i in p.issues:
        if i.category != "DOCUMENTATION":
            continue
        overdue = bool(i.due_date and i.due_date < today and i.status == "OPEN")
        rows.append(
            {
                "name": i.title,
                "code": None,
                "category": "Documentazione",
                "state": "Atteso" if i.status == "OPEN" else "Disponibile",
                "tone": "red" if i.status == "OPEN" else "green",
                "due": i.due_date,
                "updated": None,
                "owner": None,
                "note": "Bloccante" if i.blocking else None,
                "overdue": overdue,
            }
        )
    for f in sorted(p.source_files, key=lambda f: f.file_name.lower()):
        if f.source_type != "DOCUMENT" or not f.is_present:
            continue
        rows.append(
            {
                "name": f.file_name,
                "code": None,
                "category": "Cartella commessa",
                "state": "Disponibile",
                "tone": "green",
                "due": None,
                "updated": f.modified_at,
                "owner": None,
                "note": "File rilevato: adeguatezza da confermare",
                "overdue": False,
            }
        )
    waiting = [r for r in rows if r["state"] == "Atteso"]
    soon = [r for r in waiting if r["due"] and today <= r["due"] <= today + timedelta(days=7)]
    segments = [
        {"label": label, "count": sum(1 for r in rows if r["state"] == state), "tone": tone}
        for label, state, tone in (
            ("Disponibili", "Disponibile", "green"),
            ("Da verificare", "Da verificare", "amber"),
            ("Da aggiornare", "Da aggiornare", "orange"),
            ("Attesi", "Atteso", "red"),
            ("N/A", "N/A", "gray"),
        )
    ]
    return {
        "rows": rows,
        "segments": segments,
        "total": len(rows),
        "waiting": len(waiting),
        "waiting_30": sum(1 for r in waiting if r["due"] and r["due"] <= today + timedelta(days=30)),
        "overdue": sum(1 for r in rows if r["overdue"]),
        "soon": len(soon),
        "upcoming": sorted([r for r in waiting if r["due"]], key=lambda r: r["due"])[:5],
        "critical": [r for r in rows if r["overdue"] or (r["note"] == "Bloccante" and r["state"] == "Atteso")],
    }


# --------------------------------------------------------------------- economics


def economics(p: Project, control: dict | None, today: date) -> dict:
    contract_value = _contract_value(p, control)
    approved = [c for c in p.changes if c.order_received]
    changes = [
        {
            "date": c.requested_date,
            "description": c.description,
            "amount": c.quoted_value,
            "state": "Approvata" if c.order_received else "In valutazione",
            "tone": "green" if c.order_received else "amber",
        }
        for c in sorted(p.changes, key=lambda c: c.requested_date, reverse=True)
    ]
    if control:
        groups: dict[str, dict] = {}
        for r in control["vda_rows"]:
            label = nature_for_vda(r["vda_code"])["label"]
            g = groups.setdefault(
                label, {"label": label, "budget": 0.0, "actual": 0.0, "open": 0.0, "committed": 0.0, "vda": []}
            )
            g["budget"] += r["operational_budget"]
            g["actual"] += r["actual_cost"]
            g["open"] += r["open_order_commitment"]
            g["committed"] += r["committed_cost"]
            g["vda"].append(r)
        categories = []
        for g in groups.values():
            g["variance"] = g["committed"] - g["budget"]
            g["variance_pct"] = _pct(g["variance"], g["budget"])
            g["tone"] = (
                "red"
                if g["variance"] > 0.01
                else ("amber" if g["budget"] and g["committed"] / g["budget"] >= 0.9 else "green")
            )
            if not g["budget"] and not g["committed"]:
                g["tone"] = "gray"
            g["vda"].sort(key=lambda r: -(r["committed_cost"] - r["operational_budget"]))
            categories.append(g)
        categories.sort(key=lambda g: -g["budget"])
        overruns = sorted(
            [r for r in control["vda_rows"] if r["committed_cost"] - r["operational_budget"] > 0.01],
            key=lambda r: -(r["committed_cost"] - r["operational_budget"]),
        )
        commitments = sorted(
            [r for r in control["vda_rows"] if r["open_order_commitment"] > 0.01],
            key=lambda r: -r["open_order_commitment"],
        )
        snapshots = sorted(p.control_snapshots, key=lambda s: (s.captured_at, s.id or 0))
        return {
            "mode": "control",
            "contract_value": contract_value,
            "budget": control["operational_budget"],
            "baseline_budget": control["baseline_budget"],
            "spent": control["actual_total"],
            "spent_pct": _pct(control["actual_total"], control["operational_budget"]),
            "open": control["open_order_commitment"],
            "committed": control["absorbed_committed"],
            "uncovered": control["uncommitted_budget"],
            "forecast": None,
            "forecast_note": control.get("forecast_message")
            or "Forecast finale non consolidabile senza costi a finire confermati.",
            "variance": None,
            "approved_changes": sum(c.quoted_value for c in approved),
            "approved_changes_pct": _pct(sum(c.quoted_value for c in approved), contract_value),
            "margin_budget": (contract_value - control["operational_budget"]) if contract_value else None,
            "categories": categories,
            "overruns": overruns[:5],
            "gross_overrun": control["budget_health"]["gross_overrun"],
            "saving": control["saving"],
            "commitments": commitments[:6],
            "changes": changes,
            "snapshots": [
                {"date": s.captured_at, "spent": s.received + s.labor + s.overhead, "budget": s.operational_budget}
                for s in snapshots
            ],
            "quality": control.get("quality", {}),
            "source_label": control["source_label"],
            "captured_at": control["captured_at"],
        }
    if p.budget_lines:
        categories = []
        for b in p.budget_lines:
            forecast = b.actual + b.committed + b.etc
            categories.append(
                {
                    "label": b.category,
                    "budget": b.budget,
                    "actual": b.actual,
                    "open": b.committed,
                    "committed": b.actual + b.committed,
                    "forecast": forecast,
                    "variance": forecast - b.budget,
                    "variance_pct": _pct(forecast - b.budget, b.budget),
                    "tone": "red" if forecast - b.budget > 0.01 else "green",
                    "vda": [],
                }
            )
        budget = sum(c["budget"] for c in categories)
        forecast = sum(c["forecast"] for c in categories)
        spent = sum(c["actual"] for c in categories)
        return {
            "mode": "legacy",
            "contract_value": contract_value,
            "budget": budget,
            "spent": spent,
            "spent_pct": _pct(spent, budget),
            "open": sum(c["open"] for c in categories),
            "committed": sum(c["committed"] for c in categories),
            "forecast": forecast,
            "forecast_note": "Forecast = consuntivo + impegnato + ETC inserito manualmente (dato demo).",
            "variance": forecast - budget,
            "variance_pct": _pct(forecast - budget, budget),
            "approved_changes": sum(c.quoted_value for c in approved),
            "approved_changes_pct": _pct(sum(c.quoted_value for c in approved), contract_value),
            "margin": (contract_value - forecast) if contract_value else None,
            "margin_pct": _pct(contract_value - forecast, contract_value) if contract_value else None,
            "categories": sorted(categories, key=lambda c: -c["budget"]),
            "overruns": [],
            "commitments": [],
            "changes": changes,
            "snapshots": [],
        }
    return {"mode": "none", "contract_value": contract_value, "changes": changes}


# --------------------------------------------------------------- billing & payment


CONTRACT_MILESTONE_LABELS = {
    "milestone_order_ack": ("Order acknowledgement", ("order", "ack")),
    "milestone_fat": ("FAT", ("fat",)),
    "milestone_delivery": ("Delivery", ("delivery", "consegna")),
    "milestone_sat_take_over": ("SAT / Take Over", ("sat", "take over")),
}


def billing(p: Project, control: dict | None, today: date) -> dict:
    contract_value = _contract_value(p, control)
    invoices = sorted(p.invoices, key=lambda i: i.issue_date)
    used = set()

    def match_invoice(keywords):
        for inv in invoices:
            if inv.id in used or not inv.milestone_name:
                continue
            name = inv.milestone_name.lower()
            if any(k in name for k in keywords):
                used.add(inv.id)
                return inv
        return None

    def invoice_state(inv):
        open_amount = max(inv.amount - inv.paid_amount, 0)
        if open_amount <= 0.01:
            return "Incassata", "green"
        if inv.due_date < today:
            return "Scaduta", "red"
        return "Da incassare", "blue"

    events = []
    for m in sorted(p.milestones, key=lambda m: m.contract_date or date.max):
        if not (m.invoice_required or m.invoice_value):
            continue
        inv = match_invoice((m.name.lower(),))
        matured = bool(m.actual_date)
        events.append(
            {
                "name": m.name,
                "amount": m.invoice_value or None,
                "share": _pct(m.invoice_value, contract_value) if m.invoice_value else None,
                "trigger": f"Milestone {m.name}",
                "maturity_date": m.actual_date or m.contract_date,
                "matured": matured,
                "invoice": inv,
            }
        )
    decisions = _decisions(p, "CONTRACT_CONDITION")
    for key, (label, keywords) in CONTRACT_MILESTONE_LABELS.items():
        d = decisions.get(key)
        if not d or d.status != "FROZEN":
            continue
        events.append(
            {
                "name": label,
                "amount": None,
                "share": None,
                "trigger": d.value,
                "maturity_date": None,
                "matured": None,
                "invoice": match_invoice(keywords),
            }
        )
    for inv in invoices:
        if inv.id in used:
            continue
        events.append(
            {
                "name": inv.milestone_name or "Fattura senza evento collegato",
                "amount": inv.amount,
                "share": _pct(inv.amount, contract_value),
                "trigger": "Evento contrattuale non configurato",
                "maturity_date": None,
                "matured": None,
                "invoice": inv,
            }
        )
    for e in events:
        inv = e["invoice"]
        if inv:
            e["state"], e["tone"] = invoice_state(inv)
            e["invoice_number"] = inv.number
            e["invoice_date"] = inv.issue_date
            e["due_date"] = inv.due_date
            e["collected"] = inv.paid_amount
            if e["amount"] is None:
                e["amount"] = inv.amount
                e["share"] = _pct(inv.amount, contract_value)
        else:
            e["invoice_number"] = e["invoice_date"] = e["due_date"] = e["collected"] = None
            if e["matured"]:
                e["state"], e["tone"] = "Da fatturare", "amber"
            elif e["matured"] is None:
                e["state"], e["tone"] = "Da verificare", "gray"
            else:
                e["state"], e["tone"] = "Non dovuto", "gray"
    invoiced = sum(i.amount for i in invoices)
    collected = sum(i.paid_amount for i in invoices)
    matured_amount = sum(e["amount"] or 0 for e in events if e["matured"])
    maturity_known = all(e["matured"] is not None for e in events) if events else False
    upcoming = sorted(
        [i for i in invoices if i.amount - i.paid_amount > 0.01],
        key=lambda i: i.due_date,
    )
    quarters = defaultdict(float)
    for pay in p.payments:
        quarters[f"Q{(pay.payment_date.month - 1) // 3 + 1} {pay.payment_date.year}"] += pay.amount
    segments = defaultdict(int)
    for e in events:
        segments[(e["state"], e["tone"])] += 1
    return {
        "contract_value": contract_value,
        "matured": matured_amount if maturity_known else None,
        "matured_partial": matured_amount if not maturity_known and matured_amount else None,
        "invoiced": invoiced if invoices or events else None,
        "collected": collected if invoices else None,
        "exposure": (invoiced - collected) if invoices else None,
        "pct": {
            "matured": _pct(matured_amount, contract_value) if maturity_known else None,
            "invoiced": _pct(invoiced, contract_value),
            "collected": _pct(collected, contract_value),
            "exposure": _pct(invoiced - collected, invoiced) if invoiced else None,
        },
        "events": events,
        "upcoming": [
            {
                "due": i.due_date,
                "number": i.number,
                "open": i.amount - i.paid_amount,
                "event": i.milestone_name,
                "days": (i.due_date - today).days,
                "state": "Scaduta" if i.due_date < today else "Da pagare",
                "tone": "red" if i.due_date < today else "amber",
            }
            for i in upcoming
        ],
        "quarters": [{"label": k, "amount": v} for k, v in quarters.items()],
        "quarters_max": max(quarters.values(), default=0),
        "segments": [{"label": s, "tone": t, "count": n} for (s, t), n in segments.items()],
    }


# --------------------------------------------------------------- operational pages


def criticita(p: Project) -> dict:
    rows = [_alert_row(p, a) for a in _active_alerts(p)]
    return {
        "rows": rows,
        "red": sum(1 for r in rows if r["tone"] == "RED"),
        "yellow": sum(1 for r in rows if r["tone"] == "YELLOW"),
    }


def storico(p: Project, today: date) -> list[dict]:
    events = [
        {"date": e["date"], "kind": e["kind"], "title": e["title"], "detail": e["detail"], "tone": e["tone"]}
        for e in timeline(p, today)
    ]
    for d in getattr(p, "cockpit_decisions", []):
        when = d.updated_at or d.created_at
        if not when:
            continue
        events.append(
            {
                "date": when.date(),
                "kind": "DECISIONE",
                "title": f"{d.decision_type.replace('_', ' ').title()} · {d.decision_key}",
                "detail": f"{d.status} · {d.value or ''} · {d.created_by or 'N/D'}",
                "tone": "blue",
            }
        )
    for imp in getattr(p, "source_imports", []):
        events.append(
            {
                "date": imp.processed_at.date(),
                "kind": "FONTE",
                "title": f"Import {imp.source_type.title()} · {imp.processor}",
                "detail": imp.status if not imp.error_message else f"{imp.status} · {imp.error_message}",
                "tone": "green" if imp.status == "SUCCESS" else "red",
            }
        )
    events.sort(key=lambda e: (e["date"], e["kind"]), reverse=True)
    return events


def confidence(p: Project, today: date) -> dict:
    return confidence_summary(p, today)


def control(p: Project) -> dict | None:
    return control_summary(p)
