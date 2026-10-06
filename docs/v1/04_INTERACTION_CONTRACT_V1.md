# 04 — Interaction Contract V1 (A17)

**Stato:** PROPOSTA — sostituisce `docs/authority/drafts/NEEDS_UPDATE_08_INTERACTION_CONTRACT_V1_DRAFT.md` dopo approvazione.
**Data:** 2026-10-06
**Autorità superiore:** Product Freeze V1 · `05_SHARED_UI_SHELL_CONTRACT_V1.md` · `06_VISUAL_FREEZE_MANIFEST_FINAL.md` · mockup `docs/visuals/V01…V08`.

Correzioni rispetto alla bozza: Billing e Payment unificati, nessuna superficie `Control`, shell condivisa, drawer AI unico, permessi per ruolo.

---

## 1. Shell condivisa (tutte le schermate)

| Elemento | Comportamento |
|---|---|
| **Sidebar** | solo navigazione globale: `Portfolio`; in fondo accessi di supporto (Impostazioni, Ruoli e utenti se permesso). Comprimibile ("Riduci menu"). **Nessuna** voce di dominio di commessa. |
| **Header di commessa** | codice · cliente / nome · descrizione breve · stato · cliente · offerta · PM · inizio contratto · consegna prevista. Identico su ogni schermata di commessa. Campi mancanti → `N/D` grigio. |
| **Navigazione di commessa** | barra orizzontale unica, stesse etichette e stesso ordine ovunque: `Overview · Master · Technical · Procurement · Documents · Economics · Billing & Payment · Criticità · Attività · Conversazioni · Storico` (lingua: OD-02). |
| **Pulsante AI** | uno solo, nella shell; apre il drawer a destra; chiuso per default; ambito = intera commessa, pagina corrente solo come contesto. |
| **Toolbar locale** | solo funzioni della pagina: ricerca, filtri, vista, esporta, creazione di oggetti del Cockpit (`Aggiungi Procurement Item`, `Aggiungi documento richiesto`, `Nuova decisione`). Vietati comandi che eseguono processi esterni (`Emetti RFQ`, `Crea ordine`, `Emetti fattura`). |
| **Supporto** | Fonti, Storico dell'oggetto, Impostazioni commessa, Parti e ruoli: drawer o menu `…`, non navigazione primaria. |
| **Utente** | nome e ruolo dell'utente corrente; in demo selettore utente (ADR-004). |

Una funzione ha **una sola** collocazione principale: se è nella shell non si ripete nella pagina.

## 2. Regole trasversali

- **Dati mancanti**: la struttura della schermata non cambia; il componente mostra `N/D`, `Non ancora disponibile` o `Parziale` in grigio, con tooltip che spiega il perché. Mai verde.
- **Drill-down**: ogni semaforo, contatore ed esposizione è cliccabile e porta alla superficie/oggetto che lo genera, mantenendo il contesto (filtro o sezione evidenziata).
- **Perché lo vedo**: ogni Attention mostra spiegazione, valori confrontati, fonte, data della fonte e affidabilità (drawer "Fonti").
- **Azioni del Cockpit** riconoscibili come tali: `Conferma`, `Scarta`, `Prendi in carico`, `Crea attività`, `Registra esito`, `Congela interpretazione`, `Conferma saving`, `Correggi collegamento`. Per i dati sorgente solo `Vedi evidenza` / `Apri nella fonte`.
- **Permessi**: pulsanti non consentiti al ruolo non vengono mostrati; il server rifiuta comunque la richiesta (ADR-005).
- **Feedback**: ogni azione produce un messaggio che dice cosa è cambiato **e cosa non è cambiato** (es. "La fonte Galileo non è stata modificata").
- **Proposte AI**: visivamente distinte dai dati confermati (badge "Proposta AI"); azioni Accetta / Collega / Scarta tracciate.
- **Esporta**: CSV/XLSX della tabella visibile con i filtri applicati.

## 3. Superfici

### V01 — Portfolio
- Riepilogo: totale commesse · critiche · in attenzione · in linea · non attive.
- Filtri di stato: Tutte · In corso · In avvio · Chiuse · Archiviate. Le archiviate sono escluse per default, ricercabili, riattivabili.
- Ricerca per commessa, cliente, offerta.
- Colonne: N° · Cliente/Progetto · Fase · semafori `Master · Technical · Procurement · Documents · Economics · Billing · Payment` · Principale esposizione (causa → conseguenza, n° criticità e attenzioni).
- Ordinamento di default **priorità di controllo prima della paginazione**: rosso → giallo → senza Attention; a parità numero di aree coinvolte, poi prossimità a milestone sensibili. Nessuno score opaco.
- Click su intestazione di dominio: ordina l'intero portfolio per severità in quel dominio.
- Click su riga → Overview; click su semaforo → superficie di quel dominio.
- Visibilità secondo il perimetro del ruolo (ADR-005); stesso Portfolio per tutti, filtri predefiniti diversi per ruolo.

### V02 — Overview (Panoramica commessa)
Ordine fisso: 1) contesto (header + "N aree critiche · N in attenzione") · 2) striscia domini compatta e cliccabile con contatori · 3) **Principale esposizione** (titolo causa → conseguenza, domini coinvolti, "In gestione: …", prossimo aggiornamento, `Apri causa`) · 4) **Altre attenzioni** (max poche righe, `Apri`) · 5) **Prossimo gate** (nome, data, readiness, n° blocker, Target vs Forecast, `Apri Master`) · 6) supporto/AI su richiesta (`Fonti`, `Storico`, `…`).
Non diventa una dashboard di KPI e non duplica il dettaglio dei domini. Nessun semaforo globale indipendente.

