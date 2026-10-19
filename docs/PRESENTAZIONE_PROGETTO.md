# Brofind Control Cockpit — presentazione del progetto

**Documento di presentazione della bozza** · ottobre 2026 · versione demo v1.0.1

> Le cifre di costo e le tempistiche sono **stime indicative** per orientare la decisione, da confermare con IT, fornitori e Amministrazione. I dati mostrati nella demo sono fittizi o anonimizzati.

---

## 1. In una frase

Il Control Cockpit è il **cruscotto unico delle commesse Brofind**: legge i dati che già esistono (Galileo, cartelle di commessa sul server, posta Outlook), confronta *cosa dovrebbe essere vero oggi* con *cosa risulta vero oggi*, e mostra a ciascuno dove serve attenzione, prima che un problema diventi un ritardo, un costo o un incasso mancato.

Non sostituisce nessun sistema: **li osserva e li mette in relazione**.

---

## 2. Il problema che risolve

Oggi le informazioni su una commessa sono distribuite:

| Dove | Cosa contiene | Il limite |
|---|---|---|
| Galileo | costi, ordini, fatture, incassi | numeri corretti, ma senza contesto di fase e scadenze |
| Cartella di commessa | contratto, documenti tecnici, revisioni | si sa cosa c'è, non cosa *manca* |
| Outlook | solleciti, promesse, richieste del cliente | l'informazione resta nella casella di chi l'ha ricevuta |
| Planner / Excel personali | date e milestone | versioni diverse per persone diverse |

La conseguenza è nota a tutti: per sapere "come sta la commessa" servono telefonate, riunioni di allineamento e ricostruzioni a memoria. I segnali deboli (un ordine che slitta, un documento non ancora inviato, una fattura scaduta) emergono tardi, quando i margini di manovra sono già ridotti.

---

## 3. A chi serve

| Ruolo | Cosa ci trova | Domanda a cui risponde |
|---|---|---|
| **Direzione** | Portfolio di tutte le commesse con semaforo per area | "Dove devo guardare questa settimana?" |
| **Project Manager** | Panoramica e dettaglio della propria commessa, criticità e attività aperte | "Cosa sta per andare storto e chi se ne sta occupando?" |
| **Commerciale** | Contratto, condizioni di fatturazione, varianti | "Cosa abbiamo promesso e cosa stiamo consegnando?" |
| **Acquisti** | Stato degli ordini rispetto alla data di bisogno | "Quali forniture rischiano di bloccare il montaggio?" |
| **Amministrazione** | Maturato, fatturato, incassato, esposizione | "Cosa possiamo fatturare e cosa è scaduto?" |
| **Ufficio Tecnico / E&I / Software** | Decisioni tecniche e documenti da emettere | "Cosa aspetta una nostra decisione o un nostro documento?" |
| **Service** | Storico della commessa al passaggio in assistenza | "Cosa è stato deciso e perché?" |

Ognuno vede **solo ciò che il suo ruolo prevede**: i permessi sono configurabili e verificati dal server, non solo nascosti nell'interfaccia.

---

## 4. Come si usa

### 4.1 Il linguaggio comune: quattro colori

| Colore | Significato |
|---|---|
| 🟢 **Verde** | in linea **e** dati aggiornati |
| 🟡 **Giallo** | qualcosa da verificare, rischio concreto ma non ancora un problema |
| 🔴 **Rosso** | problema accertato: ritardo, blocco, scostamento confermato |
| ⚪ **Grigio** | dati mancanti o vecchi: **non sappiamo**, e lo diciamo |

Il grigio è la regola più importante: il Cockpit non mostra mai "tutto bene" quando in realtà mancano informazioni.

### 4.2 Il percorso tipico

