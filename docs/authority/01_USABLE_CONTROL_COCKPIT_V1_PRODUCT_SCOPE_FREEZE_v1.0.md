# USABLE CONTROL COCKPIT V1 — PRODUCT & SCOPE FREEZE

**Versione:** 1.0  
**Stato:** FROZEN — Product Model / V1 Scope  
**Data freeze:** 04/10/2026  
**Progetto:** Brofind Project Control / Cockpit controllo commesse  

---

## 1. Scopo del documento

Questo documento congela il **Product Model** e il **perimetro funzionale della V1** del Cockpit controllo commesse.

Da questo momento:

- il modello qui descritto è la base autorevole per Concept UI, Figma, Implementation Contract, Codex, QA e UAT;
- nuove idee non entrano automaticamente nella V1;
- ogni nuova richiesta deve essere classificata come:
  - **IN PATH** — coerente con il freeze e necessaria al passo approvato;
  - **MODEL GAP** — concetto mancante che impedisce al modello di funzionare;
  - **CHANGE REQUEST** — miglioramento utile ma fuori dal freeze corrente;
  - **OUT OF SCOPE** — funzione non coerente con la V1 o appartenente a un altro sistema.

---

# 2. Definizione del prodotto

Il Cockpit è un **Project Monitoring, Control and Coordination Layer**.

Il suo compito è:

**BASELINE / TARGET  
→ OBSERVED  
→ FORECAST  
→ VARIANCE  
→ ATTENTION  
→ eventuale CRITICITÀ  
→ eventuale ATTIVITÀ  
→ OUTCOME  
→ rivalutazione dello stato reale**

Il Cockpit:

- osserva fonti esterne;
- confronta atteso e osservato;
- rileva assenze, ritardi, conflitti e dati stale;
- aggiorna il forecast quando esistono dati affidabili;
- segnala Attention e incoerenze;
- coordina le eccezioni;
- conserva evidenze, cause e storico;
- permette di ricostruire cosa è successo e perché.

Il Cockpit **non è**:

- ERP;
- sistema acquisti;
- Gantt/CPM completo;
- sistema di progettazione;
- EDMS completo;
- sistema contabile;
- CRM;
- Service Management;
- workflow engine rigido;
- autorità decisionale AI.

---

# 3. Principi costituzionali

## 3.1 Expected State Now vs Observed State Now

Il controllo valuta sempre:

> **cosa dovrebbe essere vero oggi**  
> rispetto a  
> **cosa risulta vero oggi**

tenendo conto di:

- fase;
- date obiettivo;
- forecast;
- dipendenze;
- readiness;
- qualità e freschezza dei dati.

Incompletezza non significa automaticamente ritardo.

## 3.2 Il Cockpit monitora, non esegue

Il Cockpit:

- osserva;
- segnala;
- coordina;
- registra;
- verifica l'esito.

Le attività operative restano nei sistemi e processi competenti:

- Galileo;
- Outlook;
- planner;
- cartella server;
- reparto tecnico;
- amministrazione;
- acquisti;
- commerciale;
- service.

## 3.3 Automation-first, confirmation-when-needed

Il Cockpit deve evitare data entry duplicato.

Regola:

> **se un dato può essere osservato in modo affidabile da una fonte configurata, non deve essere reinserito manualmente.**

L'intervento umano serve soprattutto per:

- conferme;
- decisioni;
- interpretazioni;
- eccezioni;
- riconciliazioni;
- override.

## 3.4 Human authority

L'AI può:

- leggere;
- estrarre;
- classificare;
- confrontare;
- rilevare pattern;
- proporre collegamenti;
- proporre outcome;
- proporre checkpoint;
- proporre stime.

L'AI non può:

- scegliere una soluzione tecnica;
- decidere un fornitore;
- autorizzare costi;
- modificare obblighi contrattuali;
- decidere causalità/responsabilità senza conferma;
- chiudere decisioni tecniche;
- risolvere conflitti ambigui autonomamente.

---

# 4. Unified Control Language

Tutto il Cockpit usa la stessa grammatica di controllo.

## 4.1 Semafori

**VERDE**  
Stato coerente con ciò che dovrebbe essere vero oggi e dati sufficientemente affidabili.

**GIALLO**  
Esiste una condizione da verificare, un rischio concreto o un disallineamento che richiede attenzione, ma non una violazione/blocco accertato.

