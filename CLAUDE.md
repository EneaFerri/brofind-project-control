# CLAUDE.md — Brofind Project Control

Cockpit di controllo commesse Brofind: **Project Monitoring, Control and Coordination Layer** sopra i sistemi esistenti (Galileo ERP, Outlook, file server, planner). Osserva, confronta, segnala e coordina; non esegue i processi.

## Stato

- Baseline: **v0.3.8.1** (tag `v0.3.8.1-baseline`) — FastAPI + SQLAlchemy + Jinja2, SQLite.
- Corrente: **v1.0.0** (tag `v1.0.0`) — interfaccia V1 sul modello v0.3.8.1; gap in `docs/v1/IMPLEMENTATION_GAPS.md`. Le slice successive escono come `v1.x`.
- Obiettivo in corso: migrazione a **Usable Control Cockpit V1** secondo `docs/authority/` e i mockup `docs/visuals/`.
- Target di esercizio: applicazione su rete aziendale per utenti brofind.com, con accesso per ruolo (ruoli configurabili, autorizzazione lato server).

## Ordine di autorità

1. `docs/authority/01_USABLE_CONTROL_COCKPIT_V1_PRODUCT_SCOPE_FREEZE_v1.0.md` (Product & Scope Freeze, FROZEN).
2. `docs/authority/02_…` (Monitoring Layer / Work Execution Boundary) e `04_ASTRA_AUTHORITY_AND_BOUNDARIES.md`.
3. Contratti di interazione / dati / accettazione: proposte finali in `docs/v1/03…05` (le bozze originali restano in `docs/authority/drafts/`). Piano, ADR e decisioni aperte in `docs/v1/`.
4. `05_SHARED_UI_SHELL_CONTRACT_V1.md` + `06_VISUAL_FREEZE_MANIFEST_FINAL.md` + gli 8 mockup in `docs/visuals/` (uno canonico per superficie).
5. Piano di implementazione approvato.
6. Codice.

Un livello inferiore non ridefinisce silenziosamente uno superiore. Se un mockup non è implementabile con i dati disponibili, segnalare **IMPLEMENTATION GAP**: non riprogettare la schermata. Nuove richieste vanno classificate: IN PATH / MODEL GAP / CHANGE REQUEST / OUT OF SCOPE.

## Regole inderogabili

- **READ MANY, WRITE LITTLE**: le fonti ufficiali sono read-only; il cockpit scrive solo il proprio layer operativo (finding, Attention, Criticità, Attività, decisioni, conferme). Mai mutare dati sorgente.
- Nessun valore inventato; nessun forecast preciso senza dati che lo supportino.
- Dati mancanti / stale / incerti sono visibili (grigio), mai rappresentati come sani (verde).
- Attention ≠ Criticità ≠ Attività. Chiudere un'Attività non risolve la Criticità. Conversazione ≠ Outcome. Change Item ≠ Criticità.
- L'AI è assistiva: può estrarre, confrontare, spiegare, proporre. Non sceglie fornitori o soluzioni tecniche, non autorizza costi, non modifica obblighi contrattuali, non chiude decisioni. Una proposta AI diventa fatto solo dopo conferma umana.
- Storia e provenienza (fonte, data, autore, motivo) sempre preservate.
- Autorizzazione dei workflow lato server, non solo nascondendo pulsanti in UI.
- Valori dei mockup = fixture visive, mai dati di produzione.

## Debiti noti

- **AD-001**: autorizzazione del ciclo di vita lato server incompleta (es. `POST /api/actions/{id}/status` consente `CLOSED` saltando la validazione). Si chiude nella slice S1.
- **AD-002**: il re-import di uno snapshot con la stessa identità può alterare la storia.
- Eccezioni hard-coded per la commessa `9028` in `app/confidence.py` e `app/serializers.py`.

## Riservatezza

Il repository potrà diventare pubblico. Non committare dati reali di clienti, numeri d'ordine reali, nomi di colleghi o documenti interni. La commessa `9028` è un pilota **anonimizzato** (importi reali, riferimenti fittizi `PO-PILOT-*`). Lo studio AS-IS dei processi resta fuori dal repo.

## Lingua

UI in italiano (eccetto le etichette di navigazione canoniche del Shared UI Shell Contract). Documentazione di progetto in italiano.

## Comandi

```bash
./start_demo.sh                       # macOS/Linux, Python 3.13–3.15, runtime demo su :8080
start_demo.bat                        # Windows
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest            # usa DB isolato sotto data/test
.venv/bin/ruff check . && .venv/bin/ruff format --check .
BROFIND_RUNTIME=development .venv/bin/alembic revision --autogenerate -m "..."   # ogni modifica di schema
```

- Codice: router in `app/routers/`, dati delle superfici V1 in `app/cockpit_views.py`, ora corrente con `app.clock.utcnow()`, versione solo in `pyproject.toml`.
- UI: ogni pagina di commessa estende `templates/project_base.html` (header, navigazione, drawer Fonti/AI/Contratto/Affidabilità); componenti in `templates/_macros.html`; nessuna libreria frontend esterna. Dato mancante → `ui.nd()`, mai verde.
- Fine riga LF (vedi `.gitattributes`); `demo/b1/` non va mai modificato (verificato da `SHA256SUMS`).

Runtime e database: `docs/DEMO_RUNTIME.md`. Python supportato: **3.13, 3.14, 3.15** (nuove dipendenze: solo se hanno wheel per tutte e tre, niente build locali sul PC demo).
