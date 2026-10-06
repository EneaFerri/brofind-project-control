from __future__ import annotations

from datetime import date
from typing import Any

from .control import control_summary
from .config import settings
from .models import Project

LEVELS = {
    "HIGH": {"label": "Alta", "tone": "green", "rank": 3},
    "MEDIUM": {"label": "Media", "tone": "amber", "rank": 2},
    "LOW": {"label": "Bassa", "tone": "red", "rank": 1},
    "INSUFFICIENT": {"label": "Insufficiente", "tone": "neutral", "rank": 0},
}

RECOVERY_GUIDANCE = {
    "ECONOMIC": {
        "owner": "Amministrazione / Responsabile Tecnico",
        "actions": [
            "Chiudere le verifiche dati realmente materiali per il controllo economico.",
            "Qualificare la quota di budget ancora non coperta da costi o impegni prima di consolidare il forecast.",
            "Riconciliare con Procurement le VdA ancora aperte prima di consolidare saving o forecast finale.",
        ],
    },
    "PROCUREMENT": {
        "owner": "Acquisti / Responsabile Tecnico",
        "actions": [
            "Verificare le VdA con budget ma senza ordini identificati.",
            "Confermare quali VdA hanno realmente concluso gli acquisti.",
            "Validare o scartare i finding engineering che possono modificare lo scope residuo.",
        ],
    },
    "CONTRACT": {
        "owner": "Commerciale",
        "actions": [
            "Congelare nel cockpit le condizioni già ricavabili dal dossier contrattuale.",
            "Verificare la copertura contrattuale/economica dei change potenziali.",
            "Collegare ogni extra formalizzato al relativo ordine o accordo cliente.",
        ],
    },
    "SCHEDULE": {
        "owner": "PM / Responsabile Tecnico",
        "actions": [
            "Acquisire un planning operativo corrente come fonte autorevole.",
            "Confermare milestone aperte, forecast e prossime date critiche.",
            "Collegare le required date procurement alle milestone operative rilevanti.",
        ],
    },
    "TECHNICAL": {
        "owner": "Responsabile Tecnico",
        "actions": [
            "Confermare o scartare i finding tecnici/engineering ancora aperti.",
            "Identificare eventuali documenti tecnici bloccanti per acquisti o costruzione.",
            "Chiudere o assegnare le issue tecniche che riducono la leggibilità dello stato.",
        ],
    },
}

DOMAIN_LABELS = {
    "ECONOMIC": "Economia",
    "PROCUREMENT": "Procurement",
    "CONTRACT": "Contratto",
    "SCHEDULE": "Tempi",
    "TECHNICAL": "Tecnica",
}


def _domain(
    key: str,
    level: str,
    strengths: list[str],
    gaps: list[str],
    *,
    processing_backlog: list[str] | None = None,
    forecast_level: str | None = None,
    forecast_gaps: list[str] | None = None,
) -> dict[str, Any]:
    meta = LEVELS[level]
    out = {
        "key": key,
        "label": DOMAIN_LABELS[key],
        "level": level,
        "level_label": meta["label"],
        "tone": meta["tone"],
        "rank": meta["rank"],
        "strengths": strengths,
        "gaps": gaps,
        "processing_backlog": processing_backlog or [],
        "explanation": gaps[0] if gaps else (strengths[0] if strengths else "Nessuna evidenza disponibile."),
    }
    if forecast_level:
        fm = LEVELS[forecast_level]
        out.update({
            "forecast_level": forecast_level,
            "forecast_level_label": fm["label"],
            "forecast_tone": fm["tone"],
            "forecast_gaps": forecast_gaps or [],
        })
    return out