**ROSSO**  
Esiste una condizione accertata incompatibile con il controllo atteso: ritardo previsto/effettivo, blocco, scostamento confermato, sequenza contrattuale violata o altro evento equivalente.

**GRIGIO / DA VERIFICARE**  
I dati sono mancanti, stale o insufficienti per esprimere un giudizio affidabile.

Il verde richiede **sia assenza di problemi rilevati sia dati sufficientemente freschi e affidabili**.

## 4.2 Livelli di lettura

**Portfolio**  
Segnale semplice per capire dove guardare.

**Project Overview**  
Sintesi delle principali cause.

**Domain Control**  
Dettaglio operativo, oggetti, stati ed evidenze.

**Source / History**  
Perché il Cockpit mostra quel dato e come si è evoluto.

---

# 5. Source Configuration di commessa

Ogni commessa ha una configurazione esplicita delle proprie fonti.

Fonti minime previste:

- **Project Communication Source**  
  contenitore Outlook dedicato o equivalente;
- **Project Document Folder**  
  cartella server ufficiale della commessa;
- **Galileo Project Source**  
  dati strutturati della commessa;
- eventuale **Planner Source**;
- eventuali altre fonti autorizzate.

Il Cockpit osserva solo fonti:

- configurate;
- esplicitamente collegate;
- oppure associabili alla commessa con sufficiente confidence.

Associazioni ambigue richiedono conferma.

---

# 6. Source / Freshness / Confidence / Reconciliation

Ogni dato rilevante deve poter esporre:

- fonte;
- data della fonte;
- data ultimo aggiornamento/rilevamento;
- stato di freschezza;
- stato di verifica/confidence;
- evidenza collegata, quando necessaria.

## 6.1 Freschezza

Una fonte autorevole può diventare inaffidabile se non sufficientemente fresca.

Le soglie di freschezza:

- sono configurabili;
- hanno default globali;
- possono avere override di commessa/item;
- non devono essere hard-coded.

## 6.2 Reconciliation

Il Cockpit distingue sempre tra:

- **dato osservato dalla fonte**;
- **valore di controllo riconciliato**.

Una fonte più recente non prevale automaticamente su una più vecchia.

Prima si identifica **che cosa rappresenta il dato**, poi si gestisce l'eventuale conflitto.

Un valore riconciliato:

- non cancella la fonte originaria;
- conserva motivo, evidenza, autore e data;
- lascia visibile la discrepanza finché la sorgente non viene riallineata.

Nuove evidenze materialmente incompatibili possono riaprire una verifica già confermata.

---

# 7. Project Opening / KOM / Scope Profile

L'apertura della commessa segue il principio:

**Template Brofind + analisi ordine/contratto + KOM  
→ proposta configurazione  
→ conferma/correzione PM  
→ approvazione della baseline iniziale**

Il KOM è un **modulo strutturato di interpretazione operativa**, non la source of truth.

Il contratto/ordine rimane fonte degli obblighi esterni.

Il KOM serve a inizializzare:

- Scope Profile;
- milestone contrattuali;
- gate interni;
- sensibilità contrattuali;
- dipendenze esterne;
- responsabilità;
- fonti di controllo;
- checkpoint tecnici;
- documenti attesi;
- possibili Change Item da monitorare.

La configurazione iniziale può essere **progressiva**.

Il sistema non richiede completezza totale all'apertura.

---

# 8. Project Parties & Roles

Ogni commessa dispone di un registro condiviso leggero di soggetti e ruoli.

Esempi:

- PM;
- commerciale;
- processo;
- E&I;
- acquisti;
- cliente;
- engineering;
- fornitore;
- installatore;
- terze parti.

Il registro viene usato da tutti i domini per:

- ownership;
- responsabilità di monitoraggio;
- responsabilità di disponibilità;
- confirming role;
- escalation.

Non è una RACI completa né un CRM.

---

# 9. Master Planner

Il Master Planner rappresenta le date/gate che possono materialmente cambiare il controllo della commessa.

Non è un Gantt dettagliato.

## 9.1 Tipi di milestone

Le milestone possono essere:

1. **Contrattuali**;
2. **Interne Brofind**;
3. **Esterne / importate da planner**.

Numero e contenuto variano per progetto.

## 9.2 Date

Ogni milestone può avere:

- **Data iniziale** — baseline immutabile;
- **Data obiettivo** — target attualmente valido/approvato;
- **Data prevista** — forecast realistico corrente;
- **Data effettiva** — data reale dell'evento.

