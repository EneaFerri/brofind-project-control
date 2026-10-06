# 01 — Baseline → Target: gap analysis

**Stato:** PROPOSTA — da approvare
**Data:** 2026-10-06
**Baseline:** v0.3.8.1 + Demo B1 (tag `v0.3.8.1-baseline`, commit `b25995f`)
**Target:** Usable Control Cockpit V1 (`docs/authority/01_…PRODUCT_SCOPE_FREEZE`) con grafica degli 8 mockup canonici (`docs/visuals/`). Rilascio come **v1.0**.

Corrisponde alle attività A19 (baseline bootstrap) e A20 (gap analysis) della checklist Astra.

---

## 1. Baseline riconciliata (A19)

| Voce | Valore |
|---|---|
| Repository | locale, inizializzato da `Brofind_Project_Control_DEMO_FINAL` |
| Storia precedente | **non disponibile**: la storia Git su Windows (`demo-final-polish`, tag `demo-stable-2026-09-27`) non è stata importata |
| Stack | Python 3.13, FastAPI 0.128, SQLAlchemy 2.0, Jinja2, JS vanilla, SQLite |
| Test | **87/87 PASS** (Python 3.13.x) |
| Runtime | demo / development / test isolati (`app/config.py`); avvio robusto su Windows, `start_demo.sh` su macOS |
| Dati demo | 12 commesse simulate (P-26001…012), pilota 9028 (anonimizzato), caso guidato DEMO-B1-001 |

### Documenti di autorità mancanti

I documenti recuperati citano autorità che **non sono presenti** nel pacchetto:

| Riferimento | Citato in | Impatto |
|---|---|---|
| WORKFLOW FREEZE — Gestione operativa Cockpit v1.1 | `02_…MONITORING_LAYER` | semantica Criticità/Attività |
| OPERATIONAL CONTROL FREEZE v1.0 (management objective, coverage, correction path) | `02_…` | Criticità, copertura gestionale |
| COLLABORATION FREEZE v1.0 | `02_…` | Conversazioni, messaggistica |
| UI FREEZE — Gestione operativa v1.0 | `02_…`, `03_…` | superfici Criticità/Attività/Conversazioni |
| DEC-019…DEC-026 (in particolare DEC-020, 021, 025, 026) | `03_UI_GOVERNANCE` | regole UI |
| `AGENTS.md`, `docs/DECISIONS.md`, `docs/PROJECT_STATE.md` | `02_…` | sostituiti da `CLAUDE.md`; DEC-001…018 sono riportati integralmente in `02_…` |
| Stage 1 economico / proiezione `economic_v1`, tentativo Stage 2 | `03_UI_GOVERNANCE` §9 | lavoro non presente in questa baseline |

Vedi `07_OPEN_DECISIONS.md` (OD-01).

---

## 2. Cosa esiste e come si riusa

