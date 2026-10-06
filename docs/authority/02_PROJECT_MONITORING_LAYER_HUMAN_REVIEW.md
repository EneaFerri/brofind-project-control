# Project Monitoring Layer — Human Review Report

Repository: `C:\Cockpit\Brofind_Project_Control_V0_3_8_1 - review`

This report is read-only with respect to the repository. It records the current content and Git state at review time.

## Current `docs/ARCHITECTURE.md`

```markdown
# Architecture V0

> **NORMATIVE ARCHITECTURE AUTHORITY.** For current documentation precedence, see `AGENTS.md` and `docs/PROJECT_STATE.md`. This document states architectural intent and boundaries; it does not claim that every target or approved future contract is implemented in the v0.3.8.1 baseline.

## Source of truth

External authoritative systems remain authoritative. Cockpit observes, imports, normalizes, derives, and manages operational state without silently overriding external truth. This implements the governing principle: **READ MANY, WRITE LITTLE**.

## Data authority taxonomy

The following conceptual categories describe authority and provenance; they do not introduce schema fields:

- **SOURCE / EXTERNAL AUTHORITATIVE:** facts owned by an external system or original source.
- **IMPORTED / REPLICA:** Cockpit’s normalized representation of source data.
- **CONFIRMED BY USER:** a human confirmation in the Cockpit operational layer.
- **CALCULATED / DETERMINISTIC:** a reproducible result from defined control logic.
- **INFERRED / AI:** an AI-derived finding, classification, summary, or proposal.
- **OPERATIONAL WORKFLOW STATE:** Cockpit-owned state for work, review, and accountability.

## Domain separation

Source data, normalized project data, deterministic controls, AI findings, operational workflow, and UI are separate concerns. UI is a projection of domain and workflow behavior; it must not introduce workflow semantics by itself.

## Project Monitoring Layer — architectural principle v1.0

The Cockpit is first of all a monitoring and control layer over existing Brofind processes. Its canonical monitoring sequence is:

`PLAN / TARGET / BASELINE → OBSERVED REALITY → FORECAST → VARIANCE → ATTENTION → optional CRITICITÀ → optional ATTIVITÀ`

Normal project progress is not workflow activity. A healthy project can contain many monitored domain objects and few, or no, Criticità or Attività.

Monitoring applies to distinct domain objects, including Procurement Item, Milestone, Budget Position, Contract Obligation, Deliverable, Payment, and Technical Requirement. These objects remain distinct: this principle does not introduce a generic universal domain object. They share a conceptual monitoring projection/contract containing `TARGET / BASELINE`, `OBSERVED`, `FORECAST`, `VARIANCE`, `SOURCE / PROVENANCE`, `CONFIDENCE`, and `ATTENTION`.

`VARIANCE` does not automatically mean Criticità; `ATTENTION` does not automatically mean Criticità; and Criticità does not automatically mean Attività. An Attività is created only when explicit human work, verification, clarification, collaboration, or a formal decision is required. Rules and AI must not automatically create definitive workflow actions unless a future approved rule explicitly authorizes it.

The product model therefore distinguishes normal project monitoring, exception management, and explicit collaboration workflow:

`DOMAIN OBJECT → monitoring state → variance / attention → optional Criticità → optional Attività → Outcome → re-evaluate monitored reality`

Criticità and Attività must not become containers for normal project progress. The Project Overview and future UI must derive from monitored project state first, with exceptions emerging from that state; this principle does not redesign the UI.

## Work Execution Boundary

The Cockpit observes, compares, updates, forecasts, signals, coordinates explicit requests for work, records structured outcomes, and preserves evidence and audit context. It does not replace ERP, procurement execution tools, technical engineering work, detailed planning tools, specialist calculations, commercial negotiation tools, or ordinary corporate communication tools.

For each explicit work request, the Cockpit must know the required result, responsible party, due date, expected result, obtained result, and supporting evidence. It does not normally host the detailed specialist reasoning or process used to obtain that result; that work remains in the appropriate execution system or professional context.

Formal authorization decisions remain valid Cockpit Decision Activities where responsibility and audit must be tracked. This boundary does not authorize new workflow objects, a specialist workstation, or baseline implementation.

## Operational control semantics (approved future contract)

The Operational Control Freeze v1.0 formalizes two future domain concepts in the Cockpit operational layer: `Criticità.management_objective` and `Activity.purpose = EXECUTION | DECISION`. This is a conceptual contract only: it does not claim a schema field, migration, API, or baseline implementation.

Management Coverage is a deterministic derived projection of Criticità state and linked Activity states, not an autonomous lifecycle or manually editable truth. Correction Path is the coordinated projection of a Criticità management objective, linked Activities, obtained Outcomes, and next necessary work; it is not an entity, owner, lifecycle, dependency graph, or speculative work plan. Activity purpose uses the existing Activity lifecycle. Role-aware Attention is a deterministic, explainable, deduplicated projection and is neither RBAC, an AI score, nor a domain entity.

## AI authority and confidence

AI may detect, classify, summarize, propose, and suggest. AI may not alter external authoritative facts, silently close deterministic criticità, override human workflow authority, or autonomously perform administrative overrides.

Evidence confidence and AI-finding confidence are distinct concepts. No canonical numeric threshold or calibration is currently defined; calibration remains unresolved.

## Implementation-status boundary

Architecture targets, baseline implementation, and future integrations must be distinguished. Live Galileo, Pipedrive, Microsoft Graph, and FileServer/EDMS adapters are targets unless they are explicitly documented as implemented in the current baseline.

## Snapshot and authorization boundaries

Historical source/control snapshots must not be silently overwritten. Current same-identity snapshot re-import behavior is a known architecture debt (AD-002), not resolved behavior.

Workflow authorization must ultimately be enforced server-side, not only by UI visibility. Current incomplete server-side lifecycle authorization is known architecture debt AD-001, not an accepted security boundary.

## Layer
1. Source adapters: mock oggi, reali domani.
2. Domain/Data Hub: modello normalizzato di commessa.
3. Rules Engine: controlli deterministici.
4. Agent layer: eventi inferiti da comunicazioni/documenti, sempre tracciati e validabili.
5. API: contratto stabile tra backend e UI.
6. UI: portfolio, attention queue, project detail.

## Adapter target
- GalileoAdapter: da definire dopo verifica API/DB/export Sanmarco.
- PipedriveAdapter: REST API/webhook.
- OutlookAdapter: Microsoft Graph, con scope limitato alle superfici di progetto autorizzate.
- FileServerAdapter: lettura controllata delle cartelle commessa / gateway.

## Regola di autorità
ERP/contratto > dati approvati > comunicazioni > inferenze AI.
L'AI non modifica automaticamente dati contabili o contrattuali.

## Budget
Formula target di forecast: `Actual + Commitment residuo + ETC`.

Nella fase attuale il cockpit **non dipende da un ETC strutturato compilato dai PM**: usa prima dati oggettivi (consuntivo, ordini residui, stato acquisti) e dichiara l'incertezza quando il costo futuro non è determinabile. L'ETC potrà essere aggiunto in seguito solo con provenienza tracciata (MANUAL, CALCULATED, ERP/AI validato).

## RBAC
DIRECTOR: tutte le commesse.
SALES: sales_owner = owner_key.
PM: pm_owner = owner_key.
In produzione il mapping utente/ruolo sarà delegato a Entra ID.

## Project Intelligence V0.3
`Communication -> Intelligence Engine -> AgentFinding -> Rules Engine -> Alert -> Human Review -> Action`

`AgentFinding` è il boundary tra AI e dominio. L'AI può proporre data, importo, rischio e azione, ma non scrive direttamente nei master data della commessa.

## Control Data Foundation (V0.3.3)

Il nuovo dominio `ProjectControlSnapshot` separa il controllo economico operativo dal vecchio modello demo `BudgetLine/ETC`.

Flusso previsto:

`Galileo / export JMRP + ordini -> Adapter -> Snapshot storico -> Aggregazione VdA/CDA -> Rules Engine -> Cockpit`

Regole architetturali:

- ogni import crea/aggiorna uno snapshot datato, senza sovrascrivere la storia precedente;
- il livello di analisi è `Project -> VdA -> Analysis Center`;
- il cockpit aggrega i CDA prima del confronto VdA/budget;
- i dati sorgente sono considerati read-only;
- il forecast ETC non è richiesto per calcolare gli indicatori oggettivi di impegno;
- l'integrazione diretta con Galileo potrà sostituire l'Excel mantenendo invariato il dominio applicativo.

Interfaccia dati minima attesa dall'adapter Galileo:

- baseline budget;
- operational budget;
- orders total (JMRP);
- orders total + residual (interrogazione ordini);
- received materials/services;
- labor cost;
- overhead;
- purchase complete flag;
- VdA code/name;
- Analysis Center code;
- snapshot timestamp and source identity.


## Evidence-driven Control (V0.3.4)

Nuove entità / evidenze:

- `CustomerOrder`: PO cliente base/extra, valore netto, IVA, termini pagamento, Incoterm, riferimento offerta e source_ref;
- `ChangeRequest`: budget costo e valore cliente dell'extra, con source_ref;
- budget bridge: `baseline + extra approvati -> budget teorico autorizzato -> budget operativo Galileo`;
- stato VdA separato in `economic_status` e `procurement_status`;
- data availability: assenza di fonte = `N/D`, non `GREEN`.

Regola budget candidata:

`gross local overruns` confrontato con `headroom on purchase-closed VdA`, mantenendo separato il budget ancora aperto. La copertura non è automaticamente classificata come saving finale.


## UX / semantic status contract (V0.3.5)

Il colore non è decorativo ma parte del contratto informativo:

- `GREEN`: fonte disponibile e situazione valutata regolare;
- `YELLOW`: situazione da presidiare o incertezza significativa;
- `RED`: condizione negativa concreta che richiede intervento;
- `ND`: fonte/dato non disponibile, sempre neutro;
- `PARTIAL`: copertura dati incompleta, neutra e distinta da un alert.

Principio di composizione delle schermate: **sintesi -> eccezioni -> dettaglio -> evidenza**. Un problema locale non eredita automaticamente la propria severità alla commessa; l'aggregazione di portafoglio e progetto usa regole esplicite e spiegabili.


## V0.3.8 — Read Many, Write Little

Il sistema è diviso concettualmente in due superfici dati.

### 1. Project Data Hub / Read Model
Replica normalizzata e storicizzata delle sorgenti autorevoli. Dal cockpit è **read-only**.

`Galileo / Pipedrive / Outlook / Contract & PO / Planning / File server-EDMS -> Adapter -> Read Model`

Il cockpit non espone comandi per modificare ordini, fatture, budget ERP, planning ufficiale, documenti, email sorgente o contratto originale.

### 2. Cockpit Operational Layer
Contiene soltanto oggetti propri del processo di controllo:

- finding, alert, action e escalation;
- note/thread operativo e risposte registrate;
- review e validazioni;
- `CockpitDecision` per interpretazioni operative congelate e classificazioni;
- stato di conferma/scarto dei finding;
- classificazione saving;
- Contract Baseline operativa.

Regola di scrittura:

`WRITE_ALLOWED = oggetto nato nel cockpit o interpretazione operativa tracciata`

`WRITE_FORBIDDEN = master data o documento appartenente a una sorgente ufficiale`

Una discrepanza non viene corretta nel Read Model: genera un data-quality finding. La correzione avviene nella sorgente autorevole e viene acquisita al sync successivo.

### UI contract
Ogni modifica consentita deve essere riconoscibile come azione cockpit (`Conferma`, `Scarta`, `Crea azione`, `Nota`, `Registra risposta`, `Congela interpretazione`, `Conferma saving`, `Chiudi review`). Per i dati sorgente l'azione corretta è `Vedi evidenza` o, in futuro, `Apri nella sorgente`.
```

