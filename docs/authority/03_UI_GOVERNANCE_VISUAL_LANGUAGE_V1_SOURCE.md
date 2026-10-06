# GOVERNANCE UI — FONTE VISIVA E LINGUAGGIO v1.0

**Prodotto:** Brofind Project Control / Cockpit controllo commesse  
**Stato:** APPROVATO DA PRODUCT STRATEGY — DA CANONICIZZARE NEL REPOSITORY  
**Ambito:** tutte le schermate, componenti, testi e interazioni dell'interfaccia utente  
**Data:** 28/09/2026

---

## 1. Scopo

Queste regole impediscono che l'implementazione grafica del Cockpit venga reinterpretata liberamente da chi scrive il codice o da un agente AI.

L'interfaccia deve derivare da una catena di autorità esplicita:

**regole di prodotto e di workflow → Figma approvato → contratto di implementazione UI → codice → verifica visiva → approvazione umana**

Nessun passaggio può essere saltato per le aree UI significative.

---

## 2. Fonti di autorità

### 2.1 Autorità semantica

Le decisioni di prodotto, i workflow, i modelli di dominio, le regole di autorità e le sorgenti dati sono governati dai documenti canonici del repository, in particolare:

- `docs/DECISIONS.md`
- `docs/PROJECT_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/V0_SCOPE.md`
- freeze funzionali e di collaborazione approvati

Figma non può introdurre o modificare semantica di dominio o workflow.

### 2.2 Autorità visiva

Per una superficie UI dichiarata congelata, il nodo Figma approvato è la **fonte visiva autoritativa** per:

- architettura dell'informazione visibile;
- composizione della pagina;
- ordine delle sezioni;
- scelta fra card, tabella, lista, pannello, drawer o altra struttura;
- gerarchia visiva;
- disposizione dei domini di controllo;
- rappresentazione degli stati;
- posizione e peso delle Attention / segnalazioni;
- pulsanti e azioni principali;
- densità informativa;
- relazioni spaziali fra componenti;
- testi UI congelati, salvo correzioni linguistiche approvate.

L'implementazione non può sostituire una struttura approvata con una soluzione alternativa solo perché tecnicamente più semplice.

### 2.3 Contratto di implementazione UI

Prima dell'implementazione di una schermata significativa deve esistere un contratto di implementazione che colleghi esplicitamente:

**nodo Figma → componente visivo → dato disponibile → stato → comportamento → file/codice di destinazione**

Il contratto non ridisegna la schermata: traduce il design approvato in istruzioni eseguibili.

---

## 3. Regola di non deviazione

Per una schermata con nodo Figma canonico:

> **L'implementatore non ha autorità per reinterpretare la composizione grafica.**

Non sono consentite, senza nuova approvazione Product Strategy + Figma:

- sostituzione di card con tabelle o viceversa;
- modifica dell'ordine delle sezioni principali;
- eliminazione di domini o indicatori congelati;
- introduzione di nuove gerarchie visive;
- spostamento di Criticità / Attività prima dello stato monitorato;
- trasformazione di Attention in workflow;
- nuove scorciatoie o pulsanti principali;
- cambi sostanziali di navigazione;
- introduzione di terminologia tecnica non approvata;
- uso di stati positivi per dati mancanti, parziali o non verificati.

Se l'implementazione non può rispettare il design per un limite tecnico o per dati mancanti, deve fermarsi e dichiarare un **GAP DI IMPLEMENTAZIONE**. Non deve inventare una soluzione alternativa.

---

## 4. Gestione dei dati non ancora disponibili

L'assenza di implementazione di un dominio non autorizza il cambiamento della struttura grafica.

Esempio: se la schermata Portfolio prevede quattro domini di controllo, i quattro domini restano visibili anche quando solo Economia è realmente alimentato.

Gli altri domini devono mostrare uno stato esplicito come:

- `N/D`
- `NON ANCORA DISPONIBILE`
- `PARZIALE`

secondo il contratto di prodotto.

La struttura della schermata resta invariata; cambia solo il contenuto o lo stato del componente.

---

## 5. Processo obbligatorio per ogni UI significativa

1. **Decisione semantica**  
   Product Strategy definisce cosa rappresenta la schermata e quali concetti sono ammessi.

2. **Design Figma**  
   La schermata viene creata o aggiornata in Figma.

3. **Congelamento visivo**  
   Viene identificato il nodo Figma canonico.

4. **Contratto di implementazione UI**  
   Si descrivono componenti, stati, testi, dati e comportamento senza reinterpretare il design.

5. **Implementazione**  
   Il codice realizza il contratto.

6. **Confronto visivo**  
   La schermata reale viene confrontata con Figma.

7. **Validazione umana**  
   La UI viene approvata esplicitamente.

8. **Test di regressione**  
   I test automatici devono restare verdi.

9. **Commit / chiusura dello stage**  
   Solo dopo il superamento dei gate precedenti.

Una schermata non è completata solo perché i test automatici passano.

---

## 6. Gate obbligatorio di verifica visiva

