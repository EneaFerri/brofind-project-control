from __future__ import annotations

from collections import defaultdict

from .config import settings

# Master-data candidate. Logic is uniform; parameters calibrate expectations by type of VdA.
VDA_NATURE = {
    "C000028": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000032": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000008": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000013": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000017": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000003": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000019": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000026": ("DIRECT_PURCHASE", "Acquisto diretto / package"),
    "C000002": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000011": ("DIRECT_PURCHASE", "Acquisto diretto / package"),
    "C000016": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000027": ("DIRECT_PURCHASE", "Acquisto diretto / package"),
    "C000009": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000001": ("DIRECT_PURCHASE", "Acquisto diretto"),
    "C000021": ("LOGISTICS", "Logistica"),
    "C000029": ("MIXED_SERVICE", "Servizio / montaggio"),
    "C000014": ("MIXED_SERVICE", "Servizio / montaggio"),
    "C000025": ("INTERNAL", "Ore interne / servizi tecnici"),
    "C000024": ("INTERNAL", "Ore interne"),
    "C000030": ("INTERNAL", "Attività futura / sito"),
    "C009999": ("RESERVE", "Riserva"),
}

PROFILE_BY_NATURE = {
    "DIRECT_PURCHASE": {
        "expected_order_phase": "Anticipata / media",
        "lead_time": "Medio-alto",
        "rfq_relevance": "Media",
        "completion_evidence": "Scope coperto + PO/package riconciliati + chiusura acquisti",
    },
    "MIXED_SERVICE": {
        "expected_order_phase": "Tardiva",
        "lead_time": "Medio",
        "rfq_relevance": "Alta",
        "completion_evidence": "RFQ/offerte + fornitore individuato + PO/subappalto",
    },
    "LOGISTICS": {
        "expected_order_phase": "Tardiva",
        "lead_time": "Basso-medio",
        "rfq_relevance": "Media",
        "completion_evidence": "Piano logistico + ordini/booking coerenti con consegna",
    },
    "INTERNAL": {
        "expected_order_phase": "N/A",
        "lead_time": "N/A",
        "rfq_relevance": "N/A",
        "completion_evidence": "Avanzamento attività/costi interni",
    },
    "RESERVE": {
        "expected_order_phase": "N/A",
        "lead_time": "N/A",
        "rfq_relevance": "N/A",
        "completion_evidence": "Riserva economica, non procurement",
    },
    "UNKNOWN": {
        "expected_order_phase": "Da classificare",
        "lead_time": "N/D",
        "rfq_relevance": "N/D",
        "completion_evidence": "Da definire",
    },
}


def nature_for_vda(vda_code: str) -> dict:
    key, label = VDA_NATURE.get(vda_code, ("UNKNOWN", "Da classificare"))
    return {"key": key, "label": label, "profile": PROFILE_BY_NATURE[key]}


def requirements_by_vda(project) -> dict[str, list]:
    out = defaultdict(list)
    dismissed = {
        d.decision_key
        for d in getattr(project, "cockpit_decisions", [])
        if d.decision_type == "REQUIREMENT_DISPOSITION"
        and d.status == "ACTIVE"
        and (d.value or "").upper() == "DISMISSED"
    }
    for req in getattr(project, "requirements", []) or []:
        if req.requirement_key in dismissed:
            continue
        if req.vda_code:
            out[req.vda_code].append(req)
    return out