Le modifiche significative mantengono storia e causa.

## 9.3 Readiness

Una milestone può avere 0..N condizioni/dipendenze.

Le condizioni possono essere:

- **BLOCCANTI**;
- **RILEVANTI**.

Readiness:

- **PRONTA**;
- **NON PRONTA**;
- **DA VERIFICARE**.

**PRONTA ≠ RAGGIUNTA.**

La milestone è raggiunta solo quando l'evento è effettivamente avvenuto e, quando richiesto, esiste evidenza adeguata.

## 9.4 Dipendenze

La milestone può dipendere da oggetti di dominio già esistenti:

- Procurement Item;
- Document Item;
- Technical Checkpoint;
- condizioni cliente/terze parti;
- Control Checkpoint.

Gli oggetti non vengono duplicati nel Master.

Quando non esiste un oggetto adeguato si può creare un **Control Checkpoint leggero**.

Le variazioni upstream propagano:

> **necessità di verifica / segnale**

non spostamenti automatici delle date downstream.

## 9.5 Fasi

Le fasi sono raggruppamenti configurabili del Master.

Non sono workflow rigidi.

Possono:

- variare tra commesse;
- sovrapporsi;
- essere proposte dal Cockpit;
- essere corrette dal PM con tracciabilità.

Servono a contestualizzare lo **Expected State Now**.

## 9.6 Planner esterni

Il Cockpit non replica il Gantt completo.

Importa solo:

- milestone;
- date;
- gate;
- dipendenze selezionate;
- revisioni rilevanti.

Le fonti possono essere:

- operative autorizzate;
- informative.

La freschezza del planner è monitorata.

---

# 10. Control Checkpoint

Il Control Checkpoint rappresenta:

> **un fatto/esito atteso che il Cockpit deve osservare**

Non rappresenta l'attività che produce quel fatto.

Esempio:

- “Accordo cliente ricevuto” = checkpoint;
- “Contattare il cliente” = Activity.

Stati minimi:

- ATTESO;
- RILEVATO;
- CONFERMATO;
- SCADUTO / NON RILEVATO;
- NON APPLICABILE.

**RILEVATO ≠ CONFERMATO.**

La conferma può essere automatica solo nei casi:

- semplici;
- deterministici;
- esplicitamente autorizzati.

Ogni checkpoint può avere:

- monitoring owner;
- confirming role;
- data necessaria opzionale;
- fonte/evidenza;
- collegamenti a milestone.

La data del checkpoint è una **data di controllo**, non la scadenza di un'attività operativa.

---

# 11. Change Control / Variazioni

La Variazione è un oggetto V1 di primo livello.

Nome concettuale:

> **Change Item / Variazione**

Può nascere:

- manualmente;
- da contratto/documenti;
- da mail;
- da evidenze tecniche;
- da proposta AI/regole.

Una proposta AI diventa Change Item ufficiale solo dopo conferma umana.

## 11.1 Lifecycle leggero

Stati:

- RILEVATA;
- IN VALUTAZIONE;
- DEFINITA;
- CHIUSA.

Esito possibile:

- concordata;
- non concordata;
- annullata;
- altra classificazione configurata.

Stato implementazione separato:

- NON AVVIATA;
- IN CORSO;
- COMPLETATA.

La V1 evita hard-stop.

La chiusura è flessibile:

- il Cockpit segnala impatti ancora aperti;
- il PM può chiudere con motivazione;
- rigidità bassa, tracciabilità alta.

## 11.2 Owner

Il PM è normalmente il **Control Owner complessivo**.

Le verifiche specialistiche non trasferiscono automaticamente la responsabilità di coordinamento.

## 11.3 Matrice impatti

Ogni Change Item può valutare in modo leggero:

- Scope;
- Master;
- Economic;
- Procurement;
- Document;
- Technical;
- Billing.

Stati:

- DA VALUTARE;
- IMPATTO RILEVATO;
- NESSUN IMPATTO.

## 11.4 Change ≠ Criticità

Una variazione non è automaticamente una Criticità.

I due oggetti hanno lifecycle indipendenti.

## 11.5 Change non modifica direttamente il progetto

Il Change Item:

- genera/giustifica aggiornamenti;
- conserva il legame causale;
- non riscrive direttamente Master, Budget, Procurement o altri domini.

## 11.6 Extra / Minus

Classificazione preliminare:

- EXTRA;
- MINUS;
- NEUTRO;
- DA DETERMINARE.

Il dettaglio economico resta nell'Economic Control.

---

# 12. Document Control

Missione:

> **controllare se la documentazione necessaria alla commessa e al corretto funzionamento del Cockpit è disponibile, aggiornata e adeguata quando serve.**

Non è un EDMS.

## 12.1 Due famiglie

1. **Deliverable di progetto**
2. **Documenti / fonti di controllo**

## 12.2 Document Register

Se esiste una Document List:

> viene usata come base primaria del controllo.

Se non esiste:

> viene proposto un **Minimum Document Set** derivato da template, scope, contratto/KOM e requisiti applicabili.

Il Document Register Cockpit può integrare documenti di controllo non presenti nella Document List.

## 12.3 Document Item

Oggetto logico leggero con:

- nome;
- tipo;
- ruolo competente;
- soggetto responsabile della disponibilità;
- eventuale data necessaria;
- stato corrente;
- ultima evidenza;
- data ultimo aggiornamento;
- collegamenti agli oggetti di progetto.

Revision management completo resta fuori V1.

## 12.4 Stato

Stati minimi:

- ATTESO;
- DISPONIBILE;
- DA AGGIORNARE;
- DA VERIFICARE;
- NON APPLICABILE.

Lo stato richiesto può dipendere dal contesto.

Lo stesso documento può essere sufficiente per una milestone e non per un'altra.

Verifica automatica solo se:

- criterio strutturato;
- stato strutturato;
- logica deterministica.

Negli altri casi:

- DA CONFERMARE;
- DA VERIFICARE.

## 12.5 Date

Il Document Control non duplica date del Master.

Un documento eredita il contesto temporale dal collegamento alla milestone/checkpoint quando possibile.

## 12.6 Attention

Un documento mancante genera Attention solo quando la sua assenza diventa rilevante rispetto a:

- fase;
- data necessaria;
- dipendenze;
- freschezza;
- milestone.

## 12.7 Evoluzione

Il registro è dinamico e tracciato.

Nuovi documenti possono essere:

- aggiunti manualmente;
- derivati da Change;
- proposti da AI;
- estratti da nuove fonti.

AI propone; umano conferma nei casi non deterministici.

---

# 13. Procurement Control

Missione:

> **controllare la disponibilità futura delle forniture rispetto alle date necessarie di progetto, usando ordini, forecast, fonti e dipendenze, senza eseguire il processo di acquisto.**

## 13.1 Procurement Item

Oggetto base:

> **fornitura rilevante per il controllo della commessa**

Gli ordini Galileo sono fonti collegate, non necessariamente l'oggetto principale.

Un Procurement Item può esistere anche prima dell'ordine.

## 13.2 Date principali

- Data necessaria;
- Data promessa;
- Data prevista;
- Data effettiva.

## 13.3 Checkpoint pre-ordine

Esempi:

- offerta necessaria entro;
- ordine necessario entro;
- approvazione tecnica necessaria entro.

## 13.4 Lead time

Ogni categoria Galileo può avere parametri standard configurabili.

Il singolo Item:

- eredita il default;
- può avere override;
- aggiorna il lead time secondo l'evoluzione reale della fase.

Progressione:

**standard categoria  
→ offerte ricevute  
→ fornitore selezionato  
→ conferma ordine  
→ forecast fornitore**

La storia non viene cancellata.

L'AI può estrarre lead time dalle offerte.

Dati ambigui richiedono conferma.

## 13.5 Freschezza

Ogni forecast può avere soglia di freschezza configurabile.

Forecast stale:

> **DA VERIFICARE**

non automaticamente ritardo.

## 13.6 Necessità multiple

Un Item può servire più milestone/checkpoint.

Il Cockpit conserva tutti i collegamenti.

La data necessaria corrente è la prima necessità attiva e confermata, salvo override motivato.

## 13.7 Stato operativo leggero

Esempi:

- DA QUOTARE;
- OFFERTE DISPONIBILI / IN VALUTAZIONE;
- FORNITORE DEFINITO / DA ORDINARE;
- ORDINATO;
- IN ESECUZIONE;
- DISPONIBILE / CONSEGNATO.

Non è un workflow bloccante.

## 13.8 Stati di controllo

- IN LINEA;
- DA VERIFICARE;
- A RISCHIO;
- IN RITARDO PREVISTO;
- DISPONIBILE.

