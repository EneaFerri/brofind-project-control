# 06 — Implementation Plan V1 (A21)

**Stato:** PROPOSTA — nessuna slice parte senza approvazione esplicita (A22).
**Data:** 2026-10-06

Migrazione da v0.3.8.1 al Cockpit V1 per slice verticali (interfaccia già rilasciata in **v1.0.0**): ognuna porta modello, regole, proiezione, schermata e test, e rispetta `05_ACCEPTANCE_AND_TEST_CONTRACT_V1.md`.

## Sequenza

| Slice | Contenuto | Dipende da | Release |
|---|---|---|---|
| **S0** Pulizia pre-push | vedi sotto | — | (nessun tag; poi primo push) |
| **S1** Identità e permessi | ADR-004/005: `User`, `Role`, `Permission`, `RoleAssignment`, `Department`, DevLoginProvider, dipendenza `require()`, matrice test ruoli × endpoint; chiude AD-001 | S0 | v1.1.0 |
| **S2** Shell e design system ✅ *anticipata, rilasciata in v1.0.0* | layout condiviso (sidebar, header commessa, nav di commessa, drawer AI vuoto), design token dai mockup, componenti (semaforo, badge stato, KPI, ciambella, tabella ordinabile, pannello laterale), nessuna libreria frontend esterna, registro domini con stato `Non ancora disponibile` | S1 | v1.0.0 |
| **S3** Portfolio + Overview | `MonitoringView` comune (ADR-007), Attention per dominio con deduplica e cause comuni, fasi e stato commessa (archiviazione), ordinamento senza score, Principale esposizione, Prossimo gate (`N/D` finché manca S7); ricalcolo su import/evento invece che su GET | S2 | v1.2.0 |
| **S4** Economics | snapshot immutabili e storici (AD-002), forecast con metodologia configurabile + conferma, Economic Result, scostamenti con causa, varianti → Change Item (parte economica); rimozione eccezioni 9028 | S3 | v1.3.0 |
| **S5** Billing & Payment | Billing Event da contratto (riusa review campi B1), collegamento eventi ↔ fatture Galileo, tolleranze, KPI maturato/fatturato/incassato/esposizione | S3, S7 parziale | v1.3.0 |
| **S6** Procurement | Procurement Item, stadi, need/promise/forecast/actual, lead time con override, matching ordini Galileo con conferma; vista per VdA come aggregato | S3, S4 | v1.4.0 |
| **S7** Master Planner | Milestone V1, fasi, readiness, condizioni e Control Checkpoint, propagazione "da verificare"; collega Procurement/Documents/Technical/Billing | S3 | v1.4.0 |
| **S8** Documents | Document Item, Minimum Document Set da template, evidenze dalla cartella commessa, stati derivati | S7 | v1.5.0 |
| **S9** Technical | Technical Decision/Checkpoint, Outcome, segnali di allineamento | S7 | v1.5.0 |
| **S10** Controllo operativo | Criticità, Attività V1, Outcome, Conversazioni, Change Item completo, Storico di commessa | S3; **freeze mancanti (OD-01)** | v1.6.0 |
| **S11** Drawer AI | provider di estrazione, drawer con citazione fonti, tracciamento proposte; modello linguistico secondo OD-08 | S10 | v1.6.0 |
| **S12** Esercizio in rete aziendale | runtime `production`, PostgreSQL, EntraIdProvider, HTTPS, backup, guida di installazione | S1 | v1.7.0 |
| **UAT** | dataset demo coerente su 8 superfici, pilota reale (Gate 7), verifica visiva finale | tutte | rilascio di accettazione |

**Stato al 2026-10-06:** S0 completata; la grafica V1 (S2) è applicata a tutte le 8 superfici più Criticità/Attività/Conversazioni/Storico usando il modello dati v0.3.8.1. Ciò che il modello non fornisce ancora è mostrato come N/D: elenco in [`IMPLEMENTATION_GAPS.md`](IMPLEMENTATION_GAPS.md).

S5 usa le date di maturazione: se S7 non è pronto, la data viene dal contratto confermato (caso B1) e la readiness resta `N/D`.

## S0 — Pulizia pre-push (proposta di dettaglio)

Obiettivo: repository pulito e pronto per la collaborazione, **senza** cambiare il comportamento funzionale. Gli 87 test devono restare verdi.

1. **Alembic**: configurazione, migrazione iniziale = schema attuale; runtime demo/dev la applicano all'avvio; i test continuano con `create_all`.
2. **Ristrutturazione di `main.py`** in router (`portfolio`, `project`, `sources`, `actions`, `findings`, `decisions`, `admin`) senza cambiare URL né risposte.
3. **Versione unica** letta da `pyproject.toml`.
4. **`datetime.utcnow()` → `datetime.now(UTC)`** (rimuove ~6.000 warning).
5. **Strumenti di qualità**: `ruff` (lint + formattazione) e `pre-commit`; passo `ruff` nella CI.
6. **Documentazione**: README riscritto (scopo, avvio, struttura, link a `docs/v1/`); note di rilascio V0.x spostate in `docs/history/`.
7. **Template di collaborazione GitHub**: template per PR (con checklist dei Gate) e per issue (bug / IMPLEMENTATION GAP / change request).
8. **Verifica riservatezza** finale prima del push (ricerca di nomi, riferimenti cliente, segreti).

Non inclusi in S0 (per non mescolare pulizia e funzionalità): AD-001 (→ S1), AD-002 e rimozione eccezioni 9028 (→ S4).

## Modalità di lavoro

- Un branch per slice (`slice/s1-identita-permessi`…), PR verso `main` con checklist Gate, CI verde, screenshot vs mockup per le slice UI.
- Ogni slice parte con un breve **contratto di implementazione UI** (componente mockup → dato → stato → comportamento → file).
- Gli IMPLEMENTATION GAP emersi vengono registrati e portati alla decisione del Product Owner, non risolti in autonomia.
