from __future__ import annotations

from collections import defaultdict
from typing import Optional

from .models import Project, ProjectControlSnapshot
from .procurement import analyze_procurement_row, requirements_by_vda, summarize_procurement


def latest_control_snapshot(project: Project) -> Optional[ProjectControlSnapshot]:
    if not project.control_snapshots:
        return None
    return max(project.control_snapshots, key=lambda s: (s.captured_at, s.id or 0))


def _economic_status(row: dict) -> dict:
    op = row["operational_budget"]
    committed = row["committed_cost"]
    if op <= 0 and committed > 0:
        return {"key": "NO_BUDGET", "tone": "red", "label": "Costo senza budget"}
    if op > 0 and committed > op:
        return {"key": "OVER", "tone": "red", "label": "Oltre budget"}
    if op > 0 and committed / op >= 0.90:
        return {"key": "NEAR_LIMIT", "tone": "amber", "label": "Vicino al budget"}
    if op > 0:
        return {"key": "WITHIN", "tone": "green", "label": "Nei limiti"}
    return {"key": "NO_ACTIVITY", "tone": "neutral", "label": "Nessun budget/movimento"}


def _budget_health(rows: list[dict], operational_budget: float) -> dict:
    gross_overrun = sum(max(r["committed_cost"] - r["operational_budget"], 0.0) for r in rows)
    closed_headroom = sum(
        max(r["operational_budget"] - r["committed_cost"], 0.0)
        for r in rows if r["purchases_closed"] is True
    )
    open_headroom = sum(
        max(r["operational_budget"] - r["committed_cost"], 0.0)
        for r in rows if r["purchases_closed"] is not True
    )
    uncovered = max(gross_overrun - closed_headroom, 0.0)
    gross_pct = (gross_overrun / operational_budget * 100) if operational_budget else 0.0
    open_pct = (open_headroom / operational_budget * 100) if operational_budget else 0.0

    if gross_overrun <= 0.01:
        key, tone, label = "OK", "green", "Sotto controllo"
        message = "Nessuno sforamento già impegnato rilevato."
    elif uncovered <= 0.01:
        key, tone, label = "WATCH", "amber", "Da presidiare"
        message = (
            "Esistono sforamenti locali e residui su VdA con acquisti conclusi. I residui non compensano automaticamente "
            "gli sforamenti: vanno prima qualificati come saving e ogni riallocazione deve essere esplicita."
        )
    else:
        material = uncovered >= max(15000.0, operational_budget * 0.02)
        exposed = open_pct >= 20.0
        if material or (gross_pct >= 3.0 and exposed):
            key, tone, label = "CRITICAL", "red", "Critico"
            message = "Sforamento netto non coperto con esposizione residua significativa."
        else:
            key, tone, label = "WATCH", "amber", "Da presidiare"
            message = "Sforamento non completamente coperto, ma ancora sotto la soglia di criticità di commessa."

    return {
        "key": key,
        "tone": tone,
        "label": label,
        "message": message,
        "gross_overrun": gross_overrun,
        "gross_overrun_pct": gross_pct,
        "closed_headroom": closed_headroom,
        "uncovered_overrun": uncovered,
        "open_headroom": open_headroom,
        "open_headroom_pct": open_pct,
    }