## 13.9 Multi-PO / forniture parziali

Un Procurement Item può essere alimentato da più ordini/consegne.

Il Cockpit può suddividerlo in lotti/componenti di controllo quando necessario.

Le vere necessità possono essere corrette dal PM.

Il Cockpit non replica la distinta operativa Galileo.

## 13.10 Responsabilità

- PM = responsabilità sull'impatto progetto;
- Procurement Monitoring Owner = tipicamente Acquisti, configurabile;
- Technical Reference = opzionale.

## 13.11 Galileo

Galileo alimenta il Procurement Control come fonte strutturata.

Il Cockpit importa solo dati utili al controllo.

Matching:

- deterministico → automatico;
- ambiguo → conferma umana.

---

# 14. Technical Control

Missione:

> **controllare le condizioni tecniche, le informazioni e le verifiche necessarie affinché la commessa possa avanzare, senza eseguire la progettazione né sostituire i reparti tecnici.**

## 14.1 Structured Technical Control

Usa soprattutto **Technical Control Checkpoint**.

Le voci possono nascere da:

- template Brofind;
- KOM;
- contratto/specifice;
- documenti;
- comunicazioni;
- aggiunte manuali;
- proposte AI.

Il criterio è:

> se l'informazione resta indefinita, può compromettere una decisione, una milestone, una readiness, lo scope o generare una variazione?

Se sì, è candidata al monitoraggio.

## 14.2 Technical Alignment Monitoring

Il Cockpit può osservare comunicazioni e fonti per rilevare:

- temi tecnici ricorrenti non chiusi;
- indicazioni discordanti;
- decisioni riaperte;
- churn tecnico/documentale;
- checkpoint aperti troppo a lungo;
- richieste ripetute cliente;
- aumento delle interfacce coinvolte;
- disallineamento tra comunicazioni e stato Cockpit.

Il sistema non usa:

- sentiment;
- tono emotivo;
- numero di mail preso da solo.

Il segnale deve essere:

- breve;
- spiegabile;
- collegato a evidenze.

## 14.3 Segnale vs Attention

Il Technical Alignment distingue:

- segnale informativo;
- Attention.

L'Attention nasce quando il fenomeno è:

- persistente;
- crescente;
- materialmente rilevante;
- vicino a una milestone;
- collegato a una condizione aperta.

## 14.4 Nuovi checkpoint

Il Technical Alignment può proporre:

- collegamento a checkpoint esistente;
- creazione di nuovo checkpoint;
- nessuna formalizzazione.

La decisione viene registrata nello storico.

## 14.5 Stabilizzazione

Un segnale può diventare:

- STABILIZZATO;
- SCARTATO;
- ANCORA ATTIVO.

Una ricorrenza successiva è trattata come riapertura.

## 14.6 Visibilità progressiva

PM:

> vede segnali precoci.

Responsabile PM / Direzione:

> vede fenomeni persistenti o materialmente rilevanti.

Aumento di visibilità ≠ escalation operativa automatica.

## 14.7 Decisioni tecniche

Una decisione tecnica richiede Outcome esplicito confermato dal ruolo competente.

La sola assenza di nuove mail non chiude una decisione.

## 14.8 Readiness

Technical Control produce lo stato delle **condizioni tecniche**.

La readiness complessiva di milestone/gate appartiene al **Master Planner**, che aggrega tutti i domini.

---

# 15. Cost Control

Missione:

> **controllare l'evoluzione dei costi rispetto al budget, mostrando speso/impegnato, costi ancora attesi e forecast finale per VdA.**

Oggetto base:

> **VdA / posizione di budget Galileo**

## 15.1 Budget

- Budget iniziale — baseline immutabile;
- Budget corrente — autorizzato e tracciato;
- Forecast finale — previsione corrente.

Il budget corrente può cambiare solo tramite eventi autorizzati/tracciati.

## 15.2 Forecast

Concetto:

> costo osservato/impegnato + residuo atteso = forecast finale

La formula tecnica definitiva dipenderà dai dati reali Galileo.

Non viene congelata una formula unica.

La metodologia deve essere:

- evolutiva;
- configurabile;
- non hard-coded.

Segnali Galileo, incluso il flag di **ultimazione ordini della VdA**, possono cambiare la metodologia applicata.

## 15.3 AI Cost-to-Complete Assistant

L'AI può analizzare:

- dati Galileo;
- Procurement;
- Change;
- documenti;
- comunicazioni;
- altre fonti configurate.

Può:

- identificare costi futuri già espliciti;
- evidenziare elementi non quantificati;
- proporre ETC/Forecast;
- segnalare forecast non più coerente con nuove evidenze.

Il valore diventa operativo solo dopo conferma umana.

## 15.4 Freschezza

Ogni forecast ha:

- data;
- owner;
- stato di freschezza.

Nuove evidenze significative possono renderlo **DA RIVEDERE** prima della scadenza temporale.

## 15.5 Change economici

Un Change può influenzare il forecast prima di modificare il Budget corrente.

Restano distinti:

- Budget corrente;
- Forecast;
- esposizione economica da Change aperti.

## 15.6 Semaforo

Deriva da:

- Forecast vs Budget corrente;
- freschezza;
- esposizioni non recepite;
- qualità dati.

Soglie configurabili.

---

# 16. Project Economic Result

Missione:

> **controllare il risultato economico atteso della commessa confrontando valore contrattuale riconosciuto e forecast costi finali.**

Dati principali:

- Valore contratto iniziale;
- Valore contratto corrente riconosciuto;
- variazioni aperte separate;
- Forecast costi finali;
- risultato economico previsto;
- margine previsto.

Extra/minus non formalizzati:

> non modificano il valore riconosciuto.

Il segnale economico complessivo considera:

- risultato attuale;
- deterioramento rispetto alla baseline;
- qualità/freschezza del forecast;
- esposizioni aperte.

Billing e incassi restano domini distinti.

---

# 17. Billing Control

Missione:

> **controllare la coerenza tra eventi contrattuali che maturano la fatturazione, stato reale della commessa e stato della fatturazione registrato in Galileo.**

Il Cockpit non replica la fatturazione Galileo.

## 17.1 Maturazione

La maturazione deve derivare, quando possibile, da oggetti già controllati:

- Master milestone;
- Document Item;
- Control Checkpoint;
- altri eventi strutturati.

Se deterministico:

> maturazione automatica.

Se ambiguo/contrattuale:

> conferma umana.

## 17.2 Attention

Se:

> evento maturato + stato Galileo non coerente

oltre una tolleranza configurabile:

> Attention.

Il caso inverso viene segnalato come:

> DA VERIFICARE.

## 17.3 Sequenze contrattuali

Il Billing può controllare prerequisiti contrattuali rispetto a milestone successive.

Esempio:

> avviso merce pronta deve precedere spedizione/ritiro.

Segnale preventivo:

> prerequisito non completato + fase successiva vicina.

Segnale grave:

> fase successiva già superata + prerequisito ancora non completato.

Il Cockpit avvisa; non blocca fisicamente il processo.

## 17.4 Configurazione

Regole Billing e sequenze contrattuali derivano da:

- contratto;
- ordine;
- KOM;
- chiarimenti successivi.

AI può proporre; umano conferma.

---

# 18. Payment Control

La V1 mantiene questo dominio volutamente semplice.

Missione:

> **rappresentare numericamente quanto la commessa è coperta da fatturazione e incassi rispetto al reale stato di avanzamento, evidenziando squilibri.**

Dati tipici:

- avanzamento reale della commessa;
- fatturato;
- incassato.

Il Cockpit non diventa un sistema di credit management.

La metodologia per misurare numericamente l'avanzamento:

- deve essere trasparente;
- configurabile;
- validata;
- non viene hard-coded nel Product Model.

---

# 19. Project Overview

Missione:

> **permettere al PM di capire in pochi secondi se la commessa è sotto controllo, dove sono i segnali principali e dove entrare per capire il perché.**

La Project Overview:

- non introduce nuovi dati;
- aggrega i domini sottostanti;
- mostra contesto commessa;
- mostra semafori dei domini;
- mostra poche cause principali;
- mantiene drill-down verso il dettaglio.

Domini principali:

- Master;
- Technical;
- Procurement;
- Documents;
- Cost;
- Economic Result;
- Billing;
- Payment.

Attention / Criticità / Activity rilevanti sono mostrate separatamente.

Non serve un semaforo globale indipendente.

Lo stato complessivo è una sintesi derivata:

- numero aree critiche;
- numero aree in attenzione;
- principale causa/esposizione.

Il layout finale resta modificabile in fase UI/Figma.

---

# 20. Portfolio

Missione:

> **permettere a Direzione, PM e responsabili di capire rapidamente quali commesse richiedono attenzione, in quale dominio e con quale priorità.**

Mostra segnali sintetici dei domini.

Il Portfolio:

- non gestisce il progetto;
- non introduce nuove verità;
- serve a triage e prioritizzazione.

Ordinamento:

1. commesse con ROSSO;
2. commesse con GIALLO;
3. commesse senza Attention;
4. a parità:
   - numero di aree coinvolte;
   - prossimità a milestone sensibili.

Nessuno score sintetico opaco.

Il Portfolio è unico.

Può aprirsi con filtri/preferenze diverse per ruolo.

---

# 21. Attention / Criticità / Activity / Outcome

Semantica unica per tutti i domini.

## Attention

Segnale di controllo che richiede consapevolezza o verifica.

## Criticità

Problema formalizzato che richiede gestione e monitoraggio fino alla risoluzione.

## Activity

Intervento umano esplicito da eseguire.

Lifecycle:

- DA FARE;
- IN CORSO;
- IN ATTESA DI CONFERMA;
- CHIUSA;
- ANNULLATA.

## Outcome

Esito verificato di un'attività o decisione.

Regole:

- Attention non crea automaticamente Criticità;
- Criticità non crea automaticamente Activity salvo casi predefiniti;
- chiudere Activity non chiude automaticamente Criticità;
- messaggio ≠ Outcome;
- Outcome non elimina la necessità di rivalutare la condizione sottostante.

---

# 22. Alert fatigue / deduplicazione

Il Cockpit distingue:

1. osservazioni;
2. segnali informativi;
3. Attention.

Molte osservazioni correlate devono alimentare **una sola condizione di controllo**, non molti alert separati.

Un segnale scartato:

- viene ricordato;
- non viene riproposto senza nuove evidenze materiali.

Una condizione deterministica incompatibile:

- non può essere semplicemente silenziata;
- può essere presa in carico, giustificata o collegata a una decisione.

Quando una causa comune produce impatti in più domini:

> Project Overview e Portfolio devono poter raggruppare le conseguenze intorno alla causa principale.

---

# 23. History / Audit Trail

Ogni modifica significativa conserva:

- valore/stato precedente;
- nuovo valore/stato;
- data;
- autore/confermatore;
- motivo;
- fonte/evidenza;
- eventuale causa collegata.

Lo storico deve essere:

> **leggibile a livello progetto**

non un log tecnico del software.

Le ipotesi AI interne non mostrate all'utente non entrano nello storico.

Una proposta AI effettivamente presentata e:

- accettata;
- collegata;
- scartata

deve avere un esito tracciato.

---

# 24. Settings / Override Governance

Modello unico:

**Global Settings  
→ Project Configuration  
→ Item Override**

## 24.1 Global Settings

Contengono:

- default Brofind;
- soglie;
- template;
- categorie;
- policy;
- regole automatiche.

## 24.2 Project Settings

Configurano:

- scope;
- fonti;
- ruoli;
- soglie specifiche;
- gate;
- milestone;
- controlli;
- override di commessa.

## 24.3 Item Override

Consente eccezioni su:

- Procurement Item;
- Document Item;
- Checkpoint;
- VdA;
- altre entità.

Ogni override conserva:

- default;
- valore attivo;
- autore;
- data;
- motivo.

Gli override operativi sono flessibili.

Gli override che riducono controlli contrattuali/sensibili richiedono approvazione.

Una modifica globale non riscrive silenziosamente le commesse esistenti.

---

# 25. Post-completion / Residui

Il Cockpit distingue:

- **chiusura operativa della commessa**;
- **residui post-completion**.

Esempi:

- punch list;
- claim;
- documenti finali;
- attività residue;
- issue di garanzia monitorate.

La commessa può essere operativamente chiusa con residui aperti se questi hanno:

- owner;
- stato;
- aging;
- evidenza.

Ogni residuo può avere soglia aging configurabile.

Superamento soglia:

> Attention.

Persistenza ulteriore:

> aumento progressivo di visibilità / escalation al responsabile.

La V1 non diventa un sistema Service/Warranty completo.

---

# 26. Flessibilità e confrontabilità

Il Cockpit deve supportare commesse molto diverse per:

- complessità;
- milestone;
- dipendenze;
- documenti;
- procurement;
- scope;
- responsabilità.

La confrontabilità non deriva dall'avere gli stessi oggetti.

Deriva da:

> **stessa semantica di controllo, stessi livelli di segnalazione e stessi principi di drill-down.**

Il PM ha ampia libertà sulla configurazione operativa.

Non può cambiare arbitrariamente:

- significato dei semafori;
- Source/Freshness/Confidence;
- audit;
- lifecycle trasversale;
- controlli minimi sensibili;
- autorità AI.

---

# 27. Capacità V1 MUST HAVE

La V1 include:

1. Portfolio Control;
2. Project Overview;
3. Project Opening / Scope Profile;
4. Master Planner;
5. Readiness trasversale delle milestone;
6. Change Control;
7. Control Checkpoint;
8. Document Control;
9. Procurement Control;
10. Technical Control;
11. Technical Alignment Monitoring;
12. Cost Control per VdA;
13. AI Cost-to-Complete Assistant assistivo;
14. Project Economic Result;
15. Billing Control;
16. Payment Control semplice;
17. Operational Control:
   - Attention;
   - Criticità;
   - Activity;
   - Outcome;
18. Source / Freshness / Confidence;
19. Reconciliation;
20. History / Audit Trail;
21. Source Configuration;
22. Project Parties & Roles;
23. Settings / Override Governance;
24. Post-completion residual monitoring.

---

# 28. Explicit Out of Scope V1

Restano fuori:

- sostituzione Galileo / ERP;
- emissione ordini di acquisto;
- procurement execution;
- Gantt dettagliato / CPM / Primavera-like planning;
- engineering calculations;
- progettazione tecnica;
- requisiti tecnici completi tipo ALM;
- full EDMS;
- check-in/check-out documentale;
- transmittal workflow completo;
- gestione completa revisioni;
- firma documentale;
- emissione fatture;
- incasso / credit collection workflow;
- CRM;
- Service/Warranty Management completo;
- AI decisionale autonoma;
- AI che sceglie soluzioni tecniche/commerciali;
- auto-acceptance di obblighi contrattuali;
- risoluzione automatica di conflitti ambigui;
- modellazione completa di ogni workflow Brofind.

---

# 29. Parametri volutamente NON congelati nel Product Model

Non sono MODEL GAP:

- soglie numeriche;
- cataloghi definitivi;
- lead time standard;
- soglie di freschezza;
- formule finali Economic Forecast;
- metodo numerico definitivo dell'avanzamento Payment;
- layout UI;
- ordine e dimensione delle card;
- dettaglio grafico dei semafori;
- scelta tecnica shared mailbox vs cartella Outlook;
- modalità API/file/database di integrazione Galileo;
- pattern tecnico di folder watching;
- tuning dei modelli AI;
- naming definitivo di alcune entità UI.

Questi elementi verranno definiti nei gate successivi.

---

# 30. Red-team finale — esito

Il modello è stato stress-testato su:

- commesse incomplete;
- commesse molto diverse tra PM;
- fonti contraddittorie;
- alert fatigue;
- interventi eseguiti fuori Cockpit;
- rischio di data entry eccessivo;
- commesse che cambiano struttura;
- fonti ufficiali errate o stale;
- errori di conferma umana;
- commesse apparentemente verdi ma con dati non affidabili;
- una causa comune con impatti multi-dominio;
- chiusura operativa con residui aperti.

**Esito: PASS.**

Non sono emersi MODEL GAP strutturali che impediscano alla V1 di accompagnare una commessa dall'apertura alla chiusura.

---

# 31. Freeze

## USABLE CONTROL COCKPIT V1 — PRODUCT MODEL / SCOPE

**STATUS: FROZEN**

Da questo punto:

> **evidence → Product Strategy decision → canonical freeze → UI / implementation**

Nuove idee devono essere classificate.

Nessuna modifica semantica può essere introdotta implicitamente da:

- Figma;
- Codex;
- implementazione;
- convenienza tecnica;
- scorciatoie UI.

---

# 32. Next Gate

Il prossimo gate è:

> **CONCEPT UI / INFORMATION ARCHITECTURE**

Sequenza:

**Product Freeze  
→ Concept UI per superficie  
→ Interaction Contract  
→ UI Freeze / Figma  
→ Implementation Contract  
→ Codex / Enea  
→ Automated QA  
→ Functional & Visual Review  
→ UAT  
→ Pilot  
→ V1 Release**

Il dimostratore 13/10 deve essere una **anteprima credibile del modello operativo**, non l'intera V1 completa.
