# Implementation gaps — interfaccia V1 su modello v0.3.8.1

**Data:** 2026-10-06 · **Release:** v1.0.0 (shell e superfici V1 sui dati esistenti)

La grafica delle 8 superfici canoniche è applicata. Dove il modello dati non fornisce ancora il dato richiesto dal mockup, la struttura della schermata resta invariata e il valore è mostrato come `N/D` / `Non ancora disponibile` (regola `03_UI_GOVERNANCE` §4). Ogni gap si chiude nella slice indicata.

| Superficie | Elemento del mockup | Stato attuale | Slice |
|---|---|---|---|
| Portfolio | Filtro *Archiviate* | conteggio 0: archiviazione non modellata | S3 |
| Portfolio | Semafori verdi | basati sulla disponibilità del dato, non sulla sua freschezza | S3 |
| Overview | Readiness e blocker del prossimo gate | N/D | S7 |
| Overview | "In gestione / prossimo aggiornamento" | derivato dall'attività collegata al segnale (non da una Criticità formale) | S10 |
| Master | Fasi (barra superiore e colonna Fase) | N/D: fasi non configurate | S7 |
| Master | Readiness | N/D; "Da verificare" solo per milestone a valle di un ritardo | S7 |
| Technical | Decisioni | derivate da requisiti/finding e issue tecniche; nessun Technical Checkpoint; *Nuova decisione* disabilitato | S9 |
| Technical | Da confermare con cliente, Interfacce da chiudere | N/D | S9 |
| Procurement | Righe | per VdA, non per Procurement Item | S6 |
| Procurement | Fornitore, Prossima scadenza, Need date, Promise, Forecast, Impatto | N/D | S6 |
| Documents | Registro documenti richiesti | mostrati solo documenti da completare registrati e file rilevati in cartella | S8 |
| Documents | Fase, Rev., Stato per categoria | N/D | S8 |
| Economics | Forecast finale, Variazione, Margine previsto | N/D senza costi a finire confermati (commesse con dati Galileo) | S4 |
| Economics | Andamento costi | richiede più snapshot storici | S4 |
| Economics | Speso per categoria | raggruppato per natura VdA: macro-famiglie non definite (OD-05) | S4 |
| Economics | Impegni aperti per fornitore e consegna prevista | fornitore e data N/D | S4/S6 |
| Billing & Payment | Maturato | calcolabile solo per eventi collegati a una milestone con data effettiva | S5 |
| Billing & Payment | Incassi per trimestre | richiede le date di incasso (non presenti nel caso B1) | S5 |
| Criticità | Criticità formali (obiettivo, copertura) | sono mostrati i segnali di attenzione | S10 |
| Storico | Storico per modifica (valore precedente/nuovo, motivo) | eventi aggregati da fonti, decisioni e import | S10 |
| Drawer AI | Chat | non attiva: fornitore e trattamento dati da decidere (OD-08) | S11 |
| Tutte | Esporta (tranne Portfolio) | disabilitato | — |