Prima della chiusura di uno stage UI devono essere verificati almeno:

- struttura generale conforme al nodo Figma;
- ordine delle sezioni conforme;
- domini richiesti presenti;
- stati corretti e non fuorvianti;
- Attention leggibili e nella posizione prevista;
- Criticità e Attività nella gerarchia approvata;
- assenza di duplicazioni visive dello stesso problema;
- comportamento dei dati mancanti/parziali;
- navigazione principale;
- leggibilità a risoluzione desktop prevista;
- testi in italiano e comprensibili;
- nessun termine tecnico interno esposto inutilmente all'utente.

Se uno di questi punti fallisce, lo stage UI non può essere dichiarato chiuso.

---

# 7. REGOLA LINGUISTICA — ITALIANO COME LINGUA BASE

## 7.1 Principio

L'interfaccia utente del Cockpit nasce in **italiano**.

Il pubblico previsto comprende Direzione, Commerciale, Project Manager, Ufficio Tecnico, Amministrazione, Acquisti, Service e altri utenti con livelli diversi di familiarità con terminologia software e project management.

Di conseguenza:

> **La comprensibilità prevale sulla terminologia tecnica.**

Non si usa un termine inglese quando esiste un equivalente italiano chiaro, naturale e non ambiguo.

---

## 7.2 Dove l'italiano è obbligatorio

Devono essere in italiano:

- menu e navigazione;
- titoli di pagina;
- etichette dei campi;
- pulsanti;
- tooltip;
- messaggi di stato;
- errori;
- testi di aiuto;
- nomi delle sezioni;
- badge e semafori;
- messaggi AI rivolti all'utente;
- testi delle Attention;
- descrizioni delle fonti;
- stati dei dati;
- dialoghi e conferme.

I nomi tecnici interni del codice, degli endpoint o dei DTO non devono essere esposti all'utente.

---

## 7.3 Eccezioni ammesse

Un termine inglese può restare solo quando:

1. è un nome proprio di prodotto o sistema;
2. è un acronimo industriale consolidato e l'alternativa italiana sarebbe meno comprensibile;
3. è richiesto da un documento o sistema sorgente e deve essere mostrato fedelmente;
4. non esiste un equivalente italiano naturale e non ambiguo.

Quando possibile, al primo utilizzo deve essere accompagnato da una spiegazione italiana.

---

## 7.4 Glossario UI preferenziale

| Evitare / termine tecnico | Testo UI preferito |
| --- | --- |
| Portfolio | Portafoglio commesse |
| Project Overview | Panoramica commessa |
| Monitoring | Monitoraggio / Stato di controllo |
| Control state | Stato di controllo |
| Attention | Richiede attenzione / Segnale da verificare |
| Baseline | Riferimento iniziale / Budget iniziale, secondo il contesto |
| Target | Obiettivo |
| Observed | Consuntivo / Stato rilevato |
| Actual | Consuntivo |
| Committed | Impegnato |
| Forecast | Previsione |
| Variance | Scostamento |
| Source | Fonte |
| Confidence | Affidabilità |
| Data quality | Qualità dei dati |
| Key milestone | Traguardo chiave / Scadenza chiave, secondo il contesto |
| Billing | Fatturazione |
| Payment | Incasso / Pagamento, secondo il contesto |
| Procurement | Acquisti |
| Outcome | Esito |
| Action | Attività / Azione, secondo il contesto |
| Decision activity | Attività decisionale |
| Workflow | Flusso operativo, quando rivolto all'utente |
| Drill-down | Dettaglio / Approfondimento |
| Legacy | Precedente / storico, oppure non mostrarlo all'utente |
| Stage | Fase, oppure non mostrarlo all'utente |
| DTO / projection | Non esporre nell'interfaccia |

Il glossario può essere esteso, ma non modificato in modo sostanziale senza approvazione Product Strategy.

---

## 7.5 Test di comprensibilità

Ogni testo UI deve superare questa domanda:

> **Un collega Brofind che non ha partecipato al progetto capisce cosa significa e cosa deve fare senza conoscere il nostro modello interno?**

Se la risposta non è chiaramente sì, il testo deve essere semplificato.

Sono da evitare:

- gergo da sviluppatori;
- termini di governance;
- nomi di oggetti interni;
- acronimi non spiegati;
- frasi astratte;
- testi che descrivono come funziona il software invece di cosa significa per l'utente.

---

# 8. AUTORITÀ FRA DOCUMENTI, FIGMA E CODICE

La relazione è:

**Documenti canonici di prodotto e workflow**  
↓  
**Figma canonico per la rappresentazione visiva**  
↓  
**Contratto di implementazione UI**  
↓  
**Codice**

Se Figma contraddice una regola semantica canonica, prevale la regola semantica e il design torna a Product Strategy per correzione.

Se il codice contraddice Figma senza una decisione esplicita, il codice è da correggere.

---

# 9. APPLICAZIONE IMMEDIATA A USABLE CONTROL COCKPIT V1

