# 05 — Acceptance & Test Contract V1 (A18)

**Stato:** PROPOSTA — sostituisce `docs/authority/drafts/NEEDS_UPDATE_10_ACCEPTANCE_GATES_AND_TESTS_DRAFT.md` dopo approvazione.
**Data:** 2026-10-06

Una slice non è completa perché "si vede" o perché i test passano: deve superare **tutti** i gate applicabili.

## Gate 1 — Conformità all'autorità
- La slice cita le fonti usate: paragrafi del Product Freeze, sezione del Data Contract, mockup canonico.
- Nessun mockup rifiutato o sperimentale usato come riferimento.
- Nessuna semantica di dominio o workflow introdotta dalla UI.
- Ogni impossibilità dichiarata come **IMPLEMENTATION GAP** in `docs/v1/IMPLEMENTATION_GAPS.md`, non risolta riprogettando.

## Gate 2 — Semantica dei dati
- Baseline/Target, Consuntivo, Forecast e Scostamento mai confusi.
- Fonte, data, freschezza e affidabilità disponibili dove il Data Contract le richiede.
- Dati mancanti o scaduti mai verdi.
- Valori dei mockup mai usati come dati di produzione.

## Gate 3 — Regole di dominio (test automatici obbligatori)
| Regola | Test |
|---|---|
| Ritardo a monte non sposta date a valle | Master: forecast upstream > target ⇒ downstream `DA VERIFICARE`, date invariate |
| Need ≠ Promise ≠ Forecast ≠ Actual | Procurement: campi indipendenti; forecast scaduto ⇒ `Da verificare`, non ritardo |
| Chiusura Attività ≠ Criticità risolta | chiudere l'Attività lascia Criticità e Attention attive se la condizione persiste |
| Attention deterministica non silenziabile | `RESOLVED/IGNORED` manuale rifiutato; presa in carico consentita |
| Documento mancante derivato | Documents: stato `ATTESO` diventa critico solo per data/rilevanza |
| Billing | evento maturato + fattura non emessa oltre tolleranza ⇒ Attention; inverso ⇒ `DA VERIFICARE` |
| Proposta AI | non diventa dato operativo senza conferma; esito tracciato |
| Snapshot immutabili | re-import identico = no-op; nuovo hash = nuovo snapshot, storico intatto (AD-002) |
| Storico | ogni modifica `USR`/`OPS` produce un History Event completo |
| Deduplica | stessa condizione ⇒ una sola Attention |

## Gate 4 — Sicurezza e permessi
- Matrice **ruolo × endpoint di scrittura**: ogni combinazione non autorizzata ⇒ 403.
- Perimetro di visibilità: un utente `PARTY` non vede commesse in cui non è parte (anche via API e link diretti).
- Transizioni di stato verificate sul server (chiude AD-001).
- DevLogin rifiutato nel runtime `production`.

## Gate 5 — Regressione
Restano veri gli invarianti esistenti:
- **DEMO-B1-001**: sforamento economico €40.000 (VdA C000013); fattura scaduta residua €200.000 da `INVOICES.Paid_Amount`; `penalty_cap` lasciato da verificare non alimenta controlli; flusso Attività PM → Amministrazione → PM; la commessa emerge nel Portfolio Direzione.
- **9028 (anonimizzata)**: totali di budget bridge e VdA invariati; saving candidato/consolidato; Contract Baseline.
- Suite completa verde su Python 3.13 in CI.

## Gate 6 — Verifica visiva (per ogni superficie)
- Struttura e ordine delle sezioni come nel mockup canonico; shell secondo lo Shell Contract.
- Nessuna card, sezione o azione non autorizzata.
- Stati mancanti/parziali/non disponibili resi correttamente.
- Drawer AI chiuso non consuma larghezza.
- Leggibile a 1440×900 e 1920×1080.
- Testi in italiano e comprensibili (test §7.5 di `03_UI_GOVERNANCE`).
- Evidenza: screenshot della schermata reale affiancato al mockup, allegato alla PR.
- **Approvazione umana esplicita** prima della chiusura della slice.

## Gate 7 — Pilota reale Brofind (prima del rilascio di accettazione V1)
Un piccolo insieme di commesse reali (in ambiente aziendale, mai nel repository) che copra: commessa sana · scostamento economico precoce · rischio milestone contrattuale · item di procurement prima e dopo l'ordine · forecast fornitore scaduto · decisione tecnica in attesa del cliente · documento mancante rilevante per un gate · evento di fatturazione maturato non allineato in Galileo · ritardo incassi vs avanzamento · Change Item con esposizione economica · Attività completata con condizione ancora presente.
**PASS** se gli utenti confermano che il Cockpit mostra informazioni di controllo utili prima o in modo più affidabile del processo attuale, **senza** data entry duplicato.

## Definizione di "slice completata"
1. Gate 1–6 superati e documentati nella PR.
2. Test nuovi per ogni regola di dominio introdotta.
3. Migrazione Alembic inclusa e reversibile.
4. Documentazione aggiornata (Data Contract / Gap / CLAUDE.md se cambia una regola).
5. Approvazione umana.
