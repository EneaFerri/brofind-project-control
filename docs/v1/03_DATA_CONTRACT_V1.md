# 03 — Data Contract V1 (A15)

**Stato:** PROPOSTA — sostituisce `docs/authority/drafts/NEEDS_UPDATE_09_DATA_CONTRACT_MATRIX_DRAFT.md` dopo approvazione.
**Data:** 2026-10-06
**Autorità superiore:** Product & Scope Freeze V1 (§ citati per ogni oggetto).

Definisce **significato, fonte, autorità, derivazione e conferma** dei dati V1. Gli schemi DB/API esatti sono dettagli di implementazione, purché rispettino questo contratto.

## 0. Regole comuni

### 0.1 Categorie di autorità
Ogni dato appartiene a una sola categoria (da `02_…MONITORING_LAYER`, *Data authority taxonomy*):

| Codice | Significato | Scrivibile dal Cockpit |
|---|---|---|
| `SRC` | fatto della fonte esterna (Galileo, contratto, cartella, Outlook, planner) | **no**: solo re-import |
| `IMP` | replica normalizzata della fonte | **no** |
| `USR` | confermato/inserito da un utente nel Cockpit | sì, con storico |
| `CALC` | calcolato in modo deterministico e riproducibile | no: si ricalcola |
| `AI` | proposta AI, estratta o inferita | no: diventa `USR` solo con conferma |
| `OPS` | stato operativo del Cockpit (workflow, presa in carico) | sì, con storico |

### 0.2 Metadati obbligatori dei dati rilevanti (freeze §6)
`source` (tipo + riferimento) · `source_date` · `observed_at` · `freshness` · `confidence` / stato di verifica · `evidence` (quando richiesta).

### 0.3 Freschezza
- Stati: `FRESCO` · `DA AGGIORNARE` · `SCADUTO` · `N/D`.
- Soglie **configurabili**: default globale → commessa → item (freeze §24). Mai nel codice.
- Un dato `SCADUTO` porta il semaforo a `GRIGIO / DA VERIFICARE`, **mai** a rosso o verde da solo.

### 0.4 Semaforo (freeze §4.1)
`VERDE` = coerente con lo stato atteso oggi **e** dati sufficientemente freschi · `GIALLO` = da verificare / rischio concreto · `ROSSO` = condizione accertata incompatibile · `GRIGIO` = dati mancanti, scaduti o insufficienti.

### 0.5 Riconciliazione (freeze §6.2)
Il valore riconciliato è un oggetto `USR` separato che **non** sovrascrive la fonte; conserva motivo, evidenza, autore e data; la discrepanza resta visibile finché la fonte non viene riallineata.

### 0.6 Storico (freeze §23)
Ogni modifica a dati `USR`/`OPS` genera un **History Event**: oggetto, valore precedente, valore nuovo, quando, chi, perché, evidenza, causa collegata.

---

## 1. Commessa e configurazione

### 1.1 Project (freeze §5, §7)
| Campo | Significato | Fonte | Autorità | Note / baseline |
|---|---|---|---|---|
| `code` | numero commessa | Galileo | SRC | ✅ `Project.code` |
| `client_name`, `project_name`, `short_description` | identità mostrata nell'header | Galileo / ordine | SRC → USR se corretto | ◐ `customer`, `description` |
| `offer_ref` | riferimento offerta | ordine / Galileo | SRC | ❌ (oggi in `CustomerOrder.quote_ref`) |
| `contract_start_date` | inizio contratto | contratto | SRC, confermato USR | ❌ |
| `expected_delivery_date` | data chiave corrente | Master (milestone configurata) | CALC | ❌ derivata, non inserita |
| `lifecycle_state` | Lead · Offerta · In avvio · In corso · Chiusa · Archiviata | Galileo + USR | USR con storico | ◐ `status` |
| `phase` | fase corrente (configurabile, freeze §9.5) | proposta Cockpit, corretta dal PM | CALC → USR | ❌ |
| `scope_profile` | complessità / profilo di controllo | KOM | USR | ❌ |
| `archived` | esclusa dal portfolio operativo, riattivabile | USR | OPS | ❌ |