## Current `docs/DECISIONS.md`

```markdown
# Decision register

Compact ADR-style register. “Future approved” decisions are binding functional targets but are **not implemented in the v0.3.8.1 baseline** unless their implementation status is explicitly changed by a higher-precedence approved decision according to `AGENTS.md`.

## DEC-001

- **Decision:** External source systems remain authoritative; Cockpit does not silently replace source truth.
- **Status:** Accepted / current architecture.
- **Rationale:** Preserve provenance and the READ MANY, WRITE LITTLE boundary.
- **Impact:** Corrections occur in the authoritative source; Cockpit imports, normalizes, derives, and manages its own operational state.
- **Supersedes / Superseded by:** None.

## DEC-002

- **Decision:** Criticità and Attività have independent lifecycles.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** A work item and the underlying condition are different operational objects.
- **Impact:** Their states and transitions must be modeled independently.
- **Supersedes / Superseded by:** Supersedes any implicit coupling in historical workflow descriptions.

## DEC-003

- **Decision:** Closing an Attività does not automatically resolve a Criticità.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** Work completion is not proof that the source condition no longer exists.
- **Impact:** Resolution follows the Criticità rules, not task closure alone.
- **Supersedes / Superseded by:** None.

## DEC-004

- **Decision:** Responsible department and personal executor are distinct concepts.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** Organizational accountability persists when execution is delegated.
- **Impact:** Assignment must preserve department responsibility.
- **Supersedes / Superseded by:** None.

## DEC-005

- **Decision:** Expected result is mandatory for Attività.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** A task requires a verifiable intended outcome.
- **Impact:** Attività creation requires an expected result.
- **Supersedes / Superseded by:** None.

## DEC-006

- **Decision:** Conversation and structured outcome are distinct.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** Messages are evidence of communication, not a structured work result.
- **Impact:** Messages do not substitute for outcome capture or state transition.
- **Supersedes / Superseded by:** None.

## DEC-007

- **Decision:** UI derives from workflow and cannot define workflow semantics.
- **Status:** Accepted / current architecture.
- **Rationale:** Domain and workflow contracts must remain consistent across interfaces.
- **Impact:** UI-only changes cannot introduce lifecycle rules.
- **Supersedes / Superseded by:** None.

## DEC-008

- **Decision:** AI is advisory/proposal-capable but not workflow authority.
- **Status:** Accepted / current architecture.
- **Rationale:** Human authority and source provenance cannot be silently overridden.
- **Impact:** AI may detect, classify, summarize, propose, and suggest; it cannot autonomously administer or close deterministic conditions.
- **Supersedes / Superseded by:** None.

## DEC-009

- **Decision:** Procurement Planning is a separate module using shared operational objects.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** Procurement has its own planning responsibilities while sharing Criticità and Attività.
- **Impact:** It may generate those shared objects without becoming their workflow authority.
- **Supersedes / Superseded by:** None.

## DEC-010

- **Decision:** Management overrides are exceptional and audited.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** Exceptional direction must remain accountable and distinct from normal workflow.
- **Impact:** Each override records actor, time, and reason.
- **Supersedes / Superseded by:** None.

## DEC-011

- **Decision:** Historical snapshots should not be silently overwritten.
- **Status:** Accepted / current architecture; implementation debt AD-002 remains open.
- **Rationale:** Control results require durable source and time provenance.
- **Impact:** Snapshot history is an architectural invariant; same-identity re-import behavior requires future remediation.
- **Supersedes / Superseded by:** None.

## DEC-012

- **Decision:** Workflow authorization belongs server-side even if UI hides actions.
- **Status:** Accepted / current architecture; implementation debt AD-001 remains open.
- **Rationale:** UI visibility is not an authorization boundary.
- **Impact:** Lifecycle authorization ultimately requires server-side enforcement.
- **Supersedes / Superseded by:** None.

## DEC-013

- **Decision:** Management Coverage is a derived projection of Criticità state and linked Activity states; it is not an autonomous lifecycle.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** Coverage must describe active handling without changing the condition lifecycle.
- **Impact:** Coverage is deterministic and separate from severity, conditions, and attention flags.
- **Supersedes / Superseded by:** None.

## DEC-014

- **Decision:** Correction Path is a coordinated representation of Activities associated with a Criticità and its Management Objective; it is not a new workflow object.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** Coordination must not introduce a parallel lifecycle, owner, dependency graph, or speculative work plan.
- **Impact:** It projects objective, linked Activities, Outcomes, and next necessary work only.
- **Supersedes / Superseded by:** None.

## DEC-015

- **Decision:** Activity has formal purpose `EXECUTION` or `DECISION`; both purposes use the same Activity lifecycle.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** A formal decision is work with accountability, not a parallel entity or workflow.
- **Impact:** The formal decision is recorded in the structured Outcome; closing it does not automatically resolve a linked Criticità.
- **Supersedes / Superseded by:** None.

## DEC-016

- **Decision:** Personal attention relevance is a deterministic and explainable projection of data, responsibility, impact, urgency, and workflow; it is neither RBAC nor an AI score.
- **Status:** Approved future functional contract; not implemented in baseline.
- **Rationale:** The same reality requires role-aware visual priority without opaque ranking or duplicate problems.
- **Impact:** Attention is deduplicated and every item provides a visible explanation.
- **Supersedes / Superseded by:** None.

## DEC-017

- **Decision:** The Cockpit is first a Project Monitoring Layer over distinct domain objects, using a common monitoring projection without replacing those objects with a universal domain object.
- **Status:** Accepted / current architecture; not implemented in baseline.
- **Rationale:** Normal project progress must be monitored as observed reality, forecast, variance, confidence, and attention before it is treated as an exception or workflow.
- **Impact:** The canonical sequence is `PLAN / TARGET / BASELINE → OBSERVED REALITY → FORECAST → VARIANCE → ATTENTION → optional CRITICITÀ → optional ATTIVITÀ`. Variance and attention do not automatically create Criticità; Criticità does not automatically create Attività; Rules and AI cannot create definitive workflow actions without future explicit approval.
- **Supersedes / Superseded by:** Clarifies DEC-002, DEC-003, DEC-013, DEC-015, and DEC-016; does not supersede them.

## DEC-018

- **Decision:** The Cockpit coordinates explicit, auditable work but does not replace the specialist execution systems or processes used to perform that work.
- **Status:** Accepted / current architecture; not implemented in baseline.
- **Rationale:** Control requires accountable requests and verifiable outcomes, not a substitute ERP, engineering, planning, procurement, negotiation, or ordinary communication workstation.
- **Impact:** An explicit Activity is created only for human work, verification, clarification, collaboration, or a formal decision, and records the required result, responsible party, due date, expected result, obtained result, and supporting evidence. Formal authorization decisions remain valid Decision Activities where responsibility and audit are required.
- **Supersedes / Superseded by:** Clarifies DEC-005, DEC-006, DEC-015, and DEC-017; does not supersede them.
```

