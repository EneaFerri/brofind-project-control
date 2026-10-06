# Brofind Project Control V0.3.3 — Control Data Foundation

Questa release prepara il cockpit all'integrazione dei dati reali di gestione e controllo senza anticipare un forecast ETC non ancora sostenibile dal processo organizzativo.

## Principi

- Il forecast finale **non viene inventato** quando manca un ETC strutturato affidabile.
- Il sistema distingue `baseline`, `budget operativo`, `consuntivo`, `ordini residui` e `budget non ancora impegnato`.
- `Budget non ancora impegnato` non significa automaticamente `saving`.
- Le VdA vengono aggregate attraverso tutti i Centri di Analisi prima del confronto economico.
- `Acquisti conclusi = S` è un segnale di completamento procurement, non una chiusura economica della VdA.
- Tutti i calcoli mostrati nel nuovo pannello sono derivati da dati strutturati e hanno controlli di quadratura.

## Nuovo modello dati

- `ProjectControlSnapshot`: fotografia storica dei dati economici di una commessa.
- `ProjectControlLine`: dettaglio VdA / Centro di Analisi relativo allo snapshot.
- Sono supportati snapshot multipli nel tempo, così le revisioni future non sovrascrivono la storia del cockpit.

## KPI automatici

- Consuntivo = ricevuto + costo uomo + spese generali.
- Costo certo / impegnato = consuntivo + residuo ordini.
- Budget non ancora impegnato = budget operativo - costo certo / impegnato.
- Viene segnalato uno sforamento solo quando costi già sostenuti/impegnati superano il budget operativo.

## Controlli affidabilità

- Quadratura totale ordini JMRP vs interrogazione ordini.
- Quadratura ordini estratti vs ricevuto + residuo ordini.
- Drill-down dei Centri di Analisi per evitare confronti errati su una sola riga `COMM`.

## Pilot 9028

La demo contiene un pilot con dati economici reali già discussi per validare l'approccio. I dettagli non ancora estratti sono aggregati come `ALTRE VdA (aggregate)` e sono esplicitamente marcati come dati parziali di validazione.

## Import Excel

Il template standard è stato predisposto con due nuovi fogli:

- `CONTROL_SNAPSHOT`
- `CONTROL_LINES`

Questo consente di simulare subito il futuro adapter Galileo senza collegarsi ancora all'ERP.

## Non incluso / da validare

- ETC strutturato compilato dai PM.
- Forecast automatico basato sulla natura delle VdA.
- Saving automatico.
- Procurement Completion Agent documentale.
- Connessione diretta a Galileo.

Questi punti restano candidati e saranno introdotti solo dopo validazione su commesse reali.
