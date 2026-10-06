from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .clock import utcnow
from .models import AgentFinding, AgentRun, Communication, Project

ENGINE_NAME = "LOCAL_PROJECT_INTELLIGENCE_V1"

MONTHS = {
    # EN
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    # IT
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
    # FR
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "décembre": 12,
    "decembre": 12,
}


@dataclass
class FindingSpec:
    finding_type: str
    dimension: str
    severity: str
    title: str
    summary: str
    evidence: str
    suggested_action: str
    suggested_owner: str
    confidence: float
    extracted_date: date | None = None
    extracted_amount: float | None = None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _sentences(text: str) -> list[str]:
    text = _normalize(text)
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def _evidence(text: str, keywords: list[str]) -> str:
    for sentence in _sentences(text):
        low = sentence.lower()
        if any(k in low for k in keywords):
            return sentence[:420]
    return _normalize(text)[:420]


def _parse_explicit_date(text: str, base: date) -> date | None:
    # yyyy-mm-dd
    m = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # dd/mm/yyyy or dd-mm-yyyy
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", text)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    # 30 September 2026 / 30 settembre / 30 septembre
    month_re = "|".join(sorted((re.escape(x) for x in MONTHS), key=len, reverse=True))
    m = re.search(rf"\b(\d{{1,2}})\s+({month_re})(?:\s+(20\d{{2}}))?\b", text, re.I)
    if m:
        day = int(m.group(1))
        month = MONTHS[m.group(2).lower()]
        year = int(m.group(3)) if m.group(3) else base.year
        try:
            candidate = date(year, month, day)
            # If year omitted and the date is implausibly in the past, roll one year.
            if not m.group(3) and candidate < base - timedelta(days=120):
                candidate = date(year + 1, month, day)
            return candidate
        except ValueError:
            pass
    return None


def _parse_relative_date(text: str, base: date) -> date | None:
    low = text.lower()
    patterns = [
        (r"\b(\d+)\s+(?:calendar\s+)?days?\b", 1),
        (r"\b(\d+)\s+(?:calendar\s+)?weeks?\b", 7),
        (r"\b(\d+)\s+giorni\b", 1),
        (r"\b(\d+)\s+settimane\b", 7),
        (r"\b(\d+)\s+jours\b", 1),
        (r"\b(\d+)\s+semaines\b", 7),
    ]
    words = {
        "one week": 7,
        "two weeks": 14,
        "three weeks": 21,
        "una settimana": 7,
        "due settimane": 14,
        "tre settimane": 21,
        "une semaine": 7,
        "deux semaines": 14,
        "trois semaines": 21,
    }
    for phrase, days in words.items():
        if phrase in low:
            return base + timedelta(days=days)
    for pattern, mult in patterns:
        m = re.search(pattern, low)
        if m:
            return base + timedelta(days=int(m.group(1)) * mult)
    return None


def extract_date(text: str, base: date) -> date | None:
    return _parse_explicit_date(text, base) or _parse_relative_date(text, base)