### 1.2 Source Configuration (freeze §5)
| Campo | Significato | Autorità |
|---|---|---|
| `source_type` | GALILEO · DOCUMENT_FOLDER · COMMUNICATION · PLANNER · ALTRO | USR |
| `locator` | percorso / casella / identificativo | USR |
| `association` | CONFIGURATA · COLLEGATA · PROPOSTA (richiede conferma) | USR / AI |
| `last_scan_at`, `status`, `freshness` | stato della fonte | CALC |
Baseline: ◐ `ProjectSourceScan`, `ProjectSourceFile` (oggi percorso fisso `data_sources/<codice>/<Galileo|Documenti|Outlook>`).

### 1.3 Project Party (freeze §8)
| Campo | Significato | Autorità |
|---|---|---|
| `party_role` | PM, Commerciale, Processo, E&I, Acquisti, Cliente, Engineering, Fornitore, Installatore, Terzi… (catalogo configurabile) | USR |
| `user_id` o `external_name` | persona interna (utente) o soggetto esterno | USR |
| `department` | reparto di appartenenza | USR |
Non concede permessi applicativi (ADR-005). Baseline: ❌ (solo `pm_owner`, `sales_owner`).

### 1.4 Settings / Override (freeze §24)
| Campo | Significato |
|---|---|
| `key` | parametro (soglia freschezza, lead time categoria, tolleranza billing…) |
| `scope` | GLOBAL · PROJECT · ITEM (+ riferimento) |
| `default_value`, `active_value` | valore ereditato e valore attivo |
| `sensitive` | se riduce un controllo contrattuale/sensibile → richiede approvazione |
| `author`, `date`, `reason` | obbligatori |
Una modifica globale non riscrive le commesse esistenti con override.

---

## 2. Master Planner (freeze §9–10)

### 2.1 Milestone
| Campo | Significato | Fonte | Autorità |
|---|---|---|---|
| `name`, `kind` | CONTRATTUALE · INTERNA · ESTERNA (planner) | contratto / KOM / planner | SRC o USR |
| `phase` | raggruppamento configurabile | USR | USR |
| `baseline_date` | data iniziale, **immutabile** | contratto / KOM | SRC / USR una sola volta |
| `target_date` | obiettivo valido approvato | USR | USR con storico e motivo |
| `forecast_date` | previsione realistica corrente | planner / USR / CALC | origine sempre dichiarata |
| `actual_date` | evento avvenuto | evidenza / USR | USR (+ evidenza se richiesta) |
| `status` | Completata · In linea · In attenzione · In ritardo · Non iniziata | — | **CALC** da date e oggi |
| `delta_days` | `forecast_or_actual − target` | — | CALC |
| `readiness` | PRONTA · NON PRONTA · DA VERIFICARE | — | CALC da condizioni |
| `sensitivity` | contrattuale / penali / fatturazione | contratto | USR |
**Regole:** PRONTA ≠ RAGGIUNTA. Un ritardo a monte rende `DA VERIFICARE` le milestone a valle, **senza spostarne le date**.
Baseline: ◐ `Milestone(contract_date, forecast_date, actual_date, ld_applicable)` → migrazione: `contract_date` → `baseline_date` e `target_date`.

### 2.2 Milestone Condition (dipendenza)
| Campo | Significato |
|---|---|
| `milestone_id` | milestone servita |
| `depends_on` | riferimento a Procurement Item · Document Item · Technical Checkpoint · Control Checkpoint · condizione cliente/terzi |
| `kind` | BLOCCANTE · RILEVANTE |
| `state` | derivato dall'oggetto collegato |
| `link_origin`, `corrected_by`, `reason` | per correggere un collegamento errato con storico |