1. **Portfolio**: la mattina, Direzione e PM aprono l'elenco delle commesse ordinate per priorità di controllo. Ogni riga ha sei semafori (Master, Technical, Procurement, Documents, Economics, Billing).
2. **Panoramica della commessa**: un clic sulla commessa mostra la sintesi: fase, prossimo traguardo, principale esposizione economica, segnali aperti con la loro causa.
3. **Aree di controllo**: dal semaforo si scende nel dettaglio dell'area, fino al singolo ordine, documento o fattura.
4. **Fonti**: per ogni dato si vede da dove viene, quando è stato letto e quanto è affidabile. Nessun numero senza provenienza.
5. **Criticità e Attività**: se un segnale richiede un intervento, il PM apre una Criticità e assegna un'Attività alla funzione competente (es. Amministrazione per un sollecito di pagamento). Chi la riceve risponde nel Cockpit; il PM verifica l'esito.
6. **Storico**: tutto ciò che è stato deciso, confermato o modificato resta tracciato con autore, data e motivo.

### 4.3 Le otto superfici

| Superficie | A cosa serve |
|---|---|
| Portfolio | vista d'insieme di tutte le commesse |
| Panoramica | sintesi di una commessa |
| Master Planner | fasi, traguardi, prontezza per il passo successivo |
| Technical Control | decisioni tecniche, punti da confermare con il cliente |
| Procurement Control | ordini fornitore: data di bisogno, promessa, previsione |
| Document Control | documenti richiesti dal contratto e loro stato |
| Economic Control | budget, speso, impegnato, previsione a finire |
| Billing & Payment | maturato, fatturato, incassato, scaduto |

### 4.4 Il ruolo dell'AI

L'assistente AI **aiuta a leggere**, non decide. Può:

- estrarre dai documenti i dati chiave (valore contratto, penali, condizioni di pagamento);
- spiegare perché un semaforo è giallo o rosso;
- confrontare fonti e segnalare incoerenze;
- riassumere la storia di una commessa o un filone di email.

Non può scegliere fornitori o soluzioni tecniche, autorizzare costi, modificare obblighi contrattuali o chiudere decisioni. **Ogni proposta dell'AI diventa un dato solo dopo la conferma di una persona.**

---

## 5. Cosa il Cockpit non è

Per evitare equivoci (e sovrapposizioni con sistemi esistenti), il Cockpit **non** è un ERP, un sistema acquisti, un Gantt di dettaglio, un archivio documentale completo, un sistema contabile o un CRM. Non scrive mai nei sistemi di origine: **legge molto, scrive poco**, solo il proprio livello di controllo (segnali, attività, decisioni, conferme).

---

## 6. Dove siamo oggi

| Elemento | Stato |
|---|---|
| Modello di prodotto e perimetro V1 | definito e congelato |
| Interfaccia delle 8 superfici | realizzata (demo v1.0) |
| Caso dimostrativo completo (commessa con sforamento e fattura scaduta) | funzionante |
| Lettura di file Galileo, documenti PDF/Word ed email da cartella | funzionante su dati di prova |
| Estrazione dati dai documenti con conferma umana | funzionante (senza modello AI esterno) |
| Login aziendale, ruoli, esercizio su server | da realizzare |
| Collegamento automatico a Galileo, server e posta | da realizzare |
| Alcuni dati delle superfici (fasi, previsioni, stato acquisti di dettaglio) | mostrati come "non disponibile" finché il modello non li fornisce |

La demo gira su un singolo PC. Il passo successivo è portarla **in rete aziendale** su un gruppo pilota.

---

## 7. Prossimi step

### Fase 0: ricognizione (subito, nessun costo di sviluppo)

- Con **IT**: dove installare il server, come raggiungere le cartelle di commessa, dove risiede la posta (il server di posta non è Exchange Online: va capito quale protocollo di lettura è disponibile), conferma del login con account @brofind.com.
- Con **Amministrazione**: quali report Galileo si usano oggi per il controllo, macro-famiglie di costo, date di incasso.
- Con il **fornitore di Galileo**: modalità di estrazione disponibili (export pianificati, viste in sola lettura, API) e relativi costi.
- Con i **PM**: struttura standard delle cartelle di commessa e contenitore email dedicato per commessa.
- Con il **DPO**: valutazione privacy per la lettura delle email.
- **Scelta di 3–5 commesse pilota**, almeno una sana e una critica.
- **Nomina di un Product Owner** interno che approvi i passaggi.

### Fase 1: pilota in rete aziendale