## Current `docs/PROJECT_STATE.md`

```markdown
# Project state

## Current approved software baseline

- Product: Brofind Project Control v0.3.8.1
- Tag: `demo-stable-2026-09-27`
- Commit: `cd183e2`

## Current active development branch

`demo-final-polish`

Status: active development branch; not itself an approved software baseline.

## Canonical governance recovery

Status: **COMPLETE**.

- Governance reconciliation commit currently present on `demo-final-polish`: `3ef60f9`
- Originating `architecture-recovery` commit: `5452d33c617c7abc282fb5bbae94abc8d7dc0293`

Canonical architecture/governance documentation is now repository-owned and authoritative according to `AGENTS.md`.

## Approved architectural principles

**PROJECT MONITORING LAYER — ARCHITECTURAL PRINCIPLE v1.0** and the **WORK EXECUTION BOUNDARY** are approved architectural principles. They are documentation-level architecture decisions and do not assert implementation in the v0.3.8.1 baseline.

They require the monitoring/product model to remain primary: monitored project state precedes optional exceptions and explicit collaboration workflow.

## Latest approved functional contract

**WORKFLOW FREEZE — GESTIONE OPERATIVA COCKPIT v1.1**

Status: **APPROVED FUTURE FUNCTIONAL CONTRACT — NOT YET IMPLEMENTED IN BASELINE**.

## Latest approved operational control contract

**OPERATIONAL CONTROL FREEZE — CRITICITÀ, COPERTURA GESTIONALE & CORRECTION PATH v1.0**

Status: **APPROVED FUTURE FUNCTIONAL CONTRACT — NOT YET IMPLEMENTED IN BASELINE**.

This contract is subordinate to WORKFLOW FREEZE — GESTIONE OPERATIVA COCKPIT v1.1 and governs operational-control semantics above Collaboration and UI contracts.

## Latest approved collaboration contract

**COLLABORATION FREEZE — GESTIONE OPERATIVA & MESSAGGISTICA v1.0**

Status: **APPROVED FUTURE FUNCTIONAL CONTRACT — NOT YET IMPLEMENTED IN BASELINE**.

This collaboration contract is subordinate to WORKFLOW FREEZE — GESTIONE OPERATIVA COCKPIT v1.1 and governs collaboration semantics above the UI contract.

## Latest approved UI contract

**UI FREEZE — GESTIONE OPERATIVA COCKPIT v1.0**

Status: **APPROVED FUTURE UI CONTRACT — NOT YET IMPLEMENTED IN BASELINE**.

This UI contract is subordinate to WORKFLOW FREEZE — GESTIONE OPERATIVA COCKPIT v1.1, OPERATIONAL CONTROL FREEZE v1.0, and COLLABORATION FREEZE v1.0 and does not assert implementation in the current software baseline.

## Unapproved development delta

The current working tree contains experimental UX changes in:

- `static/app.js`
- `static/style.css`
- `templates/project.html`
- `tests/test_web.py`

Status: **UNAPPROVED / EXPERIMENTAL / NOT CANONICAL**.

These changes must not be interpreted as approved architecture or approved implementation.

## Known architecture debt

- **AD-001 — Server-side lifecycle authorization incomplete.** Workflow authorization is not yet fully enforced server-side.
- **AD-002 — Same-identity snapshot re-import can mutate historical snapshot state.** This conflicts with the snapshot preservation principle.

These debts are recorded only; this document does not propose fixes.

## Current phase

Monitoring/product-model reconciliation under restored canonical architecture governance. Current UI/Figma work must not expand into new functional areas until that reconciliation is complete.

## Next authorized product activity

Real Brofind workflow study, beginning with Procurement AS-IS. This is product analysis only and is not a claim that any approved architectural principle or freeze is implemented in the software baseline.

The analysis must use:

- PROJECT MONITORING LAYER — ARCHITECTURAL PRINCIPLE v1.0;
- WORK EXECUTION BOUNDARY;
- canonical architecture and decisions;

UI/Figma work cannot redefine workflow/domain semantics or expand into new functional areas before the monitoring/product model is reconciled. This authorization does not claim implementation of the architectural principles or existing approved freezes in the baseline.

## Deferred / future

- Full EDMS
- PDM
- Digital Twin
- Advanced procurement module
- Other deferred scope already implied by project history

No implementation commitment is implied by this list.
```