def _material_quality_issues(control: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Split true material data-quality gaps from minor reconciliation/attribution backlog.

    The threshold is deliberately transparent and conservative: a discrepancy only reduces
    current-state confidence when it is large enough to change the management reading.
    """
    issues = list(control.get("quality", {}).get("issues", []))
    budget = float(control.get("operational_budget") or 0.0)
    threshold = max(5000.0, budget * 0.01)
    material, minor = [], []
    for issue in issues:
        amount = abs(float(issue.get("amount") or 0.0))
        (material if amount >= threshold else minor).append(issue)
    return material, minor


def confidence_summary(project: Project, today: date | None = None) -> dict[str, Any]:
    """Evidence confidence, not AI probability and not project health.

    V0.3.8.1 separates three things that were previously mixed:
    1) information genuinely missing or stale (true confidence gap),
    2) information already present in a source but not yet normalized/frozen in the cockpit
       (processing backlog),
    3) uncertainty about the future/forecast, which is distinct from confidence in the
       current-state numbers.

    The cockpit therefore measures what the company *knows*, not how much cockpit data-entry
    has already been completed.
    """
    today = today or date.today()
    control = control_summary(project)
    dismissed_requirements = {
        d.decision_key for d in getattr(project, "cockpit_decisions", [])
        if d.decision_type == "REQUIREMENT_DISPOSITION" and d.status == "ACTIVE" and (d.value or "").upper() == "DISMISSED"
    }
    domains: dict[str, dict[str, Any]] = {}

    # ECONOMIC — current-state confidence is distinct from forecast confidence.
    if not control:
        domains["ECONOMIC"] = _domain(
            "ECONOMIC", "INSUFFICIENT", [],
            ["Snapshot economico strutturato non disponibile."],
            forecast_level="INSUFFICIENT",
            forecast_gaps=["Non esiste una base economica sufficiente per stimare il costo finale."],
        )
    else:
        strengths = [
            "Budget autorizzato disponibile da fonte strutturata.",
            "Consuntivato e ordini residui disponibili da fonte strutturata.",
        ]
        gaps: list[str] = []
        processing: list[str] = []
        if abs(control["budget_bridge_difference"]) <= 10:
            strengths.append("Baseline + extra riconciliano il budget operativo con scarto non materiale.")
        else:
            gaps.append("Budget autorizzato e budget operativo non sono riconciliati in modo materiale.")

        material_quality, minor_quality = _material_quality_issues(control)
        if material_quality:
            gaps.append(f"{len(material_quality)} anomalia/e dati materiale/i possono modificare la lettura economica corrente.")
        if minor_quality:
            processing.append(f"{len(minor_quality)} verifiche dati minori da riconciliare; non alterano oggi la lettura economica complessiva.")

        level = "HIGH" if not gaps else "MEDIUM"

        forecast_gaps: list[str] = []
        if control["uncommitted_budget"] > max(25000.0, control["operational_budget"] * 0.20):
            forecast_gaps.append("Quota rilevante del budget non è ancora coperta da costi/impegni noti.")
        if control["procurement"]["open_or_unknown_count"] or control["procurement"]["not_started_count"]:
            forecast_gaps.append("Il procurement residuo non è ancora sufficientemente consolidato per stimare il costo finale.")
        forecast_level = "MEDIUM" if forecast_gaps else "HIGH"

        domains["ECONOMIC"] = _domain(
            "ECONOMIC", level, strengths, gaps,
            processing_backlog=processing,
            forecast_level=forecast_level,
            forecast_gaps=forecast_gaps,
        )

    # PROCUREMENT — timing risk is project health, not evidence confidence.
    if not control or control["procurement"]["direct_vda_count"] == 0:
        domains["PROCUREMENT"] = _domain(
            "PROCUREMENT", "INSUFFICIENT", [],
            ["Mappa procurement strutturata non disponibile."],
        )
    else:
        p = control["procurement"]
        strengths = [
            f"{p['direct_vda_count']} VdA di acquisto diretto classificate.",
            "Ordini e residui fornitori disponibili da fonte strutturata.",
        ]
        if p["closed_count"]:
            strengths.append(f"{p['closed_count']} VdA risultano con acquisti conclusi.")
        gaps: list[str] = []
        processing: list[str] = []
        if p["not_started_count"] or p["open_or_unknown_count"]:
            gaps.append(
                "Completezza degli acquisti residui non ancora pienamente confermata "
                f"({p['not_started_count']} VdA senza ordini identificati; {p['open_or_unknown_count']} non dichiarate concluse)."
            )
        pending_scope = [
            r for r in getattr(project, "requirements", [])
            if r.status == "TO_VERIFY" and r.requirement_key not in dismissed_requirements
            and (r.source_kind != "ENGINEERING" or settings.technical_document_findings_enabled)
        ]
        if pending_scope:
            gaps.append("Lo scope residuo contiene requisiti/finding ancora da validare prima di poter dire con certezza cosa resta da acquistare.")
        level = "MEDIUM" if gaps else "HIGH"
        domains["PROCUREMENT"] = _domain("PROCUREMENT", level, strengths, gaps, processing_backlog=processing)

    # CONTRACT — un-frozen cockpit fields are processing backlog if the source dossier is present.
    orders = list(getattr(project, "customer_orders", []) or [])
    if not orders:
        domains["CONTRACT"] = _domain(
            "CONTRACT", "INSUFFICIENT", [], ["Pacchetto contrattuale non disponibile."],
        )
    else:
        strengths: list[str] = []
        gaps: list[str] = []
        processing: list[str] = []
        complete_orders = all(o.document_status == "COMPLETE" for o in orders)
        if complete_orders:
            strengths.append("Pacchetti ordine acquisiti e marcati completi.")
        else:
            gaps.append("Uno o più pacchetti ordine non risultano completi.")
        formalized_changes = [c for c in project.changes if c.order_received]
        if formalized_changes:
            strengths.append(f"{len(formalized_changes)} variazione/i formalizzata/e con ordine cliente.")
        pending_scope = [
            r for r in getattr(project, "requirements", [])
            if r.status == "TO_VERIFY" and r.requirement_key not in dismissed_requirements
            and (r.source_kind != "ENGINEERING" or settings.technical_document_findings_enabled)
        ]
        if pending_scope:
            gaps.append("Esiste scope tecnico da verificare rispetto alla copertura contrattuale/economica.")
        unformalized = [c for c in project.changes if not c.order_received]
        if unformalized:
            gaps.append(f"{len(unformalized)} variazione/i non risultano ancora formalizzate.")

        required_contract_keys = {"effective_date", "delivery_date", "payment_terms", "incoterm", "penalties"} if project.code == "9028" else set()
        frozen_contract_keys = {
            d.decision_key for d in getattr(project, "cockpit_decisions", [])
            if d.decision_type == "CONTRACT_CONDITION" and d.status == "FROZEN"
        }
        missing_contract_keys = required_contract_keys - frozen_contract_keys
        if missing_contract_keys and complete_orders:
            processing.append(
                f"{len(missing_contract_keys)} condizioni sono già nel dossier ma devono ancora essere estratte/validate nella Contract Baseline del cockpit."
            )
        elif missing_contract_keys:
            gaps.append(f"{len(missing_contract_keys)} condizioni contrattuali chiave non sono ancora disponibili in forma affidabile.")

        if not complete_orders:
            level = "LOW" if gaps else "MEDIUM"
        elif gaps:
            level = "MEDIUM"
        else:
            level = "HIGH"
        domains["CONTRACT"] = _domain("CONTRACT", level, strengths, gaps, processing_backlog=processing)

    # SCHEDULE — current operational planning is the real weak point of the 9028 pilot.
    milestones = list(getattr(project, "milestones", []) or [])
    if not milestones:
        domains["SCHEDULE"] = _domain(
            "SCHEDULE", "INSUFFICIENT", [],
            ["Planning operativo corrente / milestone strutturate non disponibili: non è possibile valutare con affidabilità i tempi."],
        )
    else:
        strengths = [f"{len(milestones)} milestone strutturate disponibili."]
        gaps: list[str] = []
        if any(m.forecast_date is None and m.actual_date is None for m in milestones):
            gaps.append("Una o più milestone aperte non hanno forecast aggiornato.")
        if any(m.contract_date is None for m in milestones):
            gaps.append("Una o più milestone non hanno data contrattuale strutturata.")
        level = "MEDIUM" if gaps else "HIGH"
        domains["SCHEDULE"] = _domain("SCHEDULE", level, strengths, gaps)

    # TECHNICAL — having scope evidence is positive; only unresolved current-state items reduce confidence.
    tech_issues = [i for i in getattr(project, "issues", []) if i.category == "TECHNICAL" and i.status == "OPEN"]
    requirements = list(getattr(project, "requirements", []) or [])
    pending_engineering = [
        r for r in requirements
        if r.source_kind == "ENGINEERING" and r.status == "TO_VERIFY" and r.requirement_key not in dismissed_requirements
    ] if settings.technical_document_findings_enabled else []
    if not tech_issues and not requirements and project.technical_status not in ("CLOSED",):
        domains["TECHNICAL"] = _domain(
            "TECHNICAL", "INSUFFICIENT", [], ["Evidenze tecniche sufficienti non disponibili."],
        )
    else:
        strengths: list[str] = []
        gaps: list[str] = []
        if requirements:
            strengths.append(f"{len(requirements)} requisito/i tecnico-contrattuali strutturati.")
        if project.technical_status == "CLOSED":
            strengths.append("Stato tecnico marcato chiuso.")
        if pending_engineering:
            gaps.append(f"{len(pending_engineering)} finding/requisito engineering richiede conferma o scarto umano.")
        if tech_issues:
            gaps.append(f"{len(tech_issues)} issue tecniche aperte.")
        if any(i.severity in ("HIGH", "CRITICAL") for i in tech_issues):
            level = "LOW"
        elif gaps:
            level = "MEDIUM"
        else:
            level = "HIGH"
        domains["TECHNICAL"] = _domain("TECHNICAL", level, strengths, gaps)

    ordered = [domains[k] for k in ("ECONOMIC", "PROCUREMENT", "CONTRACT", "SCHEDULE", "TECHNICAL")]
    for d in ordered:
        guidance = RECOVERY_GUIDANCE[d["key"]]
        d["recovery_owner"] = guidance["owner"]
        d["recovery_actions"] = guidance["actions"]
        d["target_level_label"] = "Media" if d["level"] in ("LOW", "INSUFFICIENT") else ("Alta" if d["level"] == "MEDIUM" else "Mantieni")

    # Overall confidence is not the minimum domain. One weak domain should be visible without
    # making the whole project look globally unreliable when the other domains are well supported.
    insufficient = sum(1 for d in ordered if d["level"] == "INSUFFICIENT")
    low = sum(1 for d in ordered if d["level"] == "LOW")
    if insufficient >= 3 or (insufficient >= 2 and low >= 1):
        overall_level = "INSUFFICIENT"
    elif low >= 2 or (low >= 1 and insufficient >= 1):
        overall_level = "LOW"
    elif any(d["level"] != "HIGH" for d in ordered):
        overall_level = "MEDIUM"
    else:
        overall_level = "HIGH"
    overall_meta = LEVELS[overall_level]
    overall = {"level": overall_level, "level_label": overall_meta["label"], "tone": overall_meta["tone"]}

    review_domains = [d for d in ordered if d["level"] in ("LOW", "INSUFFICIENT")]
    improvement_domains = [d for d in ordered if d["level"] != "HIGH"]
    gaps = [{"domain": d["label"], "level": d["level_label"], "text": g} for d in ordered for g in d["gaps"]]
    processing = [{"domain": d["label"], "text": x} for d in ordered for x in d.get("processing_backlog", [])]
    strengths = [{"domain": d["label"], "text": s} for d in ordered for s in d["strengths"]]

    # Current-state confidence and forecast confidence are intentionally separate.
    economic_forecast = domains["ECONOMIC"].get("forecast_level")
    forecast = None
    if economic_forecast:
        fm = LEVELS[economic_forecast]
        forecast = {
            "level": economic_forecast,
            "level_label": fm["label"],
            "tone": fm["tone"],
            "gaps": domains["ECONOMIC"].get("forecast_gaps", []),
        }

    return {
        "domains": domains,
        "ordered": ordered,
        "overall": overall,
        "forecast": forecast,
        "review_required": bool(review_domains),
        "review_domains": review_domains,
        "improvement_domains": improvement_domains,
        "improvement_count": len(improvement_domains),
        # Kept for API compatibility; now counts domains to improve, not every explanatory sentence.
        "gap_count": len(improvement_domains),
        "gaps": gaps,
        "processing_backlog": processing,
        "strengths": strengths,
        "review_owner": "Responsabile Tecnico",
        "visibility": "Direzione",
        "review_title": "Project Confidence Review",
        "review_goal": "Recuperare le evidenze realmente mancanti e completare la strutturazione delle informazioni già disponibili.",
        "pilot_scope": bool(project.control_snapshots),
    }