Login aziendale e ruoli, installazione sul server, collegamento alle cartelle di commessa reali, uso quotidiano da parte di un gruppo ristretto (Direzione + 2–3 PM + Amministrazione).

### Fase 2: dati economici automatici

Estrazione da Galileo al posto dell'Excel preparato a mano. **Esecuzione in parallelo** per 2–4 settimane: i numeri del Cockpit vengono confrontati con i report usati oggi prima di fidarsene.

### Fase 3: comunicazioni e aree di controllo complete

Lettura della posta di commessa, completamento di Acquisti, Documenti, Master Planner, Technical, Criticità/Attività, assistente AI.

### Fase 4: estensione a tutte le commesse

Formazione, estensione a tutti i PM e alle funzioni, revisione delle soglie sulla base dell'uso reale.

---

## 8. Tempistiche indicative

Ipotesi: **uno sviluppatore dedicato** con supporto IT a chiamata e disponibilità dei referenti di funzione. Con risorse diverse i tempi cambiano in proporzione.

| Fase | Durata stimata | Risultato |
|---|---|---|
| 0 · Ricognizione | 2–4 settimane | schede delle fonti, commesse pilota, decisioni aperte chiuse |
| 1 · Pilota in rete | 6–8 settimane | Cockpit su server aziendale, login, cartelle reali, gruppo pilota attivo |
| 2 · Galileo automatico | 6–10 settimane (incluso parallelo) | dati economici e fatturazione aggiornati senza intervento manuale |
| 3 · Posta e superfici complete | 3–4 mesi | V1 completa sulle commesse pilota |
| 4 · Estensione | 1–2 mesi | tutte le commesse attive, tutti i ruoli |

**Traguardi:**

- **~3 mesi**: pilota utilizzabile in rete aziendale su dati reali.
- **~6–9 mesi**: V1 completa ed estesa all'azienda.

Le fasi 2 e 3 possono in parte sovrapporsi; il vincolo principale sono i tempi esterni (fornitore Galileo, valutazione privacy, IT).

---

## 9. Costi di avvio e di esercizio

### 9.1 Infrastruttura in rete aziendale

