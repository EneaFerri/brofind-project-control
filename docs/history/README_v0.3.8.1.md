# Brofind Project Control — V0.3.8.1


Patch V0.3.8.1 **Confidence Foundation Fix**. Release di semplificazione UX del cockpit Brofind, con pilot 9028 basato sulle evidenze disponibili. La V0.3.8 consolida le scelte emerse dalla review guidata della V0.3.7 e introduce come regola architetturale non negoziabile **READ MANY, WRITE LITTLE**.

## Principio fondamentale — READ MANY, WRITE LITTLE

Il cockpit non sostituisce Galileo, Pipedrive, Outlook, il file server/EDMS, il planning o il contratto. Legge, normalizza, collega e interpreta le sorgenti ufficiali; scrive soltanto il proprio layer operativo.

**Sorgenti ufficiali: read-only dal cockpit**

- ordini, fatture, pagamenti, budget e costi ERP;
- PO, contratto, extra e documenti contrattuali originali;
- planning ufficiale;
- dati Pipedrive;
- email/comunicazioni Outlook;
- documenti tecnici e file di commessa.

**Layer operativo scrivibile del cockpit**

- finding e relativa conferma/scarto;
- alert e azioni;
- owner, note, conversazioni e risposte registrate;
- validazioni, review ed escalation;
- interpretazioni operative contrattuali congelate, sempre con fonte e validatore;
- classificazione `budget residuo / saving candidato / saving consolidato`;
- disposizioni operative su requisiti/finding.

Se una sorgente è errata, la correzione viene fatta nel sistema autorevole; al sync successivo il cockpit recepisce il nuovo stato.

## Struttura UX V0.3.8

La navigazione segue il principio **decisione → diagnosi → evidenza**. Ogni vista risponde a una domanda principale:

- **Panoramica** — come sta andando la commessa?
- **Economia** — sto rispettando il budget e dove sto deviando?
- **Procurement** — abbiamo comprato ciò che serve nei tempi?
- **Contratto** — quali condizioni sono congelate e quali change vanno chiariti?
- **Operatività** — cosa deve fare qualcuno adesso?
- **Confidence Review** — quanto è affidabile il controllo e cosa manca per migliorarlo?

I dettagli secondari sono progressivamente espandibili; la pagina economica non miscela più procurement, qualità dati e confidence dettagliata.

## Workflow operativo

`SORGENTE READ-ONLY → FINDING → VALIDA/SCARTA → RECEPISCI NEL COCKPIT → ALERT/AZIONE → RISPOSTA → VALIDAZIONE → NUOVO STATO OPERATIVO`

Un finding AI non modifica mai direttamente una sorgente ufficiale. Il pulsante **Recepisci nel cockpit** applica soltanto una conseguenza nel layer operativo.

Le comunicazioni preparate dal cockpit sono inviate manualmente dall'utente. Il thread operativo distingue inviati, ricevuti e note interne.

## Avvio rapido Windows

1. Estrarre tutto lo ZIP in una nuova cartella locale.
2. Installare Python 3.13.x. Python 3.14 non è supportato per questa demo.
3. Non copiare .venv da un altro PC.
4. Lanciare start_demo.bat.
5. Attendere l'apertura automatica del browser dopo il health check.

Il primo avvio crea .venv e installa requirements.txt; gli avvii successivi
non reinstallano le dipendenze e possono essere eseguiti offline.

Endpoint di controllo: http://127.0.0.1:8080/health.

Procedura completa, database e backup: docs/DEMO_RUNTIME.md.

## Novità V0.3.8 — UX Simplification

- portfolio con intestazione sticky e tooltip sintetici;
- overview con KPI essenziali, salute per dominio e confidence complessiva separata;
- alert principali ridotti a fatti chiave + prossima azione;
- controllo economico riorganizzato in `snapshot → sintesi → stato → VdA`;
- `Costo assorbito + impegnato` come KPI centrale e `Budget non ancora coperto` come quota priva di costi/impegni noti;
- VdA senza scroll orizzontale: poche colonne manageriali, dettagli secondari espandibili;
- `Verifica urgente` più evidente, `Conferma saving` esplicito e `Potenziale ritardo procurement` per servizi/montaggi;
- Procurement separato dalla vista economica;
- confidence complessiva nelle viste normali, dettaglio per dominio solo nella Confidence Review;
- Confidence Review con `Cosa sappiamo / Cosa manca / Come migliorarla` e generazione di un piano di recupero composto solo da azioni cockpit;
- thread operativo stile chat con inviati/ricevuti sfalsati e pulsante verde **Invio** per registrare/copiare un messaggio da inviare manualmente;
- Contract Baseline operativa: chiarimento/freeze delle condizioni nel layer cockpit, senza modificare il contratto sorgente;
- change potenziali con evidenze, verifica al Commerciale e possibilità di scarto;
- nuovo `CockpitDecision` per conservare decisioni operative senza scrivere nei master data;
- finding di schedule/payment promise trasformati in azioni operative, non in modifiche del planning o delle comunicazioni sorgente.