Per le superfici V1 già congelate, i nodi Figma approvati sono fonte visiva autoritativa.

Riferimenti attuali:

- Portfolio PM — `25:2`
- Portfolio Direzione — `25:185`
- Project Overview Healthy — `46:2`
- Early Variance — `74:266`
- Economic Control — `72:2`
- Key Milestone Monitor — `72:206`
- Billing & Payment Control — `72:426`
- Critical Procurement Monitoring — `72:649`

La V1 non deve essere ridisegnata durante l'implementazione.

Per Stage 2:

- lo Stage 1 economico e la proiezione `economic_v1` restano validi;
- l'attuale tentativo Stage 2 non è approvato come riferimento visivo;
- il Portfolio deve essere riallineato al nodo Figma canonico;
- i domini non ancora implementati mantengono la posizione prevista dal design e mostrano stati di disponibilità espliciti;
- la chiusura di Stage 2 richiede confronto visivo con Figma e approvazione umana.

---

# 10. MODIFICHE CANONICHE RICHIESTE NEL REPOSITORY

Per rendere questa governance non aggirabile, deve essere registrata in cinque punti.

## 10.1 Nuovo documento

Aggiungere:

`docs/UI_GOVERNANCE_VISUAL_LANGUAGE_V1.md`

con il contenuto di questo documento.

## 10.2 `AGENTS.md`

Aggiungere una regola vincolante:

> **UI DESIGN AUTHORITY GATE** — Qualunque modifica significativa all'interfaccia deve rispettare `docs/UI_GOVERNANCE_VISUAL_LANGUAGE_V1.md`. Quando esiste un nodo Figma canonico, Figma è l'autorità visiva e l'implementazione non può reinterpretare composizione, gerarchia o componenti principali. Nessuna UI significativa può essere implementata senza nodo Figma canonico o contratto UI esplicitamente approvato. Se semantica canonica e Figma entrano in conflitto, STOP e rinvio a Product Strategy. Tutto il testo rivolto all'utente deve seguire la regola Italiano-first e il glossario approvato.

## 10.3 `docs/DECISIONS.md`

Aggiungere:

### DEC-025 — Autorità visiva Figma e gate di implementazione UI

- **Decisione:** per le superfici UI congelate, il nodo Figma approvato è la fonte visiva autoritativa; il codice non può reinterpretarne struttura o gerarchia senza nuova approvazione.
- **Stato:** APPROVATA / VINCOLANTE.
- **Motivazione:** separare decisione di prodotto, design e implementazione ed evitare derive grafiche non autorizzate.
- **Impatto:** ogni UI significativa richiede Figma canonico o contratto UI approvato, contratto di implementazione, confronto visivo e validazione umana prima del commit di chiusura.
- **Relazioni:** completa DEC-007, DEC-020 e DEC-021; non modifica semantica di dominio o workflow.

### DEC-026 — Italiano-first e linguaggio comprensibile

- **Decisione:** l'interfaccia utente nasce in italiano e usa linguaggio comprensibile a una platea Brofind ampia; termini inglesi o tecnici sono ammessi solo quando realmente necessari.
- **Stato:** APPROVATA / VINCOLANTE.
- **Motivazione:** ridurre attrito, ambiguità e rischio di mancata adozione.
- **Impatto:** navigazione, etichette, stati, pulsanti, tooltip, messaggi e testi AI rivolti all'utente devono essere in italiano e superare il test di comprensibilità. Identificatori tecnici interni non devono emergere nell'interfaccia.
- **Relazioni:** vincola tutti i futuri freeze e contratti UI.

## 10.4 `docs/PROJECT_STATE.md`

Aggiungere fra le regole correnti:

> **Governance UI attiva:** `UI_GOVERNANCE_VISUAL_LANGUAGE_V1` è vincolante. Figma canonico governa la rappresentazione visiva delle superfici congelate; Product Strategy e documenti canonici governano la semantica. Italiano-first obbligatorio per tutto il testo utente. Nessuno stage UI può chiudersi senza confronto visivo e validazione umana.

## 10.5 `docs/UI_FREEZE_USABLE_CONTROL_COCKPIT_V1.md`

Aggiungere in apertura:

> Questo freeze è soggetto a `UI_GOVERNANCE_VISUAL_LANGUAGE_V1`. I nodi Figma indicati come canonici sono riferimento visivo vincolante. Il freeze non autorizza reinterpretazioni grafiche durante l'implementazione. Tutta la copia rivolta all'utente segue la regola Italiano-first e il glossario approvato.

---

# 11. CONDIZIONE DI CHIUSURA

Questa governance si considera pienamente canonica quando:

1. il nuovo documento è nel repository;
2. DEC-025 e DEC-026 sono registrate;
3. `AGENTS.md`, `PROJECT_STATE.md` e `UI_FREEZE_USABLE_CONTROL_COCKPIT_V1.md` la richiamano;
4. le modifiche sono committate sul ramo di sviluppo autorizzato;
5. lo stato stabile v0.3.8.1 resta invariato fino a una futura decisione di release.