| Voce | Opzione economica | Opzione dedicata | Note |
|---|---|---|---|
| Server applicativo | **0–500 €** (macchina virtuale sull'infrastruttura esistente) | **2.000–4.000 €** una tantum (server fisico piccolo) | requisiti modesti: 4 CPU, 16 GB RAM, 200 GB disco |
| Sistema operativo | **0 €** (Linux) | **~1.000–1.500 €** (Windows Server Standard) + eventuali licenze d'accesso | da decidere con IT |
| Database (PostgreSQL) | **0 €** | 0 € | open source, gira sullo stesso server |
| Login aziendale (Microsoft Entra ID) | **0 €** | 0 € | già incluso nelle licenze Microsoft 365 in uso |
| Certificato HTTPS | **0 €** (certificato interno) | 50–300 €/anno | |
| Backup | **0 €** (procedure esistenti) | 100–300 €/anno di spazio aggiuntivo | il database del Cockpit è piccolo; le fonti restano negli originali |

**Totale infrastruttura: da ~0 € (riuso di quanto esiste) a ~5.000 € una tantum**, più costi annui trascurabili.

### 9.2 Collegamento alle fonti

| Voce | Stima | Note |
|---|---|---|
| Estrazione dati da Galileo (fornitore) | **1.500–6.000 €** una tantum | 2–6 giornate di consulenza per export o viste in sola lettura; **da far quotare** |
| Lettura posta | **0 €** di licenze | serve un account di servizio in sola lettura sui contenitori di commessa |
| Valutazione privacy (DPIA) | **0–3.000 €** | interna se c'è un DPO, altrimenti consulenza |
| Tempo IT interno | 5–10 giornate distribuite | installazione, accessi, account di servizio |

### 9.3 Intelligenza artificiale

L'AI è **opzionale e modulare**: il Cockpit funziona anche senza, con l'estrazione deterministica già presente. Se attivata, si paga a consumo tramite API. Prezzi di listino delle API Anthropic (ottobre 2026, in USD per milione di token: un milione di token ≈ 750.000 parole):

| Modello | Uso tipico | Input | Output |
|---|---|---|---|
| Claude Haiku 5.5 | classificazione email, estrazioni semplici | $0,10 | $0,50 |
| Claude Sonnet 5.5 | assistente quotidiano, riassunti, confronti | $2 | $10 |
| Claude Opus 5.5 | analisi complesse di contratti e documenti lunghi | $4 | $20 |

**Scenario d'uso stimato** (20 utenti, 10 domande al giorno ciascuno, ~4.400 domande al mese, ciascuna con il contesto della commessa):

| Configurazione | Costo mensile stimato |
|---|---|
| Assistente su Sonnet 5.5 | **~100–250 €/mese** (la parte bassa con la cache del contesto) |
| Assistente su Opus 5.5 | **~200–450 €/mese** |
| Classificazione automatica della posta su Haiku 5.5 | **< 20 €/mese** |
| Prima lettura di tutto l'archivio documentale (una tantum, elaborazione notturna a prezzo ridotto) | **~50–200 €** |

Un **tetto di spesa mensile** si imposta direttamente sulla console del fornitore. Gli stessi modelli sono acquistabili anche tramite il marketplace Microsoft (Microsoft Foundry), utile se si preferisce un'unica fatturazione con Microsoft 365.

**Prima di attivare l'AI** vanno decisi con Direzione e IT: fornitore, quali dati possono uscire dalla rete aziendale, tempi di conservazione presso il fornitore. Fino ad allora l'assistente non invia nulla all'esterno.

### 9.4 Riepilogo

| | Una tantum | Ricorrente |
|---|---|---|
| Infrastruttura | 0–5.000 € | ~0–600 €/anno |
| Fonti e privacy | 1.500–9.000 € | — |
| AI (se attivata) | 50–200 € | ~1.500–5.500 €/anno |
| **Totale fuori sviluppo** | **~1.500–14.000 €** | **~1.500–6.000 €/anno** |

Il costo principale resta il **tempo di sviluppo e dei referenti interni**, da valorizzare secondo il modello scelto (sviluppo interno, collaborazione esterna o mista).

---

## 10. Come cambierà il modo di lavorare

### 10.1 Struttura dei dati aziendali

Per funzionare, il Cockpit richiede alcune regole semplici che, una volta adottate, migliorano l'ordine dei dati per tutta l'azienda:

- **una cartella di commessa con struttura standard**: si sa dove sta il contratto, dove sta la documentazione tecnica, dove stanno gli export;
- **un contenitore email per commessa**: la corrispondenza non resta più nelle caselle personali;
- **codici coerenti tra Galileo e commessa**: voci di analisi e famiglie di costo mappate una volta per tutte;
- **ogni dato con la sua provenienza**: fonte, data, autore. Si smette di discutere su "quale Excel è quello giusto";
- **storico non modificabile**: ogni aggiornamento crea una nuova versione, quella precedente resta consultabile.

Nel tempo questo produce un **archivio strutturato di commesse concluse**: costi reali per famiglia, tempi effettivi di fornitura, scostamenti ricorrenti. È la base per preventivi più accurati e per previsioni più affidabili.

### 10.2 Gestione del lavoro

- **Meno riunioni di allineamento**: lo stato è visibile a tutti, le riunioni si concentrano sulle decisioni.
- **Segnali anticipati**: un ordine in ritardo rispetto alla data di bisogno emerge quando c'è ancora tempo per intervenire.
- **Nessun reinserimento**: se un dato è già in Galileo o in cartella, nessuno deve ricopiarlo.
- **Responsabilità chiare**: ogni Criticità ha un responsabile, ogni Attività un destinatario e un esito da verificare. Chiudere un'attività non significa automaticamente aver risolto il problema.
- **Passaggi di consegne più semplici**: da Commerciale a PM, da PM ad Acquisti, dalla commessa al Service, con la storia completa disponibile.

### 10.3 Coesione aziendale

- **Un linguaggio comune**: verde, giallo, rosso, grigio significano la stessa cosa per tutti, dalla Direzione all'Ufficio Tecnico.
- **Visibilità reciproca**: ogni funzione vede come il proprio lavoro incide sul risultato della commessa (un documento in ritardo blocca una milestone, che blocca una fattura).
- **Trasparenza sui dati mancanti**: il grigio non è una colpa ma un'informazione; spinge a completare le fonti invece di nascondere l'incertezza.
- **Inserimento dei nuovi colleghi**: chi arriva trova commesse leggibili e una storia delle decisioni, non solo file sparsi.

---

## 11. Evoluzioni possibili dopo la V1

Idee **non incluse** nel perimetro attuale, da valutare dopo l'uso reale:

- analisi trasversali tra commesse (fornitori più puntuali, scostamenti tipici per tipo di impianto);
- previsioni di fine commessa basate sullo storico delle commesse concluse;
- report periodici automatici per Direzione e, eventualmente, per il cliente;
- lettura di documenti scansionati (OCR) e disegni;
- integrazione con il planner di produzione;
- raccolta strutturata delle lezioni apprese a fine commessa.

---

## 12. Sicurezza nella gestione dei dati

Il Cockpit mette insieme informazioni economiche, contrattuali e di corrispondenza: per questo la sicurezza è parte del progetto fin dall'inizio, non un'aggiunta finale.

### 12.1 I dati restano in azienda

- Il Cockpit gira su un **server della rete aziendale**, raggiungibile solo dall'interno (o tramite l'eventuale VPN aziendale).
- Il database del Cockpit è **sullo stesso server**, non in un cloud esterno.
- L'applicazione **non usa servizi esterni** per funzionare: niente librerie caricate da Internet, niente analisi di utilizzo di terze parti.
- L'unica eccezione possibile è l'assistente AI, che resta **spento finché la Direzione non decide** quali dati possono essere inviati e a quale fornitore (vedi 12.6).