| Componente baseline | File | Destino V1 |
|---|---|---|
| Configurazione runtime, health, DB isolati | `app/config.py`, `app/db.py`, `scripts/*.ps1` | **Mantieni** |
| Source Center (scansione cartelle, hash, stato, import log) | `app/source_center.py`, `ProjectSourceScan/File/Import` | **Mantieni** → base di *Source Configuration* e *Source Evidence* |
| Lettori PDF/DOCX/EML/MSG | `app/source_readers.py` | **Mantieni** |
| Catena SOURCE → EXTRACTED → CONFIRMED → OPERATIONAL | `ProjectExtractedField`, `app/ai_analysis.py` | **Mantieni** il modello; l'estrazione regex resta un provider tra gli altri |
| Snapshot economico Galileo per VdA/CDA con controlli di quadratura | `ProjectControlSnapshot/Line`, `app/control.py`, `app/b1_control_adapter.py` | **Mantieni ed estendi** → Economics V1 (forecast, freschezza, storico) |
| Classificazione saving (budget residuo / candidato / consolidato) | `CockpitDecision VDA_SAVING` | **Mantieni** |
| Ciclo Action: OPEN → IN_PROGRESS → PENDING_VALIDATION → CLOSED, owner persona/reparto, richiedente | `Action`, `ActionMessage` | **Evolvi** in *Attività* V1 (stati del freeze, `expected_result`, `purpose`, Outcome separato) |
| Finding AI confermabili/scartabili, deduplica per fingerprint | `AgentFinding`, `app/intelligence.py`, `app/workflow.py` | **Evolvi** in *proposte AI* tracciate (storico dell'esito) |
| Rules engine con fingerprint e auto-resolve | `app/rules.py` | **Evolvi** in motore di *Attention* per dominio |
| `CockpitDecision` (layer operativo scrivibile) | `app/models.py` | **Mantieni**, generalizzato per override e riconciliazioni |
| Contract Baseline (condizioni FROZEN / DA CHIARIRE) | `app/serializers.py` | **Riusa** come input di Billing Event e sequenze contrattuali |
| Confidence per dominio | `app/confidence.py` | **Rifattorizza**: rimuovi eccezioni 9028; diventa *Fonte / Freschezza / Affidabilità* |
| UI (template, CSS, JS) | `templates/`, `static/` | **Sostituisci** con shell e superfici V1 |
| Modello `BudgetLine/ETC`, `Milestone` semplice, `Issue`, `Alert` | `app/models.py` | **Sostituisci / migra** (vedi §3) |
| Login a cookie e 4 ruoli fissi | `app/security.py` | **Sostituisci** (ADR-004, ADR-005) |
| Import workbook generico (12 fogli) | `app/importer.py` | **Ritira** dopo migrazione dei dati demo su fixture V1 |

---

## 3. Gap per superficie

Legenda: ✅ riusabile · ◐ parziale · ❌ assente · **GAP** = dato o regola necessari al mockup ma non disponibili.

### V01 — Portfolio
| Elemento mockup | Baseline | Note |
|---|---|---|
| Contatori critiche / in attenzione / in linea / non attive | ◐ | oggi priorità CRITICAL/HIGH/MEDIUM/OK/NO_DATA con *attention score* opaco, vietato dal freeze §20 |
| Filtri stato (Tutte, In corso, In avvio, Chiuse, Archiviate) | ❌ | manca il concetto di commessa archiviata/riattivabile |
| Fase commessa (Lead, Offerta, Engineering, Procurement, Esecuzione, Service, Chiusura) | ❌ | oggi `status` tecnico; serve vocabolario di fase configurabile |
| 7 semafori di dominio | ◐ | oggi 5 dimensioni (FINANCE, BUDGET, TECHNICAL, SCHEDULE, CONTRACT) |
| Principale esposizione causa → conseguenza | ◐ | oggi `_primary_attention`; manca il raggruppamento per causa comune |
| Ordinamento per priorità di controllo / per dominio prima della paginazione | ◐ | |
| Esporta elenco | ❌ | |

### V02 — Panoramica commessa
| Elemento | Baseline | Note |
|---|---|---|
| Header condiviso (codice, cliente, descrizione, stato, PM, offerta, inizio, consegna) | ◐ | mancano offerta, data inizio contratto e consegna prevista strutturate |
| Striscia domini con contatori | ◐ | |
| Principale esposizione con "In gestione: …" e prossimo aggiornamento | ❌ | richiede Criticità con owner e prossimo aggiornamento |
| Prossimo gate con readiness, blocker, target/forecast | ❌ | richiede Master Planner |
| Fonti / Storico / drawer AI | ◐ / ❌ / ❌ | |

### V03 — Master Planner
❌ **Interamente nuovo.** Milestone con baseline/target/forecast/actual, fasi, readiness (PRONTA / NON PRONTA / DA VERIFICARE), dipendenze verso oggetti di dominio, Control Checkpoint, propagazione "da verificare" a valle senza spostare le date. Riusa solo `Milestone` come punto di partenza per la migrazione.

### V04 — Economics
| Elemento | Baseline | Note |
|---|---|---|
| Valore contratto, Budget, Speso, Variazione, Varianti | ✅ | da snapshot + `CustomerOrder` + `ChangeRequest` |
| Forecast finale e Margine previsto | ◐ | oggi volutamente non calcolato senza ETC; serve metodologia configurabile (freeze §15.2) e proposta AI cost-to-complete confermata dall'utente |
| Andamento costi nel tempo | **GAP** | serve storico di snapshot datati (oggi uno solo per commessa; AD-002) |
| Speso per categoria / Variazione per categoria | **GAP** | le macro-famiglie di costo **non sono congelate**; si possono mostrare per VdA o per natura VdA (`procurement.VDA_NATURE`) in attesa di decisione |
| Impegni aperti per fornitore con consegna prevista | **GAP** | l'estrazione Galileo attuale non contiene righe d'ordine per fornitore |
| Principali scostamenti con causa e dominio | ◐ | causa da collegare a Change Item / Procurement Item |

### V05 — Technical
❌ **Nuovo.** Technical Decision/Checkpoint (stato, chi conferma, scadenza, impatto, evidenze), segnali di allineamento, rischi tecnici, decisioni confermate, fonti disponibili. Riusa `ProjectRequirement` + finding engineering della 9028 come primi esempi.

### V06 — Procurement
◐ La baseline ragiona **per VdA** (natura, stato acquisti, rischio). Il target ragiona per **Procurement Item** (fornitura logica, anche prima dell'ordine) con Stadio, Prossima scadenza RFQ/Ordine, Need Date, Supplier Promise, Current Forecast, Stato controllo, Impatto, fornitore. Gli Item vanno collegati a VdA e ordini Galileo. Lead time per categoria e soglie di freschezza **non congelati** → parametri configurabili con default dichiarati.

### V07 — Documents
❌ **Nuovo.** Document Item logico (ATTESO / DISPONIBILE / DA AGGIORNARE / DA VERIFICARE / N/A), Minimum Document Set da template, collegamento a milestone, evidenze dalla cartella commessa (Source Center già scansiona `Documenti/`).

### V08 — Billing & Payment
◐ Esistono `Invoice` (importo, incassato, scadenza) e milestone con `invoice_required`. Mancano **Billing Event** contrattuale (% / importo, trigger/evidenza, data di maturazione, stato maturazione), collegamento evento ↔ fattura Galileo, tolleranza configurabile, metodo di avanzamento per il Payment (**non congelato**). Il caso B1 contiene già 4 milestone di fatturazione nel contratto: buon primo fixture.

### Criticità · Attività · Conversazioni · Storico
◐ `Action`/`ActionMessage` coprono parte di Attività e Conversazioni. Mancano: Criticità come oggetto distinto dall'Attention, Outcome strutturato, `expected_result` obbligatorio, `purpose` EXECUTION/DECISION, Storico leggibile a livello commessa (History Event), Change Item con matrice impatti. **Bloccato in parte dai freeze mancanti** (§1).

### Trasversali
| Capacità V1 (freeze §27) | Baseline |
|---|---|
| Source / Freshness / Confidence per dato | ◐ fonte sì; freschezza no |
| Reconciliation (osservato vs riconciliato) | ❌ |
| History / Audit Trail | ❌ (solo timestamp e `created_by` sparsi) |
| Project Parties & Roles | ❌ (solo `pm_owner`, `sales_owner` testuali) |
| Settings / Override (globale → commessa → item) | ❌ |
| Project Opening / Scope Profile / KOM | ◐ creazione commessa e review contratto B1 |
| Post-completion residui | ❌ |
| Autenticazione / autorizzazione per ruolo | ❌ demo a cookie; AD-001 aperto |

---

## 4. Debiti tecnici da chiudere durante la migrazione

| ID | Debito | Dove si chiude |
|---|---|---|
| AD-001 | autorizzazione dei cambi di stato solo lato UI (es. `POST /api/actions/{id}/status` → `CLOSED` senza validazione) | Slice S1 (permessi server-side) |
| AD-002 | re-import snapshot con stessa identità altera la storia | Slice S4 (snapshot immutabili e versionati) |
| TD-01 | eccezioni `if project.code == "9028"` in `confidence.py`, `serializers.py` | Slice S0 / S4 |
| TD-02 | `main.py` monolitico (900 righe, 40+ endpoint) | Slice S0 |
| TD-03 | schema creato con `create_all`, nessuna migrazione | Slice S0 (Alembic) |
| TD-04 | `recompute_alerts` scrive sul DB a ogni GET | Slice S3 (ricalcolo su evento/import) |
| TD-05 | `datetime.utcnow()` deprecato (~6.000 warning) | Slice S0 |
| TD-06 | *attention score* numerico opaco nel Portfolio | Slice S3 |
| TD-07 | semaforo verde basato sola presenza del dato, senza freschezza | Slice S3 |
| TD-08 | asset frontend: nessuna libreria grafici, nessun design token | Slice S2 |

---

## 5. Incoerenze tra mockup e regole (da applicare in implementazione, senza riaprire il freeze)

Già risolte dal Shared UI Shell Contract / A14:
- sidebar solo globale; `Control` rimosso; nessun `Apri in nuova scheda`;
- un solo pulsante AI nella shell (il pulsante `AI` dentro Economics va rimosso);
- Billing e Payment in un'unica superficie;
- refusi (`Ecoments` → `Economics`); etichetta `Sintesi` → `Overview`.

Prompt AI d'esempio **da non implementare** (violano l'AI boundary):
- "Quali alternative abbiamo per lo scambiatore in caso di ritardo?" (V06);
- "Quali azioni consiglieresti per ridurre il rischio?" (V08).

Da decidere (vedi `07_OPEN_DECISIONS.md`):
- etichette di navigazione in inglese (Shell Contract, A14) vs regola Italiano-first e glossario (`03_UI_GOVERNANCE` §7);
- `03_UI_GOVERNANCE` indica Figma come autorità visiva; A14 la sostituisce con gli 8 PNG.