### 2.3 Control Checkpoint
| Campo | Significato |
|---|---|
| `description` | fatto atteso da osservare (non l'attività che lo produce) |
| `state` | ATTESO · RILEVATO · CONFERMATO · SCADUTO/NON RILEVATO · NON APPLICABILE |
| `needed_by` | data di controllo (non scadenza operativa) |
| `monitoring_owner`, `confirming_role` | Project Party |
| `evidence` | fonte |
RILEVATO ≠ CONFERMATO; conferma automatica solo per regole deterministiche autorizzate.

---

## 3. Technical Control (freeze §14)

### 3.1 Technical Decision / Checkpoint
| Campo | Significato | Autorità |
|---|---|---|
| `ref` | identificativo leggibile (es. TC-001) | CALC |
| `topic` | tema / decisione | USR o AI confermata |
| `discipline` | Processo, Meccanica, E&I, Software, … | USR |
| `state` | Da confermare · Da decidere · In attesa cliente · Confermato · Non applicabile | USR |
| `confirming_party` | chi deve confermare (Cliente, Interno, …) | USR |
| `needed_by` | scadenza di controllo | USR / collegata a milestone |
| `impact` | Layout · Prestazioni · Interfacce · Milestone · Conformità … (catalogo) | USR |
| `evidence[]` | KOM, P&ID, mail cliente, specifica, report… | SRC |
| `outcome` | esito confermato dal ruolo competente | USR |
Una decisione si chiude **solo** con Outcome esplicito; l'assenza di nuove mail non la chiude.

### 3.2 Technical Alignment Signal
| Campo | Significato |
|---|---|
| `topic`, `pattern` | fenomeno osservato (decisione riaperta, indicazioni discordanti, richieste ripetute…) |
| `evidence[]` | comunicazioni/documenti collegati |
| `materiality`, `persistence` | criteri per diventare Attention |
| `state` | ANCORA ATTIVO · STABILIZZATO · SCARTATO (con motivo) |
| `linked_object` | checkpoint esistente / nuovo / nessuno |
Vietato usare sentiment, tono o numero di mail da solo.

---

## 4. Procurement Control (freeze §13)

### 4.1 Procurement Item
| Campo | Significato | Fonte | Autorità |
|---|---|---|---|
| `description`, `category` | fornitura logica rilevante; categoria Galileo | Galileo / USR | SRC / USR |
| `vda_code` | collegamento economico | Galileo | SRC |
| `supplier` | fornitore (selezionato o in valutazione) | Galileo / offerte | SRC |
| `stage` | Da richiedere in offerta · Offerte disponibili · Da ordinare · Ordinato · In esecuzione · Disponibile | Galileo + USR | CALC / USR, non bloccante |
| `rfq_needed_by`, `order_needed_by` | checkpoint pre-ordine | CALC da need date − lead time | CALC / override USR |
| `need_date` | prima necessità attiva e confermata tra le milestone servite | Master | CALC / override motivato |
| `supplier_promise_date` | data promessa dal fornitore | conferma d'ordine / mail | SRC (AI → conferma) |
| `current_forecast_date` | previsione corrente | fornitore / USR | origine dichiarata + freschezza |
| `actual_availability_date` | disponibilità effettiva | Galileo (ricevimento) / USR | SRC / USR |
| `lead_time_days`, `lead_time_origin` | standard categoria → offerte → fornitore → conferma → forecast | Settings / SRC | storico conservato |
| `control_state` | In linea · Da verificare · A rischio · In ritardo previsto · Disponibile | — | **CALC** |
| `impact` | milestone/fase impattata | Master | CALC |
| `monitoring_owner` | tipicamente Acquisti | Project Party | USR |
| `orders[]` | ordini Galileo collegati (multi-PO, lotti) | Galileo | SRC; matching ambiguo → conferma |
**Regole:** Need ≠ Promise ≠ Forecast ≠ Actual. Forecast scaduto → `Da verificare`, non ritardo.
Baseline: ◐ analisi per VdA (`app/procurement.py`): diventa una vista aggregata degli Item per VdA.

---

## 5. Document Control (freeze §12)

### 5.1 Document Item
| Campo | Significato | Fonte | Autorità |
|---|---|---|---|
| `name`, `code`, `doc_type`, `category` | documento logico richiesto | Document List / Minimum Document Set | SRC / USR |
| `family` | DELIVERABLE · FONTE DI CONTROLLO | USR | USR |
| `competent_role`, `responsible_party` | chi lo produce / chi ne garantisce la disponibilità | Project Party | USR |
| `needed_by` | ereditata dalla milestone/checkpoint collegati quando possibile | Master | CALC / USR |
| `state` | ATTESO · DISPONIBILE · DA AGGIORNARE · DA VERIFICARE · NON APPLICABILE | evidenze + USR | CALC solo se deterministico, altrimenti USR |
| `latest_evidence`, `revision`, `last_update` | ultimo file osservato nella cartella commessa | Source Center | SRC |
| `linked_objects[]` | milestone, checkpoint, billing event… | USR | USR |
**Derivati (non stati base):** mancante / in ritardo / critico, da rilevanza, fase, data necessaria e adeguatezza.

---

## 6. Economics (freeze §15–16)

### 6.1 VdA (posizione di budget)
| Campo | Significato | Fonte | Autorità | Baseline |
|---|---|---|---|---|
| `vda_code`, `vda_name`, `analysis_center` | voce di analisi, aggregata sui CDA | Galileo | SRC | ✅ |
| `baseline_budget` | budget iniziale, immutabile | Galileo | SRC | ✅ |
| `current_budget` | budget autorizzato corrente | Galileo / eventi autorizzati | SRC | ✅ `operational_budget` |
| `actual` | consuntivo = ricevuto + costo uomo + spese generali | Galileo | CALC su SRC | ✅ |
| `committed` | ordini emessi non ancora ricevuti | Galileo | SRC | ✅ `open_order_commitment` |
| `purchases_closed` | flag ultimazione ordini VdA | Galileo | SRC | ✅ |
| `forecast_final` | previsione costo finale | metodologia configurata + USR | CALC / USR con data, owner, freschezza | ❌ |
| `forecast_method` | es. *chiusa* (= actual + committed) se acquisti conclusi; *ETC confermato* altrimenti | Settings | config | ❌ |
| `variance` | `forecast_final − current_budget` | — | CALC | ◐ oggi `committed_cost − budget` |
| `saving_class` | Budget residuo · Saving candidato · Saving consolidato | — / USR | CALC / USR | ✅ `CockpitDecision VDA_SAVING` |
| `nature`, `cost_family` | natura VdA; macro-famiglia (**non congelata**) | Settings | config | ◐ `VDA_NATURE` |
**Regole:** senza forecast confermato, `forecast_final` = `N/D` e il semaforo non diventa verde; una proposta AI cost-to-complete diventa operativa solo dopo conferma.

### 6.2 Control Snapshot
Fotografia **immutabile** di una fonte economica: `source`, `source_hash`, `captured_at`, totali e righe. Più snapshot nel tempo alimentano l'andamento costi. Re-import identico = no-op (AD-002).

### 6.3 Economic Result
| Campo | Significato | Autorità |
|---|---|---|
| `initial_contract_value` | valore iniziale (PO base, netto IVA) | SRC |
| `recognized_contract_value` | iniziale + extra/minus **formalizzati** | CALC su SRC |
| `open_change_exposure` | extra/minus aperti, separati | CALC da Change Item |
| `final_cost_forecast` | somma forecast VdA | CALC |
| `expected_result`, `expected_margin_pct` | valore riconosciuto − forecast costi | CALC (`N/D` se forecast incompleto) |
Baseline: ◐ `CustomerOrder`, `ChangeRequest`.

---

## 7. Billing & Payment (freeze §17–18)

### 7.1 Billing Event
| Campo | Significato | Fonte | Autorità |
|---|---|---|---|
| `name` | evento contrattuale (Ordine, Approvazione GA, Delivery, Take Over, Acceptance…) | contratto / KOM | SRC → USR |
| `share_pct`, `amount` | quota del valore contrattuale | contratto | SRC |
| `trigger` | condizione di maturazione | contratto | SRC → USR |
| `trigger_link` | milestone · document item · checkpoint che la soddisfano | USR | USR |
| `maturity_state` | NON MATURATO · MATURATO · DA VERIFICARE | — | CALC se deterministico, altrimenti USR |
| `maturity_date` | data di maturazione (prevista/effettiva) | Master | CALC |
| `invoice_ref`, `invoice_state` | fattura Galileo collegata: Non emessa · Emessa | Galileo | SRC |
| `control_state` | In linea · Da fatturare · Da verificare · Non dovuto | — | CALC |
| `tolerance_days` | tolleranza configurabile | Settings | config |
**Regole:** maturato + Galileo non coerente oltre tolleranza → Attention; caso inverso → DA VERIFICARE. Sequenze contrattuali: segnale preventivo / grave, mai blocco.

### 7.2 Invoice / Payment
| Campo | Significato | Fonte | Autorità |
|---|---|---|---|
| `number`, `issue_date`, `due_date`, `amount` | fattura | Galileo | SRC |
| `collected_amount` | incassato | Galileo | SRC |
| `payment_state` | Incassata · Da pagare · In scadenza · Scaduta | — | CALC |
Baseline: ✅ `Invoice(amount, paid_amount, due_date)`. Nel caso B1 `INVOICES.Paid_Amount` è l'unica fonte del pagato.

### 7.3 Indicatori di sintesi
`maturato`, `fatturato`, `incassato`, `esposizione = fatturato − incassato` sul valore riconosciuto. Il **confronto con l'avanzamento reale** richiede un metodo numerico **non congelato** (OD-06): finché manca, l'indicatore mostra `N/D` con spiegazione.

---

## 8. Controllo operativo (freeze §21–22, DEC-002…018)

> Parte dei contratti di riferimento (Workflow Freeze v1.1, Operational Control Freeze v1.0, Collaboration Freeze v1.0) **non è disponibile** (OD-01). I campi sotto derivano dal Product Freeze e dalle DEC presenti; vanno rivalidati quando i freeze saranno recuperati.

### 8.1 Attention
| Campo | Significato | Autorità |
|---|---|---|
| `condition_key` | chiave deterministica stabile (deduplica) | CALC |
| `domain` | Master · Technical · Procurement · Documents · Economics · Billing · Payment | CALC |
| `severity` | GIALLO · ROSSO | CALC |
| `explanation`, `compared_values`, `source`, `as_of`, `confidence` | perché è mostrata | CALC |
| `cause_group` | causa comune che raggruppa conseguenze multi-dominio | CALC / USR |
| `acknowledged_by`, `justification`, `linked_decision` | presa in carico (non silenziamento) | OPS |
Si chiude **solo** quando la condizione sorgente non è più vera. Un segnale scartato non si ripropone senza nuove evidenze materiali.

### 8.2 Criticità
| Campo | Significato | Autorità |
|---|---|---|
| `title`, `underlying_condition` | problema formalizzato e Attention collegate | USR (o regola approvata) |
| `impact` | domini/milestone impattati | USR |
| `owner` | responsabile della gestione | USR |
| `management_objective` | obiettivo di gestione (Operational Control Freeze) | USR |
| `state` | lifecycle indipendente dall'Attività (da definire con i freeze mancanti) | OPS |
| `next_update` | prossimo aggiornamento previsto | USR |
| `coverage` | copertura gestionale: **proiezione derivata** da stato e attività collegate | CALC |

### 8.3 Attività (Activity)
| Campo | Significato | Autorità |
|---|---|---|
| `title`, `purpose` | EXECUTION · DECISION | USR |
| `expected_result` | **obbligatorio** (DEC-005) | USR |
| `responsible_department`, `executor` | reparto responsabile ≠ esecutore personale (DEC-004) | USR |
| `requester` | chi ha chiesto e deve validare | USR |
| `due_date` | scadenza | USR |
| `state` | DA FARE · IN CORSO · IN ATTESA DI CONFERMA · CHIUSA · ANNULLATA | OPS |
| `linked_cause` | Attention · Criticità · Change · Checkpoint | USR |
| `outcome_id` | esito strutturato | USR |
Mappatura baseline: OPEN→DA FARE, IN_PROGRESS→IN CORSO, PENDING_VALIDATION→IN ATTESA DI CONFERMA, CLOSED→CHIUSA, RESOLVED→CHIUSA (da rivedere).

### 8.4 Outcome
`result` strutturato · `author` · `confirming_role` · `evidence` · `date`. Messaggio ≠ Outcome. Un Outcome non elimina la rivalutazione della condizione.

### 8.5 Conversazione / Messaggio
`activity_id` · `author` · `kind` (NOTA INTERNA · IN USCITA MANUALE · RISPOSTA RICEVUTA · VALIDAZIONE) · `body` · `created_at`. Il Cockpit non invia comunicazioni. Baseline: ✅ `ActionMessage`.

### 8.6 Change Item (freeze §11)
| Campo | Significato | Autorità |
|---|---|---|
| `description`, `origin` | manuale · contratto · mail · tecnico · proposta AI (solo dopo conferma) | USR |
| `lifecycle` | RILEVATA · IN VALUTAZIONE · DEFINITA · CHIUSA | OPS |
| `outcome` | concordata · non concordata · annullata · … | USR |
| `implementation_state` | NON AVVIATA · IN CORSO · COMPLETATA | USR |
| `owner` | normalmente PM | USR |
| `impact_matrix` | Scope, Master, Economic, Procurement, Document, Technical, Billing → DA VALUTARE · IMPATTO RILEVATO · NESSUN IMPATTO | USR |
| `economic_class` | EXTRA · MINUS · NEUTRO · DA DETERMINARE | USR |
| `estimated_cost`, `quoted_value`, `customer_order_ref` | dettaglio economico | SRC / USR |
Non riscrive direttamente gli altri domini. Baseline: ◐ `ChangeRequest`.

---

## 9. Fonti, evidenze e storico

### 9.1 Source Evidence
`source_type` · `locator` · `source_date` · `observed_at` · `freshness` · `verification` · `project_association` (con conferma se ambigua). Baseline: ◐ `ProjectSourceFile`, `ProjectSourceContent`.

### 9.2 Proposta AI
`kind` · `payload` · `evidence` · `confidence` · `shown_to` · `outcome` (ACCETTATA · COLLEGATA · SCARTATA) · `decided_by`. Le ipotesi AI non mostrate non entrano nello storico. Baseline: ◐ `AgentFinding`, `ProjectExtractedField`.

### 9.3 History Event
`object_type`, `object_id` · `field` · `old_value` · `new_value` · `at` · `actor` · `reason` · `evidence` · `cause_ref`. Append-only, leggibile a livello commessa.

---

## 10. Punti non congelati (devono restare parametri)

Soglie numeriche e di freschezza · lead time standard · formule finali di forecast economico · macro-famiglie di costo · metodo di avanzamento Payment · tolleranze billing · cataloghi (fasi, ruoli, impatti, categorie documentali) · meccanismo di integrazione Galileo e Outlook. Vedi `07_OPEN_DECISIONS.md`.