## Exact Git diff — the three requested files only

```diff
diff --git a/docs/ARCHITECTURE.md b/docs/ARCHITECTURE.md
index d7f9aba..ee73eb5 100644
--- a/docs/ARCHITECTURE.md
+++ b/docs/ARCHITECTURE.md
@@ -21,6 +21,32 @@ The following conceptual categories describe authority and provenance; they do n
 
 Source data, normalized project data, deterministic controls, AI findings, operational workflow, and UI are separate concerns. UI is a projection of domain and workflow behavior; it must not introduce workflow semantics by itself.
 
+## Project Monitoring Layer — architectural principle v1.0
+
+The Cockpit is first of all a monitoring and control layer over existing Brofind processes. Its canonical monitoring sequence is:
+
+`PLAN / TARGET / BASELINE → OBSERVED REALITY → FORECAST → VARIANCE → ATTENTION → optional CRITICITÀ → optional ATTIVITÀ`
+
+Normal project progress is not workflow activity. A healthy project can contain many monitored domain objects and few, or no, Criticità or Attività.
+
+Monitoring applies to distinct domain objects, including Procurement Item, Milestone, Budget Position, Contract Obligation, Deliverable, Payment, and Technical Requirement. These objects remain distinct: this principle does not introduce a generic universal domain object. They share a conceptual monitoring projection/contract containing `TARGET / BASELINE`, `OBSERVED`, `FORECAST`, `VARIANCE`, `SOURCE / PROVENANCE`, `CONFIDENCE`, and `ATTENTION`.
+
+`VARIANCE` does not automatically mean Criticità; `ATTENTION` does not automatically mean Criticità; and Criticità does not automatically mean Attività. An Attività is created only when explicit human work, verification, clarification, collaboration, or a formal decision is required. Rules and AI must not automatically create definitive workflow actions unless a future approved rule explicitly authorizes it.
+
+The product model therefore distinguishes normal project monitoring, exception management, and explicit collaboration workflow:
+
+`DOMAIN OBJECT → monitoring state → variance / attention → optional Criticità → optional Attività → Outcome → re-evaluate monitored reality`
+
+Criticità and Attività must not become containers for normal project progress. The Project Overview and future UI must derive from monitored project state first, with exceptions emerging from that state; this principle does not redesign the UI.
+
+## Work Execution Boundary
+
+The Cockpit observes, compares, updates, forecasts, signals, coordinates explicit requests for work, records structured outcomes, and preserves evidence and audit context. It does not replace ERP, procurement execution tools, technical engineering work, detailed planning tools, specialist calculations, commercial negotiation tools, or ordinary corporate communication tools.
+
+For each explicit work request, the Cockpit must know the required result, responsible party, due date, expected result, obtained result, and supporting evidence. It does not normally host the detailed specialist reasoning or process used to obtain that result; that work remains in the appropriate execution system or professional context.
+
+Formal authorization decisions remain valid Cockpit Decision Activities where responsibility and audit must be tracked. This boundary does not authorize new workflow objects, a specialist workstation, or baseline implementation.
+
 ## Operational control semantics (approved future contract)
 
 The Operational Control Freeze v1.0 formalizes two future domain concepts in the Cockpit operational layer: `Criticità.management_objective` and `Activity.purpose = EXECUTION | DECISION`. This is a conceptual contract only: it does not claim a schema field, migration, API, or baseline implementation.
diff --git a/docs/DECISIONS.md b/docs/DECISIONS.md
index 2f64a9f..bb5a70e 100644
--- a/docs/DECISIONS.md
+++ b/docs/DECISIONS.md
@@ -129,3 +129,19 @@ Compact ADR-style register. “Future approved” decisions are binding function
 - **Rationale:** The same reality requires role-aware visual priority without opaque ranking or duplicate problems.
 - **Impact:** Attention is deduplicated and every item provides a visible explanation.
 - **Supersedes / Superseded by:** None.
+
+## DEC-017
+
+- **Decision:** The Cockpit is first a Project Monitoring Layer over distinct domain objects, using a common monitoring projection without replacing those objects with a universal domain object.
+- **Status:** Accepted / current architecture; not implemented in baseline.
+- **Rationale:** Normal project progress must be monitored as observed reality, forecast, variance, confidence, and attention before it is treated as an exception or workflow.
+- **Impact:** The canonical sequence is `PLAN / TARGET / BASELINE → OBSERVED REALITY → FORECAST → VARIANCE → ATTENTION → optional CRITICITÀ → optional ATTIVITÀ`. Variance and attention do not automatically create Criticità; Criticità does not automatically create Attività; Rules and AI cannot create definitive workflow actions without future explicit approval.
+- **Supersedes / Superseded by:** Clarifies DEC-002, DEC-003, DEC-013, DEC-015, and DEC-016; does not supersede them.
+
+## DEC-018
+
+- **Decision:** The Cockpit coordinates explicit, auditable work but does not replace the specialist execution systems or processes used to perform that work.
+- **Status:** Accepted / current architecture; not implemented in baseline.
+- **Rationale:** Control requires accountable requests and verifiable outcomes, not a substitute ERP, engineering, planning, procurement, negotiation, or ordinary communication workstation.
+- **Impact:** An explicit Activity is created only for human work, verification, clarification, collaboration, or a formal decision, and records the required result, responsible party, due date, expected result, obtained result, and supporting evidence. Formal authorization decisions remain valid Decision Activities where responsibility and audit are required.
+- **Supersedes / Superseded by:** Clarifies DEC-005, DEC-006, DEC-015, and DEC-017; does not supersede them.
diff --git a/docs/PROJECT_STATE.md b/docs/PROJECT_STATE.md
index fc1c5b5..5d5b7c3 100644
--- a/docs/PROJECT_STATE.md
+++ b/docs/PROJECT_STATE.md
@@ -21,6 +21,12 @@ Status: **COMPLETE**.
 
 Canonical architecture/governance documentation is now repository-owned and authoritative according to `AGENTS.md`.
 
+## Approved architectural principles
+
+**PROJECT MONITORING LAYER — ARCHITECTURAL PRINCIPLE v1.0** and the **WORK EXECUTION BOUNDARY** are approved architectural principles. They are documentation-level architecture decisions and do not assert implementation in the v0.3.8.1 baseline.
+
+They require the monitoring/product model to remain primary: monitored project state precedes optional exceptions and explicit collaboration workflow.
+
 ## Latest approved functional contract
 
 **WORKFLOW FREEZE — GESTIONE OPERATIVA COCKPIT v1.1**
@@ -73,21 +79,19 @@ These debts are recorded only; this document does not propose fixes.
 
 ## Current phase
 
-Operational UI redesign / validation under restored canonical architecture governance.
+Monitoring/product-model reconciliation under restored canonical architecture governance. Current UI/Figma work must not expand into new functional areas until that reconciliation is complete.
 
 ## Next authorized product activity
 
-Figma / visual design planning, coherently with the approved future contracts and canonical architecture. This is not a claim that any freeze is implemented in the software baseline.
+Real Brofind workflow study, beginning with Procurement AS-IS. This is product analysis only and is not a claim that any approved architectural principle or freeze is implemented in the software baseline.
 
-The planning must use:
+The analysis must use:
 
-- WORKFLOW FREEZE v1.1;
-- OPERATIONAL CONTROL FREEZE v1.0;
-- COLLABORATION FREEZE v1.0;
-- UI FREEZE v1.0;
+- PROJECT MONITORING LAYER — ARCHITECTURAL PRINCIPLE v1.0;
+- WORK EXECUTION BOUNDARY;
 - canonical architecture and decisions;
 
-UI cannot redefine workflow/domain semantics. This authorization does not claim implementation of the Workflow, Collaboration, or UI Freeze in the baseline.
+UI/Figma work cannot redefine workflow/domain semantics or expand into new functional areas before the monitoring/product model is reconciled. This authorization does not claim implementation of the architectural principles or existing approved freezes in the baseline.
 
 ## Deferred / future
 
```

