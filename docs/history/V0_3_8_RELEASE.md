# Brofind Project Control V0.3.8 — UX Simplification & Read-Many/Write-Little

## Obiettivo

Rendere il cockpit più leggibile e operativo senza trasformarlo in un nuovo gestionale transazionale. La release applica i risultati della review guidata V0.3.7 e separa nettamente **stato progetto**, **diagnosi**, **confidence** ed **evidenze**.

## Decisioni congelate

1. **READ MANY, WRITE LITTLE**: sorgenti ufficiali read-only, scritture limitate al layer operativo cockpit.
2. **Una vista = una domanda principale**: Overview, Economia, Procurement, Contratto, Operatività, Confidence Review.
3. **Salute ≠ Confidence**: i semafori di dominio descrivono lo stato; la confidence descrive la solidità delle evidenze.
4. **Finding ≠ fatto**: AI/engineering finding confermabili o scartabili; nessuna scrittura automatica su fonti ufficiali.
5. **Saving ≠ budget spendibile**: il saving consolidato migliora il margine; eventuali riallocazioni restano decisioni esplicite.

## UX

- Portfolio: header sticky, tooltip brevi.
- Overview: KPI essenziali, 3 alert principali, confidence complessiva.
- Economia: budget bridge, tre KPI primari, costi secondari e VdA. Procurement/data quality dettagliata rimossa dalla sequenza principale.
- VdA: nessuno scroll orizzontale; colonne ridotte e dettaglio espandibile.
- Procurement: superficie dedicata ai casi da verificare e ai ritardi potenziali.
- Operatività: thread chat, owner/reparto, invio manuale, risposta da validare.
- Contract Baseline: chiarimento e freeze direttamente nel drawer.
- Confidence Review: suggerimenti concreti e piano di recupero.

## Data governance

Nuovo `CockpitDecision` per decisioni e interpretazioni operative. Confermare un saving, congelare una condizione contrattuale o scartare un requisito non modifica le tabelle sorgente.

Le anomalie tra fonti (es. delta JMRP/interrogazione ordini) restano data-quality findings finché la sorgente autorevole non viene corretta.

## Pilot 9028

La 9028 resta il golden case per verificare:

- Analizzatori: verifica urgente, non conclusione automatica di mancanza;
- Apparecchi a specifica: completezza acquisti e saving candidato;
- Carpenterie: saving consolidabile nel margine, non riallocato automaticamente;
- Montaggi elettrici: potenziale ritardo procurement basato su RFQ/offerte/timing.

## Non ancora congelato

Macro-famiglie economiche, required date, lead-time definitivi, percentuale di avanzamento acquisti e soglie temporali/escalation restano da validare con Direzione, Amministrazione e responsabili di reparto.
