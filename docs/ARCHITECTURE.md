# Architecture V0

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
