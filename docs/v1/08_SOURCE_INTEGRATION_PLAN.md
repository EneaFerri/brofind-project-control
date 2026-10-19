# 08 — Collegamento delle fonti dati al Control Cockpit

**Stato:** PROPOSTA — piano di lavoro, nessuna modifica al codice
**Data:** 2026-10-06 · aggiornato 2026-10-12 (ambiente di posta)
**Fonti principali:** cartelle dati sul server aziendale · comunicazioni Outlook · ERP Galileo

> **Ambiente di posta Brofind (confermato 2026-10-12):** gli utenti usano Outlook con licenze **Microsoft 365**, ma le caselle **non sono su Exchange Online**. Conseguenze per questo piano:
> - **Microsoft Graph non è utilizzabile per leggere la posta**: le API mail di Graph funzionano solo su caselle Exchange Online. La Fase 3 si basa quindi sul protocollo esposto dal server di posta effettivo (da censire in Fase 0).
> - Il tenant Microsoft 365 include comunque **Microsoft Entra ID**: il login aziendale (OD-04, ADR-004) resta percorribile e non dipende da dove risiede la posta.

Questo documento descrive gli step per collegare le tre fonti al Cockpit nel rispetto del principio **READ MANY, WRITE LITTLE**: il Cockpit legge, non scrive mai nelle fonti.

---

## 1. Punto di partenza (v1.0.0)

Il Cockpit ha già un **Source Center** che lavora su file depositati in una cartella locale:

```
data_sources/<codice commessa>/
  Galileo/     workbook .xlsx in formato controllato (CONTROL_SNAPSHOT, CONTROL_LINES, INVOICES)
  Documenti/   .pdf, .docx, .xlsx
  Outlook/     .msg, .eml
```

| Capacità esistente | Dove |
|---|---|
| Scansione della cartella, impronta SHA-256, stato file (nuovo / invariato / modificato / non più presente) | `app/source_center.py` |
| Lettura testo da PDF, DOCX, EML, MSG | `app/source_readers.py` |
| Import Galileo con controlli di quadratura (ordini = ricevuto + residuo, totali = somma righe) | `app/b1_control_adapter.py` |
| Registro di ogni import riuscito o fallito | `ProjectSourceImport` |
| Estrazione campi dai documenti → revisione umana → valore operativo | `app/ai_analysis.py`, `ProjectExtractedField` |
| Radice delle fonti configurabile | variabile `BROFIND_SOURCE_ROOT` |

**Cosa manca** per le fonti reali: accesso diretto alle cartelle del server, collegamento a Outlook, estrazione automatica da Galileo, configurazione delle fonti per commessa, aggiornamento pianificato, controllo di freschezza e storico degli snapshot non modificabile (AD-002).

---

## 2. Architettura di riferimento

```
 Cartelle server ─┐
 Posta (IMAP/EWS)─┼─► Adapter (sola lettura) ─► Osservazioni + impronta ─► Read model storicizzato ─► Regole / superfici
 Galileo ─────────┘          │                                                  │
                             └─► Registro import (esito, errori, durata)         └─► Freschezza per fonte e commessa
```

Regole comuni a tutti gli adapter:

1. **Credenziali dedicate in sola lettura** (account di servizio), mai credenziali personali.
2. **Import idempotenti**: stesso contenuto (stessa impronta) = nessuna modifica; contenuto nuovo = nuovo snapshot, lo storico non si sovrascrive.
3. **Associazione alla commessa esplicita**: configurata, collegata o proposta e poi confermata da una persona (Data Contract §1.2).
4. **Freschezza misurata**: ogni fonte espone data dell'ultimo aggiornamento riuscito; oltre soglia il dato diventa *Da verificare*, mai verde.
5. **Errori visibili**: un import fallito non cancella i dati precedenti e compare nelle Fonti della commessa.
6. **Nessun dato reale nel repository**: test e demo usano solo dati fittizi o anonimizzati.

Il Cockpit gira su un server della rete aziendale (slice S12); da lì deve poter raggiungere file server, server di posta (IMAP/EWS), Microsoft Entra ID (solo login) e Galileo.

---

## 3. Fase 0 — Ricognizione (prima di scrivere codice)

Da svolgere con IT Brofind, Amministrazione, un PM pilota e, per Galileo, Sanmarco Informatica.