### 12.2 Le fonti non vengono mai modificate

- Il Cockpit accede a Galileo, alle cartelle di commessa e alla posta con **account di servizio dedicati e in sola lettura**, mai con le credenziali personali di un collega.
- Ogni account vede **solo ciò che serve**: le cartelle delle commesse, i contenitori email di commessa (**mai le caselle personali**), le viste Galileo concordate.
- Non può cancellare, spostare o modificare nulla: anche in caso di errore o di attacco al Cockpit, **i dati di origine restano intatti**.
- Il Cockpit **non invia email** e non scrive in Galileo.

### 12.3 Chi entra e cosa vede

- **Accesso con l'account aziendale @brofind.com** tramite Microsoft Entra ID, lo stesso di Microsoft 365. Valgono le regole già in vigore: password aziendale, autenticazione a due fattori se attiva, disattivazione automatica quando un collega lascia l'azienda.
- **Permessi per ruolo**, configurabili: ad esempio un PM vede le proprie commesse, gli Acquisti vedono ciò che riguarda il loro reparto, la Direzione vede tutto.
- I permessi sono **verificati dal server a ogni operazione**, non solo nascondendo i pulsanti: chi non ha il permesso non può leggere né modificare, nemmeno chiamando direttamente l'applicazione.
- Ogni combinazione ruolo × operazione è coperta da **test automatici** che bloccano il rilascio se un permesso non funziona come previsto.

> **Stato attuale:** la demo usa un selettore di utenti di prova e ha un controllo dei permessi ancora incompleto. Login aziendale e autorizzazione completa sono il **primo intervento** previsto, prima che qualsiasi dato reale entri nel pilota. La modalità demo è rifiutata all'avvio in configurazione di produzione.

### 12.4 Protezione tecnica

| Ambito | Misura |
|---|---|
| Trasmissione | connessioni solo cifrate (HTTPS) tra browser e server, e verso posta e database |
| Sessioni | cookie protetti e firmati, non leggibili da script, validi solo su connessione cifrata |
| Credenziali | password degli account di servizio conservate sul server, **mai nel codice**; rotazione periodica |
| Registri tecnici | i log di funzionamento non contengono il testo di documenti o email |
| Codice sorgente | nessun dato reale di clienti o commesse nel repository; test e demo usano solo dati fittizi o anonimizzati |
| Aggiornamenti | dipendenze software con versioni fissate e verificate prima di ogni rilascio |

