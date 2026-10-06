# 02 — Decisioni architetturali V1 (ADR)

**Stato:** PROPOSTE — ciascuna ADR diventa vincolante solo dopo approvazione esplicita.
**Data:** 2026-10-06

Le ADR riguardano scelte **tecniche**. Non modificano la semantica di prodotto, che resta governata da `docs/authority/`.

---

## ADR-001 — Numerazione delle versioni

- **Contesto:** la baseline è v0.3.8.1. La v1.0 sarà la prima versione con la grafica dei mockup canonici e il modello V1.
- **Decisione proposta:**
  - `v0.3.8.1-baseline`: punto di partenza (già taggato).
  - `v0.4.x … v0.9.x`: release intermedie della migrazione, una per gruppo di slice (vedi `06_IMPLEMENTATION_PLAN_V1.md`).
  - `v1.0.0`: Cockpit V1 completo sulle 8 superfici, accettato secondo `05_ACCEPTANCE_AND_TEST_CONTRACT_V1.md`.
  - Versione unica in `pyproject.toml`; `app/main.py` la legge da lì (oggi è duplicata).
- **Conseguenze:** nessun tag `v1.x` prima del rilascio V1.

## ADR-002 — Stack applicativo

- **Contesto:** il team lavora in Python; l'app girerà sulla rete aziendale, anche senza accesso a Internet; le schermate V1 sono dense (tabelle, ciambelle, grafici, drawer).
- **Decisione proposta:**
  - Backend: **Python 3.13 + FastAPI + SQLAlchemy 2.0** (invariato).
  - Frontend: **pagine generate dal server con Jinja2**, componenti come macro Jinja riusabili, JavaScript leggero per interazioni (drawer, ordinamento, filtri). Aggiornamenti parziali con **htmx** dove serve.
  - Grafici: ciambelle e anelli in CSS (`conic-gradient`), linee e barre in SVG generato dal server. Nessuna libreria esterna finché bastano; Chart.js resta l'opzione se servono grafici interattivi.
  - Tutti gli asset frontend **inclusi nel repository** (nessun CDN, nessun font esterno): l'app deve funzionare in rete interna isolata.
  - Design token CSS (colori, spaziature, tipografia, semafori) derivati dai mockup in un unico file.
- **Alternative scartate:** frontend React/SPA separato. Rende di più sulle schermate ricche, ma raddoppia stack, build e competenze richieste.
- **Rivedibile se:** l'interattività richiesta dalle superfici supera ciò che htmx gestisce agevolmente (da valutare dopo la slice S3).

## ADR-003 — Database e migrazioni

- **Decisione proposta:**
  - **Alembic** per tutte le modifiche di schema, da subito. `create_all` resta solo nei test.
  - **SQLite** per demo locale e sviluppo; **PostgreSQL** per l'esercizio su rete aziendale. Il codice deve restare compatibile con entrambi (nessuna funzione SQL specifica).
  - Snapshot da fonti **immutabili**: ogni import crea una nuova versione identificata da fonte + hash + data; un re-import identico è un no-op (chiude AD-002).
  - Dati sorgente e layer operativo restano in tabelle distinte (READ MANY, WRITE LITTLE).
  - Storico (History Event) in tabella append-only.
  - Date/ore in UTC timezone-aware (`datetime.now(UTC)`).

## ADR-004 — Identità e login

- **Contesto:** utenti con account aziendale brofind.com; Brofind usa Outlook, quindi verosimilmente Microsoft 365 / Entra ID (**da confermare**, OD-04).
- **Decisione proposta:** interfaccia `AuthProvider` con due implementazioni:
  1. **DevLoginProvider**: scelta dell'utente demo da un elenco. Attivo **solo** nei runtime `demo`, `development` e `test`; rifiutato all'avvio in produzione.
  2. **EntraIdProvider**: login OIDC con Microsoft Entra ID, limitato al tenant aziendale; utente creato o aggiornato al primo accesso con email e nome.
  - Sessione con cookie firmato (`APP_SECRET` obbligatorio e non di default fuori dalla demo), `HttpOnly`, `SameSite=Lax`, `Secure` in produzione.
  - Nuovo runtime `production`: richiede PostgreSQL, EntraIdProvider, segreto configurato e HTTPS.
- **Conseguenze:** il resto dell'app vede solo "utente corrente con ruoli"; passare da demo a Entra ID non tocca i controlli di accesso.

## ADR-005 — Autorizzazione per ruolo (RBAC configurabile)

- **Contesto:** i ruoli aziendali (Direzione, Commerciale, PM, reparto Elettrico, Acquisti, Amministrazione…) devono essere definibili in futuro senza modificare il codice. Il freeze separa i ruoli **sulla commessa** (Parties & Roles, freeze §8).
- **Decisione proposta — due livelli distinti:**
  1. **Ruolo applicativo** (cosa puoi fare nel Cockpit): `Role` con insieme di `Permission`, assegnato agli utenti; configurabile da database e, in futuro, da un'interfaccia di amministrazione. Con Entra ID i gruppi aziendali possono essere mappati sui ruoli.
  2. **Ruolo sulla commessa** (chi fa cosa su quella commessa): `ProjectParty` (PM, Commerciale, referente E&I, Acquisti, cliente, fornitore…). Serve a ownership, conferme ed escalation; **non** concede permessi da solo.