### Cartelle server
- [ ] Percorso radice delle commesse (es. `\\server\commesse\`) e struttura tipica delle sottocartelle.
- [ ] Regola di nomenclatura della cartella di commessa: contiene sempre il codice? È creata manualmente (oggi da Amministrazione)?
- [ ] Esiste uno schema di sottocartelle standard (contratto, documentazione tecnica, acquisti…)? Quanto è uniforme tra PM?
- [ ] Volumi: numero di file e dimensione media per commessa; formati presenti (PDF, DOCX, XLSX, DWG, scansioni).
- [ ] Dove stanno i documenti contrattuali (ordine, contratto, KOM) e la Document List, se esiste.

### Outlook
- [x] Brofind usa Microsoft 365 con Outlook; le caselle **non** sono su Exchange Online (confermato 2026-10-12).
- [ ] Dove risiedono le caselle: **Exchange Server on-premise** o **provider di posta esterno** (hosting IMAP/POP3)? Verificabile da IT, ad esempio dai record MX del dominio brofind.com.
- [ ] Protocolli di accesso abilitati sul server di posta: IMAP (con TLS), EWS (solo Exchange on-premise), POP3. È possibile un account di servizio dedicato?
- [ ] Le mail restano sul server o vengono scaricate in file `.pst` locali (POP3)? Nel secondo caso il server non contiene lo storico e la lettura diretta non è possibile.
- [ ] Il tenant Microsoft 365 usa il dominio brofind.com come dominio verificato e gli utenti accedono con l'account @brofind.com? (necessario per il login Entra ID, OD-04)
- [ ] Come sono organizzate oggi le mail di commessa: casella condivisa per commessa, cartella condivisa, codice commessa nell'oggetto, nessuna regola?
- [ ] Quali caselle è lecito leggere: solo caselle/cartelle di commessa dedicate (raccomandato) o anche caselle personali (sconsigliato)?
- [ ] Referente privacy/DPO e regole aziendali sul trattamento delle email.

### Galileo
- [ ] Versione di Galileo, installazione (on-premise / cloud) e database sottostante.
- [ ] Modalità di estrazione disponibili: export pianificati (Excel/CSV), viste di database in sola lettura, API/web service. Costi e tempi con Sanmarco.
- [ ] Viste/report usati oggi per il controllo (JMRP — nome da verificare —, interrogazione ordini, piano di fatturazione, scadenziario incassi).
- [ ] Mappatura codici: commessa madre, VdA, Centri di Analisi, categorie merceologiche.

**Esito della fase:** una scheda per fonte con meccanismo scelto, accessi richiesti, campi disponibili e commesse pilota (3–5, di cui una sana e una critica).

---

## 4. Fase 1 — Cartelle server (prima fonte da collegare)

Motivo della priorità: il Source Center lavora già su cartelle, il rischio tecnico è basso e il valore è alto (contratti, documenti, export).

| Step | Attività | Responsabile |
|---|---|---|
| 1.1 | Creare un **account di servizio** con permesso di sola lettura sulla radice delle commesse | IT |
| 1.2 | Rendere la condivisione accessibile dal server del Cockpit (montaggio SMB in sola lettura, oppure percorso UNC se il server è Windows) | IT |
| 1.3 | Estendere la configurazione da una radice unica a un **percorso per commessa** (Source Configuration, Data Contract §1.2), con proposta automatica della cartella in base al codice commessa e conferma del PM | Sviluppo |
| 1.4 | Definire la **mappatura sottocartelle → tipo di fonte** (contratto, documenti tecnici, export Galileo, mail esportate) come configurazione, non nel codice | Sviluppo + PM pilota |
| 1.5 | Scansione **incrementale pianificata** (es. ogni notte + pulsante "Aggiorna fonti"): confronto per data di modifica e dimensione, impronta solo sui file cambiati | Sviluppo |
| 1.6 | Limiti espliciti: formati supportati (PDF testuale, DOCX, XLSX, MSG, EML), dimensione massima, cartelle escluse; scansioni senza testo (OCR) fuori perimetro in questa fase | Sviluppo |
| 1.7 | Riconoscimento revisioni da nome file (es. `_RevB`) e collegamento ai Document Item (slice S8) | Sviluppo |
| 1.8 | Prova sulle commesse pilota, misura dei tempi di scansione, verifica che nessun file venga mai aperto in scrittura | Sviluppo + IT |

**Criterio di completamento:** per le commesse pilota il Cockpit mostra i file reali, segnala nuovi/modificati/rimossi, legge i documenti supportati e l'aggiornamento notturno gira senza intervento.

---

## 5. Fase 2 — Galileo

L'obiettivo è sostituire l'Excel preparato a mano con un'estrazione automatica, **mantenendo invariato il modello dati** (snapshot per VdA/Centro di Analisi e fatture).

### Opzioni, in ordine di preferenza da validare in Fase 0

| Opzione | Pro | Contro |
|---|---|---|
| **A. Viste di database in sola lettura** create con Sanmarco, lette dal Cockpit con utente dedicato | dati sempre aggiornati, nessun file intermedio | richiede intervento Sanmarco e accesso di rete al DB |
| **B. Export pianificati** (CSV/Excel) depositati da Galileo in una cartella del server | semplice, usa la Fase 1, nessun accesso al DB | ritardo pari alla frequenza dell'export; formato da congelare |
| **C. API / web service Galileo**, se disponibili | interfaccia stabile e documentata | disponibilità e costo da verificare |

Raccomandazione: partire con **B** (riusa l'adapter attuale, che già valida il formato) e passare ad **A** o **C** quando i campi sono stabilizzati.

### Dati da estrarre (Data Contract §1, §4, §6, §7)

| Area | Campi |
|---|---|
| Commessa | codice, cliente, descrizione, PM, commerciale, date principali, stato |
| Budget | budget iniziale e corrente per VdA e Centro di Analisi |
| Costi | ricevuto, costo uomo, spese generali per VdA |
| Ordini fornitore | righe d'ordine con fornitore, importo, data di consegna promessa, ricevuto, residuo, flag acquisti conclusi |
| Fatturazione attiva | piano di fatturazione, fatture emesse, scadenze |
| Incassi | importo **e data** di ogni incasso (oggi manca la data: vedi `IMPLEMENTATION_GAPS.md`) |

### Step

| Step | Attività | Responsabile |
|---|---|---|
| 2.1 | Mappatura campo per campo tra report Galileo e Data Contract, con esempi reali su una commessa chiusa | Amministrazione + Sviluppo |
| 2.2 | Scelta del meccanismo (A/B/C) e accordo con Sanmarco | IT + Direzione |
| 2.3 | Utente dedicato in sola lettura (opzione A/C) o cartella di destinazione degli export (opzione B) | IT / Sanmarco |
| 2.4 | Adapter Galileo che produce lo stesso snapshot di oggi; **snapshot immutabili** con impronta e data (chiude AD-002) | Sviluppo |
| 2.5 | Controlli di quadratura a ogni import (già presenti) + segnalazione di qualità dati quando non tornano | Sviluppo |
| 2.6 | Frequenza di aggiornamento (es. giornaliera) e soglia di freschezza per i dati economici | Amministrazione |
| 2.7 | **Esecuzione in parallelo** per 2–4 settimane: i numeri del Cockpit vengono confrontati con i report usati oggi | Amministrazione + PM pilota |

**Criterio di completamento:** gli snapshot delle commesse pilota si aggiornano senza intervento manuale e coincidono con i report Galileo di riferimento.

---

## 6. Fase 3 — Outlook

Outlook è solo il client: il Cockpit legge dal **server di posta** su cui risiedono le caselle. Poiché la posta non è su Exchange Online, Microsoft Graph è escluso; il meccanismo dipende dall'esito della Fase 0 (OD-20).

### Opzioni, in ordine di preferenza da validare in Fase 0

| Opzione | Quando si applica | Pro | Contro |
|---|---|---|---|
| **A. IMAP in sola lettura** su caselle di commessa dedicate | provider esterno o Exchange on-premise con IMAP abilitato | protocollo standard, indipendente dal fornitore; selezione della cartella in sola lettura (`EXAMINE`) e lettura senza segnare come letto (`BODY.PEEK`) | autenticazione con password dell'account di servizio (o password per app), da custodire con cura; nessun filtro lato server per commessa |
| **B. EWS in sola lettura** | solo Exchange Server on-premise | accesso nativo a caselle e cartelle condivise, sincronizzazione incrementale | legato a Exchange; account di servizio con permesso di lettura sulle sole caselle di commessa da configurare sul server |
| **C. Cartella di esportazione** (`.msg`/`.eml` sul server) | sempre; unica via se la posta è scaricata in `.pst` locali (POP3) | già supportata dalla Fase 1, nessun accesso al server di posta | manuale o semi-manuale; copertura dipende dalla disciplina dei PM |

Raccomandazione: **A** se il server di posta espone IMAP con TLS (vale sia per un provider esterno sia per Exchange on-premise), **B** solo se IMAP non è disponibile su Exchange on-premise, **C** come fase transitoria e come ripiego. Se in futuro Brofind migra la posta su Exchange Online, l'adapter può passare a Microsoft Graph (`Mail.Read` con accesso limitato alle caselle di commessa) senza cambiare il modello dati.

### Step

| Step | Attività | Responsabile |
|---|---|---|
| 3.1 | Decidere il **contenitore di commessa**: casella dedicata per commessa (es. indirizzo di commessa messo in copia o alimentato da regola di inoltro) o cartella condivisa, compatibilmente con il server di posta (OD-16; scelta tecnica lasciata aperta dal Product Freeze). Raccomandato: un contenitore dedicato per commessa, così il Cockpit non legge mai caselle personali | Direzione + IT |
| 3.2 | Scegliere il meccanismo (A/B/C) in base al server di posta censito in Fase 0 (OD-20) | IT + Sviluppo |
| 3.3 | Creare un **account di servizio** con accesso in sola lettura **solo ai contenitori di commessa** (credenziali dedicate sul provider, oppure permessi di lettura su Exchange on-premise); nessun accesso a caselle personali | IT |
| 3.4 | Conservare password o certificati fuori dal repository (variabili d'ambiente o archivio segreti del server); connessioni solo cifrate (IMAPS / HTTPS) | IT + Sviluppo |
| 3.5 | Adapter posta: sincronizzazione **incrementale** (IMAP: `UIDVALIDITY` + `UID`; EWS: stato di sincronizzazione della cartella), deduplica per `Message-ID`, salvataggio di mittente, destinatari, data, oggetto, testo e riferimento agli allegati; l'adapter non sposta, non cancella e non marca i messaggi | Sviluppo |
| 3.6 | Associazione alla commessa: automatica se il contenitore è dedicato; proposta da confermare se si usa il codice nell'oggetto | Sviluppo |
| 3.7 | Analisi dei segnali (solleciti, richieste documenti, promesse di pagamento) con il motore esistente: restano **proposte da confermare** | Sviluppo |
| 3.8 | Valutazione privacy con il DPO: minimizzazione dei dati, tempi di conservazione, informativa ai dipendenti | DPO + Direzione |

Il Cockpit **non invia** email: l'accesso richiesto è solo di lettura (nessun SMTP).

**Fase transitoria:** finché l'adapter non è attivo, i PM possono salvare le mail rilevanti (`.msg`/`.eml`) nella cartella Outlook della commessa sul server; la Fase 1 le legge già.

**Criterio di completamento:** per le commesse pilota le nuove mail compaiono nel Cockpit entro la frequenza concordata, senza duplicati e senza accesso a caselle non autorizzate.

---

## 7. Fase 4 — Esercizio

| Tema | Attività |
|---|---|
| Pianificazione | job periodici per scansione cartelle, import Galileo e sincronizzazione della posta, con blocco per evitare esecuzioni sovrapposte |
| Monitoraggio | stato di ogni fonte e dell'ultimo aggiornamento in una pagina di amministrazione; avviso se una fonte non si aggiorna oltre soglia |
| Freschezza | soglie per fonte nei Settings (globale → commessa → item), mostrate all'utente |
| Sicurezza | account di servizio separati per fonte, permessi minimi, rotazione dei segreti, log senza contenuti sensibili |
| Backup | database del Cockpit; le fonti restano negli originali e sono sempre ricostruibili |
| Documentazione | guida per IT su configurazione, credenziali e ripristino |

---

## 8. Sequenza e collegamento con il piano

| Fase | Dipende da | Slice collegate |
|---|---|---|
| 0 Ricognizione | — | — (può partire subito) |
| 1 Cartelle server | server aziendale (S12) o accesso di prova | S8 Documents |
| 2 Galileo | Fase 1 (se export su cartella) | S4 Economics, S5 Billing & Payment, S6 Procurement |
| 3 Outlook | server di posta censito e meccanismo scelto (OD-20), decisione contenitore (OD-16), DPO (OD-19) | S9 Technical, S10 Conversazioni |
| 4 Esercizio | Fasi 1–3 | S12 |

## 9. Decisioni da aggiungere al registro

| ID | Decisione | Proposta |
|---|---|---|
| OD-15 | Meccanismo di estrazione Galileo | partire da export pianificati su cartella, poi viste DB in sola lettura |
| OD-16 | Contenitore Outlook di commessa | casella o cartella condivisa dedicata per commessa, compatibile con il server di posta |
| OD-17 | Struttura standard delle cartelle di commessa | definirla con i PM; il Cockpit propone e il PM conferma la mappatura |
| OD-18 | Frequenza di aggiornamento e soglie di freschezza per fonte | giornaliera per Galileo e cartelle; oraria per Outlook |
| OD-19 | Valutazione privacy per la lettura delle email | DPIA con il DPO prima della Fase 3 |
| OD-20 | Meccanismo di lettura della posta (non su Exchange Online) | IMAP in sola lettura se disponibile; EWS solo su Exchange on-premise; cartella di esportazione come ripiego |