def _all_explicit_dates(text: str, base: date) -> list[date]:
    """Return explicit dates in textual order, deduplicated by occurrence value."""
    hits: list[tuple[int, date]] = []
    for m in re.finditer(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text):
        try:
            hits.append((m.start(), date(int(m.group(1)), int(m.group(2)), int(m.group(3)))))
        except ValueError:
            pass
    for m in re.finditer(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", text):
        try:
            hits.append((m.start(), date(int(m.group(3)), int(m.group(2)), int(m.group(1)))))
        except ValueError:
            pass
    month_re = "|".join(sorted((re.escape(x) for x in MONTHS), key=len, reverse=True))
    for m in re.finditer(rf"\b(\d{{1,2}})\s+({month_re})(?:\s+(20\d{{2}}))?\b", text, re.I):
        day = int(m.group(1))
        month = MONTHS[m.group(2).lower()]
        year = int(m.group(3)) if m.group(3) else base.year
        try:
            candidate = date(year, month, day)
            if not m.group(3) and candidate < base - timedelta(days=120):
                candidate = date(year + 1, month, day)
            hits.append((m.start(), candidate))
        except ValueError:
            pass
    hits.sort(key=lambda x: x[0])
    return [d for _, d in hits]


def _relative_days(text: str) -> int | None:
    low = text.lower()
    words = {
        "one week": 7,
        "two weeks": 14,
        "three weeks": 21,
        "una settimana": 7,
        "due settimane": 14,
        "tre settimane": 21,
        "une semaine": 7,
        "deux semaines": 14,
        "trois semaines": 21,
    }
    for phrase, days in words.items():
        if phrase in low:
            return days
    patterns = [
        (r"\b(\d+)\s+(?:calendar\s+)?days?\b", 1),
        (r"\b(\d+)\s+(?:calendar\s+)?weeks?\b", 7),
        (r"\b(\d+)\s+giorni\b", 1),
        (r"\b(\d+)\s+settimane\b", 7),
        (r"\b(\d+)\s+jours\b", 1),
        (r"\b(\d+)\s+semaines\b", 7),
    ]
    for pattern, mult in patterns:
        m = re.search(pattern, low)
        if m:
            return int(m.group(1)) * mult
    return None


def extract_schedule_date(text: str, base: date) -> date | None:
    """Conservative date extraction for schedule changes.

    If both old and revised dates are stated, the last explicit date is considered the candidate.
    If an old explicit date is followed by a relative delay (e.g. 30 Sep + two weeks), calculate from that anchor.
    A relative delay with no explicit anchor is intentionally NOT converted into a calendar date.
    """
    dates = _all_explicit_dates(text, base)
    if len(dates) >= 2:
        return dates[-1]
    if len(dates) == 1:
        days = _relative_days(text)
        if days and any(
            k in text.lower() for k in ["delay", "postpone", "slitt", "ritard", "rinvi", "retard", "report", "repouss"]
        ):
            return dates[0] + timedelta(days=days)
        return dates[0]
    return None


def extract_amount(text: str) -> float | None:
    patterns = [
        r"(?:€|eur\s*)\s*([0-9][0-9.,\s]{2,})",
        r"([0-9][0-9.,\s]{2,})\s*(?:€|eur)\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if not m:
            continue
        raw = m.group(1).replace(" ", "")
        if "," in raw and "." in raw:
            # infer European vs English formatting from final separator
            if raw.rfind(",") > raw.rfind("."):
                raw = raw.replace(".", "").replace(",", ".")
            else:
                raw = raw.replace(",", "")
        elif "," in raw:
            tail = raw.split(",")[-1]
            raw = raw.replace(".", "")
            raw = raw.replace(",", "." if len(tail) <= 2 else "")
        else:
            raw = raw.replace(",", "")
        try:
            return float(raw)
        except ValueError:
            pass
    return None


def analyze_communication(project: Project, comm: Communication) -> list[FindingSpec]:
    text = _normalize(f"{comm.subject}. {comm.body}")
    low = text.lower()
    found: list[FindingSpec] = []
    extracted_date = extract_date(text, comm.date)
    schedule_date = extract_schedule_date(text, comm.date)
    extracted_amount = extract_amount(text)

    # Customer escalation / communication issue
    escalation_kw = [
        "urgent",
        "third reminder",
        "second reminder",
        "reminder",
        "still waiting",
        "again",
        "sollecito",
        "ancora in attesa",
        "relance",
        "toujours en attente",
    ]
    if comm.direction == "INBOUND" and ((comm.reminders_count or 0) >= 2 or any(k in low for k in escalation_kw)):
        found.append(
            FindingSpec(
                "AGENT_CUSTOMER_ESCALATION",
                "COMMUNICATION",
                "HIGH",
                "Il cliente sta sollecitando una risposta",
                "La comunicazione indica che il cliente sta aspettando una risposta o ha già sollecitato Brofind. Verifica il thread prima di registrare la criticità.",
                _evidence(text, escalation_kw),
                "Rileggere il thread, rispondere al cliente e indicare un impegno chiaro",
                project.pm_owner,
                0.94,
            )
        )

    # Schedule / milestone risk
    schedule_kw = [
        "delay",
        "delayed",
        "postpone",
        "postponed",
        "cannot take place",
        "cannot be held",
        "slitt",
        "ritard",
        "rinvi",
        "retard",
        "reporté",
        "reportee",
        "repoussé",
        "repousse",
    ]
    milestone_kw = [
        "fat",
        "sat",
        "delivery",
        "shipment",
        "commissioning",
        "acceptance",
        "consegna",
        "collaudo",
        "livraison",
        "réception",
        "reception",
    ]
    if any(k in low for k in schedule_kw) and (any(k in low for k in milestone_kw) or extracted_date):
        found.append(
            FindingSpec(
                "AGENT_SCHEDULE_RISK",
                "SCHEDULE",
                "HIGH",
                "La mail segnala un possibile slittamento di una milestone",
                "La comunicazione sembra indicare una nuova data o un ritardo. Prima di aggiornare il planning va confermato che il messaggio sia stato interpretato correttamente.",
                _evidence(text, schedule_kw),
                "Confermare la nuova data e aggiornare il forecast solo dopo verifica",
                project.pm_owner,
                0.92,
                extracted_date=schedule_date,
            )
        )

    # Payment promise / collection signal
    payment_kw = [
        "payment",
        "paid",
        "pay",
        "released",
        "bank transfer",
        "bonifico",
        "pagamento",
        "payer",
        "paiement",
        "virement",
    ]
    promise_kw = ["will", "by", "entro", "sarà", "sara", "previsto", "sera", "avant", "expected"]
    if any(k in low for k in payment_kw) and any(k in low for k in promise_kw):
        found.append(
            FindingSpec(
                "AGENT_PAYMENT_PROMISE",
                "FINANCE",
                "MEDIUM",
                "La mail contiene una possibile promessa di pagamento",
                "Il cliente sembra indicare quando intende pagare. La promessa va verificata senza modificare fatture o incassi ufficiali.",
                _evidence(text, payment_kw),
                "Verificare la promessa di pagamento e programmare il follow-up sull'incasso",
                project.sales_owner,
                0.88,
                extracted_date=extracted_date,
                extracted_amount=extracted_amount,
            )
        )

    # Documents / deliverables
    document_kw = [
        "document",
        "drawing",
        "manual",
        "as-built",
        "as built",
        "datasheet",
        "dossier",
        "documentation",
        "disegn",
        "manuale",
        "plan",
        "schéma",
        "schema",
    ]
    waiting_kw = [
        "waiting",
        "missing",
        "please send",
        "please provide",
        "still need",
        "manc",
        "in attesa",
        "inviare",
        "attend",
        "manquant",
        "transmettre",
    ]
    if any(k in low for k in document_kw) and any(k in low for k in waiting_kw):
        sev = (
            "HIGH"
            if any(k in low for k in ["urgent", "blocking", "block", "cannot", "third reminder", "blocc", "bloquant"])
            else "MEDIUM"
        )
        found.append(
            FindingSpec(
                "AGENT_DOCUMENT_REQUEST",
                "PROJECT",
                sev,
                "La comunicazione segnala documentazione ancora da fornire",
                "Il cliente chiede documenti o segnala materiale ancora mancante. Verifica se la richiesta è ancora aperta e se può bloccare una milestone.",
                _evidence(text, document_kw + waiting_kw),
                "Confermare owner e data di rilascio della documentazione richiesta",
                project.pm_owner,
                0.91,
                extracted_date=extracted_date,
            )
        )

    # Change / extra scope
    change_kw = [
        "additional",
        "extra",
        "please include",
        "additionally",
        "modification",
        "modify",
        "change request",
        "fuori scopo",
        "aggiunt",
        "modifica",
        "supplement",
        "supplément",
        "modification",
    ]
    if any(k in low for k in change_kw):
        found.append(
            FindingSpec(
                "AGENT_CHANGE_REQUEST",
                "COMMERCIAL",
                "HIGH",
                "Il cliente potrebbe aver chiesto un extra o una modifica di scopo",
                "La comunicazione sembra introdurre attività aggiuntive rispetto allo scopo base. Prima di procedere va verificato se esiste copertura commerciale.",
                _evidence(text, change_kw),
                "Verificare lo scope contrattuale e, se necessario, aprire una variante/offerta extra",
                project.sales_owner,
                0.90,
                extracted_amount=extracted_amount,
            )
        )

    # Technical / performance risk
    technical_kw = [
        "performance",
        "efficiency",
        "fid",
        "emission",
        "guarantee",
        "guaranteed",
        "above limit",
        "below guaranteed",
        "failed",
        "failure",
        "non compliant",
        "non-compliant",
        "prestazione",
        "rendimento",
        "limite",
        "garant",
        "conforme",
    ]
    technical_bad_kw = [
        "below",
        "above",
        "failed",
        "failure",
        "not",
        "non ",
        "issue",
        "problem",
        "problema",
        "hors",
        "écart",
        "ecart",
    ]
    if any(k in low for k in technical_kw) and any(k in low for k in technical_bad_kw):
        found.append(
            FindingSpec(
                "AGENT_TECHNICAL_RISK",
                "TECHNICAL",
                "HIGH",
                "La comunicazione segnala un possibile problema tecnico o di performance",
                "La mail contiene elementi che possono indicare un problema tecnico o uno scostamento rispetto alle prestazioni attese. Va verificato prima di registrarlo nella commessa.",
                _evidence(text, technical_kw),
                "Aprire una verifica tecnica con evidenze, owner e data di risposta al cliente",
                project.pm_owner,
                0.89,
            )
        )

    # Deduplicate same finding type within one message.
    dedup = {}
    for item in found:
        dedup[item.finding_type] = item
    return list(dedup.values())


def _fingerprint(project_id: int, communication_id: int, finding_type: str) -> str:
    raw = f"{project_id}:{communication_id}:{finding_type}".encode()
    return "AI:" + hashlib.sha1(raw).hexdigest()[:24]


def analyze_project(db: Session, project: Project) -> dict:
    started = utcnow()
    created = 0
    updated = 0
    messages = 0
    for comm in project.communications:
        messages += 1
        for spec in analyze_communication(project, comm):
            fp = _fingerprint(project.id, comm.id, spec.finding_type)
            finding = db.query(AgentFinding).filter(AgentFinding.fingerprint == fp).first()
            if finding is None:
                finding = AgentFinding(
                    project_id=project.id,
                    communication_id=comm.id,
                    fingerprint=fp,
                    finding_type=spec.finding_type,
                    dimension=spec.dimension,
                    severity=spec.severity,
                    title=spec.title,
                    summary=spec.summary,
                    evidence=spec.evidence,
                    extracted_date=spec.extracted_date,
                    extracted_amount=spec.extracted_amount,
                    suggested_action=spec.suggested_action,
                    suggested_owner=spec.suggested_owner,
                    confidence=spec.confidence,
                    status="NEW",
                    source_ref=comm.source_ref or f"communication:{comm.id}",
                )
                db.add(finding)
                created += 1
            else:
                # Preserve human review state, refresh only machine-generated content.
                finding.dimension = spec.dimension
                finding.severity = spec.severity
                finding.title = spec.title
                finding.summary = spec.summary
                finding.evidence = spec.evidence
                finding.extracted_date = spec.extracted_date
                finding.extracted_amount = spec.extracted_amount
                finding.suggested_action = spec.suggested_action
                finding.suggested_owner = spec.suggested_owner
                finding.confidence = spec.confidence
                finding.source_ref = comm.source_ref or f"communication:{comm.id}"
                updated += 1
    run = AgentRun(
        project_id=project.id,
        engine=ENGINE_NAME,
        status="COMPLETED",
        messages_analyzed=messages,
        findings_created=created,
        findings_updated=updated,
        started_at=started,
        completed_at=utcnow(),
    )
    db.add(run)
    db.commit()
    return {"messages": messages, "created": created, "updated": updated, "engine": ENGINE_NAME}


def analyze_all_projects(db: Session) -> dict:
    totals = {"projects": 0, "messages": 0, "created": 0, "updated": 0}
    for project in db.query(Project).all():
        result = analyze_project(db, project)
        totals["projects"] += 1
        totals["messages"] += result["messages"]
        totals["created"] += result["created"]
        totals["updated"] += result["updated"]
    return totals