- **Perimetro di visibilità** per ogni permesso di lettura: `ALL` (tutte le commesse) · `PARTY` (commesse in cui l'utente è parte) · `DEPARTMENT` (commesse con attività/oggetti assegnati al suo reparto).
- **Permessi iniziali** (codici tecnici, mai mostrati in UI):
  `portfolio.view`, `project.view`, `domain.<dominio>.view`, `project.create`, `project.configure`, `source.manage`, `extracted_field.review`, `finding.review`, `attention.acknowledge`, `criticita.manage`, `activity.create`, `activity.respond`, `activity.validate`, `decision.record`, `override.operational`, `override.sensitive`, `admin.roles`.
- **Ruoli di esempio** (seed, modificabili): Direzione (`ALL`, tutti i permessi); Responsabile PM / Direzione Tecnica (`ALL`); PM (`PARTY`); Commerciale (`PARTY`); Acquisti (`DEPARTMENT`); Amministrazione (`DEPARTMENT`); Ufficio Tecnico, Elettrico/Strumentale, Processo, Software/Automazione, Service (`DEPARTMENT`); Amministratore applicativo (`admin.roles`).
- **Applicazione:** ogni endpoint dichiara il permesso richiesto tramite una dipendenza FastAPI `require(permission, project)`. La UI nasconde ciò che non è permesso, ma la verifica è **sempre** sul server (chiude AD-001). Ogni transizione di stato verifica anche la regola di dominio (es. solo il richiedente o la Direzione validano un'Attività).
- **Test obbligatori:** matrice ruolo × endpoint di scrittura.

## ADR-006 — Struttura del codice

- **Decisione proposta:**
  ```
  app/
    core/        config, db, sicurezza, sessione, permessi, storico
    sources/     Source Center, lettori, adapter (Galileo, documenti, Outlook)
    domains/     un pacchetto per dominio: master, technical, procurement,
                 documents, economics, billing, operational (attention,
                 criticità, attività, outcome, change)
    projections/ proiezione di monitoraggio comune e aggregazioni
                 (portfolio, overview)
    web/         router FastAPI per superficie, template, componenti
    ai/          provider di estrazione e drawer AI (solo proposte)
  ```
  - Ogni dominio espone: modelli, regole deterministiche di Attention, proiezione di monitoraggio, router.
  - Nessuna logica con codice commessa scritto nel codice (le eccezioni 9028 diventano dati o configurazione).

## ADR-007 — Proiezione di monitoraggio comune

- **Contesto:** l'architettura (DEC-017) richiede oggetti di dominio distinti che condividano una proiezione di monitoraggio, senza un oggetto universale.
- **Decisione proposta:** ogni oggetto monitorato produce una `MonitoringView` calcolata (non salvata) con: `target/baseline`, `observed`, `forecast`, `variance`, `source`, `as_of`, `freshness` (FRESCO / DA AGGIORNARE / SCADUTO / N/D), `confidence`, `control_state` (VERDE / GIALLO / ROSSO / GRIGIO), `explanation`.
  - Il semaforo di dominio deriva dalle proiezioni degli oggetti. **Verde solo se** nessun problema **e** dati sufficientemente freschi.
  - Portfolio e Panoramica leggono solo le proiezioni: non introducono dati nuovi (freeze §19–20).

## ADR-008 — Dati demo e fixture

- **Decisione proposta:**
  - Un **unico dataset demo coerente e fittizio** che alimenta tutte le 8 superfici, ispirato ai valori dei mockup ma senza nomi di clienti reali.
  - I valori dei mockup restano fixture visive, mai dati di produzione (A16).
  - **9028 (anonimizzata)** e **DEMO-B1-001** restano come fixture di regressione con i loro invarianti (sforamento €40.000, scaduto €200.000, penalty cap da verificare).
  - Le 12 commesse P-26001…012 vengono migrate sul modello V1 o ritirate (OD-07).

## ADR-009 — AI

- **Decisione proposta:**
  - Interfaccia `ExtractionProvider`: l'estrazione regex attuale diventa il provider `deterministic`; un provider basato su modello linguistico potrà affiancarlo.
  - Il **drawer AI** è unico, a livello di commessa, chiuso per default. Può spiegare, riassumere, confrontare fonti e proporre; ogni proposta mostrata viene tracciata (accettata / collegata / scartata).
  - Nessuna scrittura automatica: una proposta diventa dato solo dopo conferma umana.
  - Scelta del fornitore del modello e del trattamento dei dati aziendali: **aperta** (OD-08). Fino ad allora il drawer non invia dati fuori dalla rete aziendale.