### 12.5 Tracciabilità e integrità

- **Ogni modifica è tracciata**: chi, quando, valore precedente e nuovo, motivo.
- **Lo storico non si cancella**: ogni importazione crea una nuova versione, la precedente resta consultabile. È sempre possibile ricostruire cosa sapevamo in una certa data e perché è stata presa una decisione.
- **Controlli di quadratura** a ogni import da Galileo: se i numeri non tornano, il dato viene segnalato e non mostrato come affidabile.
- **Un import fallito non cancella i dati precedenti** e compare come errore visibile.

### 12.6 Assistente AI e dati aziendali

Se e quando l'AI verrà attivata:

- **Decisione esplicita** di Direzione e IT su fornitore, tipi di dati inviabili e tempi di conservazione presso il fornitore, prima dell'attivazione.
- **Contratto commerciale API**: con i fornitori principali (Anthropic, o Microsoft Foundry) i dati inviati via API **non vengono usati per addestrare i modelli** secondo le condizioni commerciali standard. Conservazione, eventuale *zero data retention* e area geografica di elaborazione vanno **verificati e fissati nel contratto**.
- **Minimizzazione**: all'AI si invia solo il contesto necessario alla domanda, non l'intero archivio.
- **Tetto di spesa** e registro delle richieste per controllare l'uso.
- **Nessuna azione automatica**: l'AI propone, una persona conferma. Ogni proposta mostrata è registrata come accettata o scartata.

### 12.7 Privacy (GDPR)

- **Valutazione d'impatto (DPIA)** con il DPO **prima** di attivare la lettura delle email.
- **Informativa ai dipendenti** sul trattamento delle comunicazioni di commessa.
- Lettura limitata ai **contenitori di commessa dedicati**; dati personali ridotti al necessario (mittente, destinatari, data, oggetto, testo pertinente).
- **Tempi di conservazione** definiti per tipo di dato, con cancellazione o anonimizzazione delle commesse chiuse oltre il termine stabilito.

### 12.8 Continuità

- **Backup giornaliero** del database del Cockpit, inserito nelle procedure di backup aziendali, con **prova di ripristino** periodica.
- Le fonti restano negli originali: in caso di perdita totale del server, il Cockpit si **ricostruisce rileggendo le fonti**. Si perderebbero solo le annotazioni proprie del Cockpit (decisioni, conferme, attività), che sono quelle protette dal backup.
- Pagina di amministrazione con lo stato di ogni fonte e **avviso** se un aggiornamento non avviene.

---

## 13. Rischi e come li gestiamo

| Rischio | Contromisura |
|---|---|
| I dati di origine sono incompleti o disordinati | il Cockpit lo rende visibile (grigio) invece di nasconderlo; la Fase 0 definisce le regole minime |
| Scarsa adozione ("l'ennesimo strumento") | pilota piccolo, nessun reinserimento di dati, valore visibile dal primo giorno per Direzione e PM |
| Dipendenza da fornitori esterni (Galileo, posta) | partenza da export su cartella, che non richiede integrazioni; collegamento diretto solo dopo |
| Privacy delle email | lettura solo di contenitori di commessa dedicati, mai caselle personali; valutazione con il DPO prima dell'attivazione |
| Fiducia nei numeri | esecuzione in parallelo con i report attuali prima di sostituirli |
| Uso improprio dell'AI | l'AI propone, le persone confermano; nessun dato esce dalla rete senza una decisione esplicita |

---

## 14. Cosa chiediamo per partire

1. **Via libera alla Fase 0** (ricognizione, 2–4 settimane, nessun costo esterno).
2. **Un Product Owner** che approvi i passaggi e le priorità.
3. **Un referente IT** e la disponibilità di una macchina per il pilota.
4. **3–5 commesse pilota** e i rispettivi PM.
5. **Richiesta di quotazione** al fornitore di Galileo per l'estrazione dati.
