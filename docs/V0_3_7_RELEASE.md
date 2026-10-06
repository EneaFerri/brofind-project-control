# Brofind Project Control V0.3.7 — Validation Release

## Scopo
Trasformare le decisioni emerse dalla revisione della V0.3.6 in una versione utilizzabile per acceptance test sulla 9028, senza anticipare regole non ancora validate con Direzione/Amministrazione/Responsabili di reparto.

## Decisioni implementate

### Portfolio
- priorità distinte: `Critica`, `Da intervenire`, `Da presidiare`, `Sotto controllo`, `Dati insufficienti`;
- `Critica` e `Da intervenire` hanno grammatica visiva diversa;
- tooltip su ogni dominio con mini-recap del motivo.

### Testata commessa
- un solo `Budget autorizzato`;
- Base + Extra visibili come spiegazione del totale;
- card `Fase commessa` e stato procurement espresso con conteggi oggettivi;
- contratto sintetico in pagina, dettagli in drawer laterale.

### Controllo economico
- `Costo noto + impegnato` come KPI centrale;
- `Budget ancora da determinare` non viene presentato come saving;
- snapshot Baseline + Extra → Budget autorizzato → Galileo mantenuto;
- tre stati per il residuo VdA: `Budget residuo`, `Saving candidato`, `Saving consolidato`;
- il saving consolidato migliora il margine ma non rialloca automaticamente budget ad altre VdA.

### Procurement
- motore uniforme parametrizzato per natura VdA;
- acquisti diretti e servizi/montaggi hanno aspettative temporali diverse;
- per servizi/montaggi tardivi, vicino alla consegna viene richiesta evidenza di RFQ/offerte/fornitore e non viene creato un falso “ordine mancante”;
- finding engineering non validati restano evidenza da confermare/scartare e possono essere esclusi dal motore con feature flag.

### Confidence
- livelli `Alta / Media / Bassa / Insufficiente` per Economia, Procurement, Contratto, Tempi, Tecnica;
- confidence = solidità delle evidenze, non probabilità AI;
- data-quality separata dalla criticità del progetto;
- sui progetti con control foundation, `Bassa/Insufficiente` genera un alert `Confidence Review richiesta`;
- report mostra evidenze solide, gap e obiettivo della review.

### Azioni ed escalation
- action type: `VERIFY / DECISION / INTERVENTION`;
- owner persona o reparto;
- testo suggerito solo per invio manuale;
- risposta registrata → `PENDING_VALIDATION` → validazione del richiedente/Direzione → chiusura;
- escalation per scadenza visibile senza riassegnazione automatica dell'owner.

### Contract Baseline
- condizioni principali con stato `FROZEN` o `DA CHIARIRE`;
- contraddizioni non risolte automaticamente;
- change potenziale tecnico deve scalare al Commerciale per verifica dell'ordine/extra e aggiornamento manuale dello stato contrattuale.

## Limiti intenzionali
Non ancora congelati: macro-famiglie di costo, required date procurement, lead-time per categoria, percentuale di avanzamento acquisti, soglie definitive di escalation e matrice organizzativa completa.

## Acceptance test
La release include 37 test automatici. Il pilot 9028 copre i casi Analizzatori, Apparecchi a specifica, Carpenterie, Montaggi elettrici, saving candidato/consolidato, Contract Baseline e Project Confidence Review.
