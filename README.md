# Brofind Project Control

Cockpit di controllo commesse per Brofind: un livello di **monitoraggio, controllo e coordinamento** sopra i sistemi esistenti (Galileo, Outlook, cartelle di commessa, planner).

Il Cockpit legge le fonti ufficiali, confronta ciò che dovrebbe essere vero oggi con ciò che risulta vero, segnala dove serve attenzione e coordina le eccezioni. Non sostituisce ERP, acquisti, progettazione, EDMS o contabilità.

> **Stato:** baseline `v0.3.8.1` in migrazione verso il **Cockpit V1** (rilascio `v1.0`).
> Piano e specifiche: [`docs/v1/`](docs/v1/README.md) · Autorità di prodotto: [`docs/authority/`](docs/authority/) · Mockup canonici: [`docs/visuals/`](docs/visuals/)

## Principi

- **READ MANY, WRITE LITTLE**: le fonti ufficiali sono in sola lettura; il Cockpit scrive solo il proprio livello operativo (segnali, attività, decisioni, conferme).
- Dati mancanti o non aggiornati sono sempre visibili, mai mostrati come "tutto regolare".
- L'AI propone, le persone confermano.
- Ogni modifica conserva fonte, autore, data e motivo.

Regole complete per chi sviluppa: [`CLAUDE.md`](CLAUDE.md).

## Avvio della demo locale

Requisito: **Python 3.13.x** (3.14 non supportato).

| Sistema | Comando |
|---|---|
| Windows | `start_demo.bat` (arresto: `stop_demo.bat`) |
| macOS / Linux | `./start_demo.sh` |

Al primo avvio viene creata la `.venv` e installate le dipendenze; poi il Cockpit è disponibile su <http://127.0.0.1:8080> (controllo: `/health`).
Dettagli su runtime, database e backup: [`docs/DEMO_RUNTIME.md`](docs/DEMO_RUNTIME.md). Percorso guidato del caso demo: [`docs/DEMO_B1_RUNBOOK.md`](docs/DEMO_B1_RUNBOOK.md).

> Se la `.venv` è stata creata con una versione precedente del progetto, rimuoverla e rilanciare lo script: è stata aggiunta la dipendenza `alembic`.

## Sviluppo

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pre-commit install          # ruff a ogni commit
.venv/bin/python -m pytest            # test su database isolato in data/test
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

Modifiche allo schema del database: sempre tramite migrazione Alembic.

```bash
BROFIND_RUNTIME=development .venv/bin/alembic revision --autogenerate -m "descrizione"
BROFIND_RUNTIME=development .venv/bin/alembic upgrade head
```

All'avvio, i runtime `demo` e `development` applicano automaticamente le migrazioni.

## Struttura

```
app/
  main.py            avvio applicazione e registrazione router
  routers/           endpoint HTML e API, per area
  models.py          modello dati (SQLAlchemy)
  rules.py           regole deterministiche di segnalazione
  control.py         controllo economico per VdA
  procurement.py     analisi acquisti
  confidence.py      affidabilità delle evidenze
  source_center.py   fonti di commessa (Galileo, Documenti, Outlook)
  ai_analysis.py     estrazione campi dai documenti (proposte da confermare)
alembic/             migrazioni del database
templates/, static/  interfaccia
demo/b1/             caso demo congelato DEMO-B1-001
docs/                specifiche, runtime, storico
tests/               test automatici
```

## Collaborare

Un branch per attività, Pull Request verso `main` con la checklist del template e CI verde. Le slice del piano V1 seguono i gate di [`docs/v1/05_ACCEPTANCE_AND_TEST_CONTRACT_V1.md`](docs/v1/05_ACCEPTANCE_AND_TEST_CONTRACT_V1.md).

Il repository non deve contenere dati reali di clienti, documenti interni o segreti.