Vedi `docs/V0_3_8_RELEASE.md`, `docs/ARCHITECTURE.md` e `docs/WORKFLOW_BUTTONS.md`.

## Novità V0.3.7 — Validation Release

Questa release traduce in UI e workflow le scelte validate nella revisione V0.3.6 senza introdurre ancora planning/lead-time definitivi.

- portfolio con distinzione esplicita **Critica / Da intervenire / Da presidiare** e tooltip con mini-recap della causa;
- header commessa con un solo **Budget autorizzato**, fase commessa e avanzamento acquisti espresso come conteggi oggettivi;
- `Costo noto + impegnato` come KPI economico centrale, con **Confidence economica**;
- Confidence per dominio (`Alta / Media / Bassa / Insufficiente`) e **Project Confidence Review** automatica sui progetti con fondazione di controllo reale;
- report dei gap che riducono la confidence e alert assegnabile al **Responsabile Tecnico** con visibilità Direzione;
- VdA con profilo uniforme per natura, stato procurement separato dal rischio e gestione distinta `Budget residuo / Saving candidato / Saving consolidato`;
- consolidamento manuale del saving nel margine di commessa, senza riallocazione automatica verso altre VdA;
- servizi/montaggi trattati come procurement tardivo: vicino alla consegna il controllo cerca evidenza di RFQ/offerte invece di segnalare semplicemente “ordine mancante”;
- azioni di tipo `Verifica / Decisione / Intervento`, assegnabili a persona o reparto; risposta registrata → **da validare dal richiedente** → chiusura;
- escalation derivata per azioni scadute, senza riassegnare automaticamente la responsabilità originale;
- Contract Baseline laterale con condizioni `FROZEN` o `DA CHIARIRE`, ordini/extra e change potenziali; nessuna risoluzione autonoma delle contraddizioni contrattuali;
- finding tecnici/engineering ancora confermabili o scartabili; il loro contributo al procurement/confidence può essere disattivato con `TECHNICAL_DOCUMENT_FINDINGS_ENABLED=false`.

La V0.3.7 resta una **release di validazione**: macro-famiglie economiche, required date, lead-time definitivi e soglie di escalation restano da definire con Direzione, Amministrazione e responsabili di reparto.

## Novità V0.3.6

- primo **Analysis Engine** procurement per la 9028;
- distinzione tra stato acquisti e rischio acquisti;
- classificazione VdA per natura (acquisto diretto, servizi/montaggi, ore interne, logistica, riserva);
- evidenze strutturate da documenti: requisito LEL contrattuale e secondo LEL engineering da validare;
- ordine base PO-PILOT-001 marcato come pacchetto documentale acquisito/completo;
- alert prudenziale procurement per commessa prossima alla consegna, senza dichiarare ritardi in assenza di required date affidabile;
- nessun ETC strutturato richiesto ai PM.

## Novità V0.3.5

Release dedicata alla UX del cockpit, senza introdurre un nuovo modello economico:

- portfolio ridotto a KPI decisionali e separazione delle metriche secondarie;
- priorità rinominate in `Critica / Da intervenire / Da presidiare / Sotto controllo`;
- `N/D` sempre grigio e `Dati parziali` neutro, anche nel portfolio;
- origine dati evidente (`Dati controllo reali` vs `Demo`);
- pagina commessa con stati non disponibili non cliccabili e non confusi con situazioni regolari;
- controllo economico a larghezza piena;
- VdA filtrabili per rilevanza, criticità, acquisti aperti/conclusi, extra o tutte;
- intestazione VdA sticky e terminologia più esplicita (`Budget disponibile`, `Acquisti`, `Stato economico`);
- milestone/fatture senza fonte compattate invece di occupare grandi pannelli vuoti;
- timeline con categorie visivamente distinte;
- regola semantica: rosso = problema concreto, giallo = presidio/rischio, grigio = non valutabile, verde = valutato e regolare.

La logica di budget della 9028 resta **beta / da validare** su ulteriori commesse mature.

Vedi `docs/V0_3_5_RELEASE.md`.

## Novità V0.3.4

La 9028 (cliente pilota anonimizzato) è ora ricostruita con evidenze reali disponibili:

- PO cliente base `PO-PILOT-001` €985.550 netti;
- PO extra `PO-PILOT-002` €113.350 netti;
- budget baseline €657.708,26;
- budget costi Extra 1 €73.091;
- budget operativo Galileo €730.797;
- tutte le 34 VdA della baseline, con Δ scope Extra 1;
- ordini, ricevimenti, residui, costo uomo e spese generali da snapshot Galileo.

Il semaforo budget non eredita più automaticamente la severità della peggiore VdA. La 9028 mostra un alert **giallo**: esistono sforamenti locali, ma la copertura sulle VdA con acquisti dichiarati conclusi è superiore. Questa regola resta **beta / da validare** su altre commesse mature.

Le aree senza dati sono `N/D` e non verdi. Procurement e stato economico sono separati. Il template Excel supporta anche `CUSTOMER_ORDERS` e `CHANGES`, oltre a `CONTROL_SNAPSHOT` e `CONTROL_LINES`.

Vedi `docs/V0_3_4_RELEASE.md`.