### V03 — Master
- Barra fasi con avanzamento (completate / totali per fase) e stato.
- Tabella milestone: # · Milestone · Fase · Target · Forecast · Actual · Δ giorni · Stato · Readiness · Principali cause/note. Click su riga → dettaglio milestone (condizioni, storico date, evidenze).
- Pannello destro: prossima milestone (stato, Δ, readiness, cause principali, `Apri dettaglio`) · **Rischio su fasi successive** (milestone a valle marcate `Da verificare`) · milestone completate (conteggio, non %, di avanzamento lavori).
- Le date a valle **non** vengono spostate automaticamente. Modifica del Target solo con motivo; correzione di un blocker collegato per errore con motivo e storico.
- Toolbar: Vista compatta/estesa · filtro fasi · Esporta.

### V04 — Economics
- KPI: Valore contratto · Budget · Speso a oggi (% su budget) · Forecast finale (Δ) · Variazione vs budget · Varianti approvate · Margine previsto. Forecast e margine `N/D` se il forecast non è confermato.
- Andamento costi (Budget / Speso / Forecast nel tempo) da snapshot storici; con un solo snapshot: punto singolo + nota.
- Speso per categoria e Variazione per categoria: per macro-famiglia quando definita (OD-05), nel frattempo per natura VdA, dichiarato in legenda.
- Dettaglio per voce di costo (Budget · Speso · Impegnato · Forecast · Variazione · % · Stato), espandibile fino a VdA e Centro di analisi.
- Principali scostamenti con causa e dominio collegato · Varianti di commessa · Impegni aperti (se la fonte li fornisce, altrimenti `Non ancora disponibile`).
- Azioni: `Conferma saving`, `Conferma forecast` (proposta → valore operativo), `Esporta`. Nessun pulsante AI locale.

### V05 — Technical
- KPI: Decisioni aperte · Da confermare con cliente · Interfacce da chiudere · Segnali di disallineamento · Confermate di recente.
- Tabella decisioni aperte: ID · Tema · Stato · Chi deve confermare · Scadenza · Impatto · Evidenze. Pannelli: Rischi tecnici principali · Fonti disponibili (stato: disponibile / parziale / da verificare) · Decisioni confermate di recente (data, impatto, evidenza, note).
- `Nuova decisione` crea un Technical Checkpoint. Chiusura solo con esito confermato dal ruolo competente.
- Segnale di allineamento: `Collega a decisione esistente` · `Crea nuova decisione` · `Non formalizzare` (con motivo).

### V06 — Procurement
- Sintesi per stadio (ciambella) · Item critici · Prossime scadenze (RFQ / Ordini) · Ritardi fornitori.
- Tabella: # · Item · Fornitore · Stadio · Prossima scadenza · Need date · Promise · Forecast · Stato controllo · Impatto. Pannelli: Prossime scadenze · Fornitori critici · Stato per stadio.
- `Aggiungi Procurement Item`; correzione collegamento Item ↔ ordine Galileo con conferma; override lead time con motivo.
- Il Cockpit non emette RFQ né ordini.

### V07 — Documents
- Sintesi per stato (Disponibili · Da verificare · Da aggiornare · Attesi · N/A) · Documenti attesi (di cui con scadenza ≤ 30 gg) · Documenti scaduti (di cui critici) · Prossime scadenze.
- Tabella: # · Documento · Codice · Categoria · Fase · Rev. · Stato · Scadenza · Ultimo aggiornamento · Responsabile · Note. Pannelli: Prossime scadenze · Documenti critici (motivo) · Stato per categoria.
- `Aggiungi documento richiesto`; conferma di adeguatezza nei casi non deterministici. Non è un EDMS: nessun check-in/out, transmittal o firma.

### V08 — Billing & Payment
- KPI ad anello: Maturato · Fatturato · Incassato · Esposizione da incassare (sul valore contrattuale riconosciuto).
- Tabella eventi: # · Evento contrattuale · % / Importo · Evidenza / Trigger · Data maturazione · Fattura (Galileo) · Scadenza pagamento · Incassato · Stato controllo. Pannelli: Prossime scadenze di pagamento · Incassi per trimestre · Stato per evento.
- Segnali Billing e Payment restano distinti (semafori separati nel Portfolio) ma aprono questa stessa superficie sulla sezione pertinente.
- Nessuna emissione di fatture né workflow di sollecito/credito.

### Criticità · Attività · Conversazioni · Storico
- **Criticità**: elenco con condizione, impatto, owner, obiettivo di gestione, copertura (derivata), prossimo aggiornamento; collegamento all'Attention e al dominio di origine.
- **Attività**: elenco per stato; creazione con `expected_result` obbligatorio; risposta del responsabile → `In attesa di conferma` → validazione del richiedente → chiusa. La chiusura **non** risolve la Criticità né l'Attention.
- **Conversazioni**: thread per attività; il Cockpit prepara testi da inviare manualmente e registra risposte ricevute.
- **Storico**: cronologia leggibile della commessa (cosa, quando, chi, perché, evidenza), filtrabile per dominio/oggetto.
- Layout di dettaglio da congelare quando saranno disponibili i freeze operativi (OD-01).

## 4. Drawer AI
- Apertura dal pulsante della shell; larghezza fissa a destra; non occupa spazio quando chiuso.
- Tab: Chat · Fonti · Azioni (le "Azioni" sono solo proposte da confermare).
- Esempi di domande ammessi: spiegazioni, cause, confronto fonti, dati mancanti, sintesi, bozze di testo. Vietati esempi che chiedono di scegliere fornitori, soluzioni tecniche o azioni operative.
- Ogni risposta cita le fonti; avviso permanente "L'AI può commettere errori".
