# 08 — Collegamento delle fonti dati al Control Cockpit

**Stato:** PROPOSTA — piano di lavoro, nessuna modifica al codice
**Data:** 2026-10-06
**Fonti principali:** cartelle dati sul server aziendale · comunicazioni Outlook · ERP Galileo

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
 Outlook (Graph) ─┼─► Adapter (sola lettura) ─► Osservazioni + impronta ─► Read model storicizzato ─► Regole / superfici
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

Il Cockpit gira su un server della rete aziendale (slice S12); da lì deve poter raggiungere file server, Microsoft 365 e Galileo.

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
- [ ] Brofind usa Microsoft 365 / Exchange Online? (OD-04)
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

### Meccanismo raccomandato: Microsoft Graph in sola lettura

| Step | Attività | Responsabile |
|---|---|---|
| 3.1 | Decidere il **contenitore di commessa**: casella condivisa per commessa o cartella condivisa (OD aperta nel Product Freeze §29). Raccomandato: un contenitore dedicato per commessa, così il Cockpit non legge mai caselle personali | Direzione + IT |
| 3.2 | Registrare un'applicazione in **Microsoft Entra ID** con permesso `Mail.Read` di tipo applicazione, con consenso amministratore | IT |
| 3.3 | Limitare l'accesso **solo ai contenitori di commessa** tramite Application Access Policy / RBAC di Exchange Online | IT |
| 3.4 | Conservare il segreto o il certificato dell'applicazione fuori dal repository (variabili d'ambiente o archivio segreti del server) | IT + Sviluppo |
| 3.5 | Adapter Outlook: sincronizzazione **incrementale** (delta query), deduplica per identificativo del messaggio, salvataggio di mittente, destinatari, data, oggetto, testo e riferimento agli allegati | Sviluppo |
| 3.6 | Associazione alla commessa: automatica se il contenitore è dedicato; proposta da confermare se si usa il codice nell'oggetto | Sviluppo |
| 3.7 | Analisi dei segnali (solleciti, richieste documenti, promesse di pagamento) con il motore esistente: restano **proposte da confermare** | Sviluppo |
| 3.8 | Valutazione privacy con il DPO: minimizzazione dei dati, tempi di conservazione, informativa ai dipendenti | DPO + Direzione |

Il Cockpit **non invia** email: il permesso richiesto è solo di lettura.

**Fase transitoria:** finché Graph non è attivo, i PM possono salvare le mail rilevanti (`.msg`/`.eml`) nella cartella Outlook della commessa sul server; la Fase 1 le legge già.

**Criterio di completamento:** per le commesse pilota le nuove mail compaiono nel Cockpit entro la frequenza concordata, senza duplicati e senza accesso a caselle non autorizzate.

---

## 7. Fase 4 — Esercizio

| Tema | Attività |
|---|---|
| Pianificazione | job periodici per scansione cartelle, import Galileo e sincronizzazione Outlook, con blocco per evitare esecuzioni sovrapposte |
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
| 3 Outlook | Entra ID (OD-04), decisione contenitore, DPO | S9 Technical, S10 Conversazioni |
| 4 Esercizio | Fasi 1–3 | S12 |

## 9. Decisioni da aggiungere al registro

| ID | Decisione | Proposta |
|---|---|---|
| OD-15 | Meccanismo di estrazione Galileo | partire da export pianificati su cartella, poi viste DB in sola lettura |
| OD-16 | Contenitore Outlook di commessa | casella o cartella condivisa dedicata per commessa |
| OD-17 | Struttura standard delle cartelle di commessa | definirla con i PM; il Cockpit propone e il PM conferma la mappatura |
| OD-18 | Frequenza di aggiornamento e soglie di freschezza per fonte | giornaliera per Galileo e cartelle; oraria per Outlook |
| OD-19 | Valutazione privacy per la lettura delle email | DPIA con il DPO prima della Fase 3 |