def analyze_procurement_row(row: dict, *, delivery_window: str = "UNKNOWN", requirements: list | None = None) -> dict:
    requirements = requirements or []
    nature = nature_for_vda(row["vda_code"])
    ordered = float(row.get("ordered") or 0.0)
    budget = float(row.get("operational_budget") or 0.0)
    closed = row.get("purchases_closed")
    near = delivery_window in ("NEAR", "IMMINENT")
    required = [r for r in requirements if r.status == "REQUIRED"]
    to_verify = [
        r
        for r in requirements
        if r.status == "TO_VERIFY" and (r.source_kind != "ENGINEERING" or settings.technical_document_findings_enabled)
    ]

    # State answers what the current structured data tell us, without inventing missing procurement steps.
    if nature["key"] in ("INTERNAL", "RESERVE"):
        state = {"key": "NA", "tone": "neutral", "label": "N/A"}
    elif nature["key"] == "UNKNOWN" and budget <= 0 and ordered <= 0:
        state = {"key": "NA", "tone": "neutral", "label": "N/A"}
    elif closed is True:
        state = {"key": "CLOSED", "tone": "green", "label": "Conclusi"}
    elif nature["key"] == "DIRECT_PURCHASE" and budget > 0 and ordered <= 0.01:
        state = {"key": "NOT_STARTED", "tone": "amber", "label": "Non avviati"}
    elif nature["key"] == "MIXED_SERVICE" and budget > 0 and ordered <= 0.01:
        state = {"key": "PREPARATION_UNKNOWN", "tone": "neutral", "label": "Preparazione N/D"}
    elif closed is False:
        state = {"key": "OPEN", "tone": "amber", "label": "Aperti"}
    elif ordered > 0:
        state = {"key": "IN_PROGRESS_UNKNOWN", "tone": "neutral", "label": "In corso · chiusura N/D"}
    elif budget > 0 and nature["key"] == "LOGISTICS":
        state = {"key": "NOT_DUE_OR_UNKNOWN", "tone": "neutral", "label": "Da contestualizzare"}
    else:
        state = {"key": "UNKNOWN", "tone": "neutral", "label": "N/D"}

    risk = {"key": "NONE", "tone": "neutral", "label": "—", "reason": "Nessun segnale procurement deterministico."}
    if nature["key"] == "DIRECT_PURCHASE":
        if state["key"] == "NOT_STARTED":
            if required and near:
                risk = {
                    "key": "HIGH",
                    "tone": "amber",
                    "label": "Verifica urgente",
                    "reason": "Requisito confermato, nessun ordine identificato e commessa prossima alla consegna. Creare una verifica al PM/Acquisti.",
                }
            elif near:
                risk = {
                    "key": "MEDIUM",
                    "tone": "amber",
                    "label": "Da verificare",
                    "reason": "Budget presente ma nessun ordine identificato in una fase prossima alla consegna.",
                }
            else:
                risk = {
                    "key": "LOW",
                    "tone": "neutral",
                    "label": "Monitorare",
                    "reason": "Budget presente ma nessun ordine identificato; la fase temporale non rende ancora il segnale urgente.",
                }
        elif state["key"] in ("OPEN", "IN_PROGRESS_UNKNOWN") and near:
            risk = {
                "key": "MEDIUM",
                "tone": "amber",
                "label": "Chiusura da verificare",
                "reason": "Acquisti non dichiarati conclusi in una fase prossima alla consegna.",
            }
        elif state["key"] == "CLOSED":
            risk = {"key": "NONE", "tone": "green", "label": "Coerente", "reason": "Acquisti dichiarati conclusi."}
    elif nature["key"] == "MIXED_SERVICE" and budget > 0:
        if state["key"] == "PREPARATION_UNKNOWN" and near:
            risk = {
                "key": "MEDIUM",
                "tone": "amber",
                "label": "Potenziale ritardo procurement",
                "reason": "Per servizi/montaggi l'ordine può essere tardivo; vicino alla consegna l'assenza di evidenza su RFQ, offerte e fornitore individuato può trasformarsi in ritardo.",
            }
        elif state["key"] == "PREPARATION_UNKNOWN":
            risk = {
                "key": "LOW",
                "tone": "neutral",
                "label": "Preparazione da monitorare",
                "reason": "Ordine non ancora emesso: verificare in seguito RFQ/offerte secondo la fase attesa della categoria.",
            }

    # Pending engineering scope is evidence, not a deterministic missing-purchase statement.
    if to_verify and risk["key"] == "NONE":
        risk = {
            "key": "INFO",
            "tone": "neutral",
            "label": "Scope da verificare",
            "reason": "Esiste un requisito engineering non ancora consolidato contrattualmente. Confermare o scartare prima di modificare lo stato acquisti.",
        }

    return {
        "nature": nature,
        "profile": nature["profile"],
        "state": state,
        "risk": risk,
        "requirements": [
            {
                "key": r.requirement_key,
                "title": r.title,
                "status": r.status,
                "source_kind": r.source_kind,
                "source_ref": r.source_ref,
                "source_date": r.source_date,
                "quantity": r.quantity,
                "procurement_mode": r.procurement_mode,
                "confidence": r.confidence,
                "note": r.note,
            }
            for r in requirements
        ],
    }


def summarize_procurement(rows: list[dict], delivery_window: str, delivery_context: str | None = None) -> dict:
    direct = [r for r in rows if r.get("procurement", {}).get("nature", {}).get("key") == "DIRECT_PURCHASE"]
    services = [r for r in rows if r.get("procurement", {}).get("nature", {}).get("key") == "MIXED_SERVICE"]
    not_started = [r for r in direct if r["procurement"]["state"]["key"] == "NOT_STARTED"]
    open_or_unknown = [r for r in direct if r["procurement"]["state"]["key"] in ("OPEN", "IN_PROGRESS_UNKNOWN")]
    closed = [r for r in direct if r["procurement"]["state"]["key"] == "CLOSED"]
    service_preparation = [r for r in services if r["procurement"]["state"]["key"] == "PREPARATION_UNKNOWN"]
    high = [r for r in rows if r["procurement"]["risk"]["key"] == "HIGH"]
    medium = [r for r in rows if r["procurement"]["risk"]["key"] == "MEDIUM"]

    return {
        "delivery_window": delivery_window,
        "delivery_context": delivery_context,
        "direct_vda_count": len(direct),
        "service_vda_count": len(services),
        "not_started_count": len(not_started),
        "open_or_unknown_count": len(open_or_unknown),
        "service_preparation_count": len(service_preparation),
        "closed_count": len(closed),
        "high_risk_count": len(high),
        "medium_risk_count": len(medium),
        "watch_count": len(high) + len(medium),
        "not_started": [
            {
                "vda_code": r["vda_code"],
                "vda_name": r["vda_name"],
                "budget": r["operational_budget"],
                "risk": r["procurement"]["risk"],
            }
            for r in not_started
        ],
        "top_watch": [
            {
                "vda_code": r["vda_code"],
                "vda_name": r["vda_name"],
                "budget": r["operational_budget"],
                "ordered": r["ordered"],
                "open_order_commitment": r["open_order_commitment"],
                "risk": r["procurement"]["risk"],
            }
            for r in (high + medium)[:8]
        ],
    }
