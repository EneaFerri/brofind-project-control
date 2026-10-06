# Brofind Project Control V0.3.4 — Evidence-driven project reconstruction

## Obiettivo
La V0.3.4 trasforma la 9028 (cliente pilota anonimizzato) da pilot economico parziale a commessa campione ricostruita con evidenze reali disponibili: PO cliente base, PO extra, budget baseline, budget Extra 1, JMRP e interrogazione ordini.

## Evidenze 9028
- PO-PILOT-001: €985.550 netti, DDP, 60 gg data fattura, riferimento offerta OFF-PILOT-001 Rev.5.
- PO-PILOT-002: extra €113.350 netti (+ IVA €22.670), DDP, 60 gg data fattura, riferimento OFF-PILOT-002.
- Valore cliente netto complessivo: €1.098.900.
- Budget baseline: €657.708,26.
- Budget costi Extra 1: €73.091,00.
- Budget teorico post-extra: €730.799,26; budget operativo Galileo: €730.797,00; differenza -€2,26.
- JMRP / ordini: ordini €454.208,89 nell'estrazione, ricevuto €199.691,62, residuo ordini €254.517,27, costo uomo €1.801,53, spese generali €3.025,06.

## Modifiche funzionali
- tutte le 34 VdA della baseline sono visibili;
- colonna Δ scope evidenzia il budget aggiunto dall'Extra 1;
- procurement e stato economico della VdA sono separati;
- lo sforamento locale non rende automaticamente rossa l'intera commessa;
- la 9028 è gialla: gli sforamenti locali sono inferiori alla copertura prudenziale sulle VdA con acquisti dichiarati conclusi;
- le aree senza dati sono N/D, non verdi;
- PO cliente ed extra formalizzati sono visualizzati come evidenze contrattuali;
- il Project Closing non viene mostrato come anomalia durante la fase EXECUTION;
- qualità dati esplicita: mismatch ordini €172,81, differenza budget €2,26, costi uomo/spese generali non ancora completamente allocati alle VdA nel pilot.

## Regola budget candidata — ancora da validare
Il semaforo di commessa considera:
1. sforamenti già sostenuti/impegnati per VdA;
2. disponibilità sulle sole VdA con acquisti dichiarati conclusi;
3. quota di budget ancora aperta/non consolidata.

La disponibilità delle VdA chiuse non viene chiamata saving finale. La regola resta beta fino al back-test su altre commesse mature/chiuse.