def control_summary(project: Project) -> Optional[dict]:
    snap = latest_control_snapshot(project)
    if not snap:
        return None

    actual_total = snap.received + snap.labor + snap.overhead
    absorbed_committed = actual_total + snap.open_order_commitment
    uncommitted = snap.operational_budget - absorbed_committed
    baseline_delta = snap.operational_budget - snap.baseline_budget
    baseline_delta_pct = (baseline_delta / snap.baseline_budget * 100) if snap.baseline_budget else 0.0
    order_reconciliation = snap.orders_jmrp - snap.orders_extract
    residual_reconciliation = snap.orders_extract - (snap.received + snap.open_order_commitment)

    groups = defaultdict(lambda: {
        "vda_code": "", "vda_name": "", "baseline_budget": 0.0, "operational_budget": 0.0,
        "ordered": 0.0, "received": 0.0, "open_order_commitment": 0.0, "labor": 0.0,
        "overhead": 0.0, "centers": [], "closed_values": [],
    })
    for line in snap.lines:
        g = groups[line.vda_code]
        g["vda_code"] = line.vda_code
        g["vda_name"] = line.vda_name
        g["baseline_budget"] += line.baseline_budget
        g["operational_budget"] += line.operational_budget
        g["ordered"] += line.ordered
        g["received"] += line.received
        g["open_order_commitment"] += line.open_order_commitment
        g["labor"] += line.labor
        g["overhead"] += line.overhead
        if line.purchases_closed is not None:
            g["closed_values"].append(bool(line.purchases_closed))
        g["centers"].append({
            "analysis_center": line.analysis_center,
            "baseline_budget": line.baseline_budget,
            "operational_budget": line.operational_budget,
            "ordered": line.ordered,
            "received": line.received,
            "open_order_commitment": line.open_order_commitment,
            "labor": line.labor,
            "overhead": line.overhead,
            "purchases_closed": line.purchases_closed,
            "source_ref": line.source_ref,
        })

    rows = []
    req_map = requirements_by_vda(project)
    saving_decisions = {
        d.decision_key: d for d in getattr(project, "cockpit_decisions", [])
        if d.decision_type == "VDA_SAVING" and d.status == "ACTIVE" and (d.value or "").upper() == "CONSOLIDATED"
    }
    for g in groups.values():
        closed_values = g.pop("closed_values")
        purchases_closed = None if not closed_values else all(closed_values)
        saving_confirmed = g["vda_code"] in saving_decisions
        actual_cost = g["received"] + g["labor"] + g["overhead"]
        committed_cost = actual_cost + g["open_order_commitment"]
        remaining = g["operational_budget"] - committed_cost
        usage_pct = (committed_cost / g["operational_budget"] * 100) if g["operational_budget"] else 0.0
        row = {
            **g,
            "purchases_closed": purchases_closed,
            "saving_confirmed": saving_confirmed,
            "actual_cost": actual_cost,
            "committed_cost": committed_cost,
            "remaining_uncommitted": remaining,
            "usage_pct": usage_pct,
            "scope_delta": g["operational_budget"] - g["baseline_budget"],
        }
        row["economic_status"] = _economic_status(row)
        row["procurement"] = analyze_procurement_row(
            row, delivery_window=getattr(project, "delivery_window", "UNKNOWN"), requirements=req_map.get(row["vda_code"], [])
        )
        row["procurement_status"] = row["procurement"]["state"]
        row["procurement_risk"] = row["procurement"]["risk"]
        if remaining <= 0.01:
            row["saving_status"] = {"key": "NONE", "tone": "neutral", "label": "—", "amount": 0.0, "note": "Nessun residuo positivo da qualificare."}
        elif saving_confirmed:
            row["saving_status"] = {"key": "CONSOLIDATED", "tone": "green", "label": "Saving consolidato", "amount": remaining, "note": "Residuo validato e trasferibile al margine di commessa; non autorizza spesa su altre VdA senza riallocazione."}
        elif purchases_closed is True:
            row["saving_status"] = {"key": "CANDIDATE", "tone": "amber", "label": "Saving candidato", "amount": remaining, "note": "Acquisti dichiarati conclusi: verificare eventuali costi residui prima di consolidare il saving."}
        else:
            row["saving_status"] = {"key": "RESIDUAL", "tone": "neutral", "label": "Budget residuo", "amount": remaining, "note": "Residuo matematico: non è ancora saving."}
        rows.append(row)

    economic_order = {"NO_BUDGET": 0, "OVER": 1, "NEAR_LIMIT": 2, "WITHIN": 3, "NO_ACTIVITY": 4}
    procurement_order = {"NOT_STARTED": 0, "PREPARATION_UNKNOWN": 1, "OPEN": 2, "IN_PROGRESS_UNKNOWN": 3, "UNKNOWN": 4, "CLOSED": 5, "NA": 6}
    rows.sort(key=lambda x: (
        economic_order.get(x["economic_status"]["key"], 9),
        procurement_order.get(x["procurement_status"]["key"], 9),
        -abs(min(x["remaining_uncommitted"], 0)), x["vda_name"]
    ))

    line_baseline = sum(r["baseline_budget"] for r in rows)
    line_operational = sum(r["operational_budget"] for r in rows)
    line_ordered = sum(r["ordered"] for r in rows)
    line_received = sum(r["received"] for r in rows)
    line_open = sum(r["open_order_commitment"] for r in rows)
    line_labor = sum(r["labor"] for r in rows)
    line_overhead = sum(r["overhead"] for r in rows)

    approved_changes = [c for c in project.changes if c.order_received]
    approved_change_cost = sum(c.estimated_cost for c in approved_changes)
    approved_change_sales = sum(c.quoted_value for c in approved_changes)
    theoretical_authorized_budget = snap.baseline_budget + approved_change_cost
    budget_bridge_difference = snap.operational_budget - theoretical_authorized_budget

    customer_orders = sorted(project.customer_orders, key=lambda x: x.order_date)
    customer_order_net = sum(o.net_value for o in customer_orders)
    base_order_net = sum(o.net_value for o in customer_orders if o.order_kind == "BASE")
    extra_order_net = sum(o.net_value for o in customer_orders if o.order_kind == "EXTRA")
    budget_margin = customer_order_net - snap.operational_budget if customer_order_net else None
    budget_margin_pct = (budget_margin / customer_order_net * 100) if customer_order_net else None
    contract_documentation_complete = bool(customer_orders) and all(o.document_status == "COMPLETE" for o in customer_orders)

    quality_issues = []
    if abs(order_reconciliation) > 0.01:
        quality_issues.append({
            "key": "ORDERS_MISMATCH",
            "label": "Totale ordini non perfettamente allineato tra JMRP e interrogazione ordini",
            "amount": order_reconciliation,
            "detail": f"JMRP €{snap.orders_jmrp:,.2f} · estrazione ordini €{snap.orders_extract:,.2f}",
        })
    if abs(residual_reconciliation) > 0.01:
        quality_issues.append({
            "key": "RESIDUAL_MISMATCH",
            "label": "Ordini, ricevimenti e residuo non quadrano",
            "amount": residual_reconciliation,
            "detail": f"Ordini €{snap.orders_extract:,.2f} · ricevuto+residuo €{snap.received + snap.open_order_commitment:,.2f}",
        })
    if abs(line_operational - snap.operational_budget) > 0.01:
        quality_issues.append({
            "key": "BUDGET_BRIDGE_MISMATCH",
            "label": "Budget VdA ricostruito e budget operativo Galileo differiscono leggermente",
            "amount": line_operational - snap.operational_budget,
            "detail": f"Baseline + Extra 1 per VdA €{line_operational:,.2f} · Galileo €{snap.operational_budget:,.2f}",
        })
    unallocated_labor = snap.labor - line_labor
    unallocated_overhead = snap.overhead - line_overhead
    if abs(unallocated_labor) > 0.01:
        quality_issues.append({
            "key": "LABOR_UNALLOCATED",
            "label": "Parte del costo uomo non è ancora attribuita a una VdA nel pilot",
            "amount": unallocated_labor,
            "detail": f"Totale JMRP €{snap.labor:,.2f} · attribuito alle VdA €{line_labor:,.2f}",
        })
    if abs(unallocated_overhead) > 0.01:
        quality_issues.append({
            "key": "OVERHEAD_UNALLOCATED",
            "label": "Spese generali non ancora attribuite a una VdA nel pilot",
            "amount": unallocated_overhead,
            "detail": f"Totale JMRP €{snap.overhead:,.2f} · attribuito alle VdA €{line_overhead:,.2f}",
        })

    budget_health = _budget_health(rows, snap.operational_budget)
    saving_candidate = sum(r["saving_status"]["amount"] for r in rows if r["saving_status"]["key"] == "CANDIDATE")
    saving_consolidated = sum(r["saving_status"]["amount"] for r in rows if r["saving_status"]["key"] == "CONSOLIDATED")
    procurement_summary = summarize_procurement(
        rows, getattr(project, "delivery_window", "UNKNOWN"), getattr(project, "delivery_context", None)
    )

    previous = None
    previous_snaps = [s for s in project.control_snapshots if s.id != snap.id and s.captured_at <= snap.captured_at]
    if previous_snaps:
        ps = max(previous_snaps, key=lambda s: (s.captured_at, s.id or 0))
        previous = {
            "captured_at": ps.captured_at,
            "operational_budget_delta": snap.operational_budget - ps.operational_budget,
            "orders_delta": snap.orders_extract - ps.orders_extract,
            "received_delta": snap.received - ps.received,
        }

    return {
        "snapshot_id": snap.id,
        "captured_at": snap.captured_at,
        "source_label": snap.source_label,
        "note": snap.note,
        "baseline_budget": snap.baseline_budget,
        "operational_budget": snap.operational_budget,
        "baseline_delta": baseline_delta,
        "baseline_delta_pct": baseline_delta_pct,
        "approved_change_cost": approved_change_cost,
        "approved_change_sales": approved_change_sales,
        "theoretical_authorized_budget": theoretical_authorized_budget,
        "budget_bridge_difference": budget_bridge_difference,
        "orders_jmrp": snap.orders_jmrp,
        "orders_extract": snap.orders_extract,
        "received": snap.received,
        "open_order_commitment": snap.open_order_commitment,
        "labor": snap.labor,
        "overhead": snap.overhead,
        "actual_total": actual_total,
        "absorbed_committed": absorbed_committed,
        "certain_committed": absorbed_committed,  # backward-compatible alias used by older demo surfaces
        "uncommitted_budget": uncommitted,
        "committed_pct": (absorbed_committed / snap.operational_budget * 100) if snap.operational_budget else 0.0,
        "forecast_available": False,
        "forecast_message": "Forecast finale non stimato: il cockpit usa dati oggettivi e non richiede un ETC strutturato al PM.",
        "budget_health": budget_health,
        "saving": {
            "candidate": saving_candidate,
            "consolidated": saving_consolidated,
            "rule": "Il saving consolidato migliora il margine di commessa e non aumenta automaticamente il budget delle altre VdA.",
        },
        "procurement": procurement_summary,
        "contract": {
            "orders": [{
                "number": o.order_number, "date": o.order_date, "kind": o.order_kind, "quote_ref": o.quote_ref,
                "net_value": o.net_value, "tax_value": o.tax_value, "gross_value": o.gross_value,
                "currency": o.currency, "payment_terms": o.payment_terms, "incoterm": o.incoterm,
                "scope_summary": o.scope_summary, "source_ref": o.source_ref, "note": o.note,
                "document_status": o.document_status, "document_note": o.document_note,
            } for o in customer_orders],
            "net_total": customer_order_net,
            "base_net": base_order_net,
            "extra_net": extra_order_net,
            "budget_margin": budget_margin,
            "budget_margin_pct": budget_margin_pct,
            "documentation_complete": contract_documentation_complete,
        },
        "quality": {
            "status": "WARNING" if quality_issues else "OK",
            "issues": quality_issues,
            "orders_difference": order_reconciliation,
            "residual_difference": residual_reconciliation,
            "unallocated_labor": unallocated_labor,
            "unallocated_overhead": unallocated_overhead,
        },
        "line_totals": {
            "baseline": line_baseline, "operational": line_operational, "ordered": line_ordered,
            "received": line_received, "open": line_open, "labor": line_labor, "overhead": line_overhead,
        },
        "vda_rows": rows,
        "previous": previous,
    }