## Current `git status --short`

```text
 M docs/ARCHITECTURE.md
 M docs/DECISIONS.md
 M docs/PROJECT_STATE.md
```

## Consistency check

- **Decision IDs used:** DEC-017 (Project Monitoring Layer) and DEC-018 (Work Execution Boundary).
- **Monitoring versus workflow:** Clear. The architecture explicitly separates `DOMAIN OBJECT → monitoring state → variance / attention → optional Criticità → optional Attività` and states that Criticità and Attività must not contain normal project progress.
- **Work Execution Boundary:** Explicit. The Cockpit coordinates auditable requests and outcomes but does not replace ERP, procurement execution, engineering, detailed planning, specialist calculations, commercial negotiation, or ordinary communications.
- **Normal progress excluded from Activity creation:** Clear. Normal project progress is not workflow activity; an Attività is created only for explicit human work, verification, clarification, collaboration, or a formal decision.
- **Next authorized product analysis:** Clear. `docs/PROJECT_STATE.md` identifies real Brofind workflow study beginning with Procurement AS-IS.
- **Existing decisions/freezes:** No contradiction identified. DEC-017 explicitly clarifies DEC-002, DEC-003, DEC-013, DEC-015, and DEC-016 without superseding them; DEC-018 explicitly clarifies DEC-005, DEC-006, DEC-015, and DEC-017. Both preserve the existing lifecycle, AI-authority, source-of-truth, and future-contract boundaries.
