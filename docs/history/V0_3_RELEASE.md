# V0.3 — Project Intelligence

## Obiettivo
Dimostrare il passaggio da un cockpit basato su dati strutturati a un sistema capace di interpretare anche comunicazioni non strutturate, mantenendo controllo umano e tracciabilità.

## Nuovi componenti
- `app/intelligence.py`: motore locale di estrazione.
- `AgentFinding`: finding strutturato e revisionabile.
- `AgentRun`: audit di ogni esecuzione dell'agente.
- endpoint di analisi per singola commessa.
- endpoint di review finding.
- form live per aggiungere una mail demo e analizzarla.
- import Excel delle comunicazioni.

## Principio di sicurezza funzionale
L'agente non ha write access ai dati autorevoli. Può solo creare finding e alert. Il passaggio da informazione estratta a dato ufficiale richiede una futura azione/validazione esplicita.

## Provider abstraction
La V0.3 usa `LOCAL_PROJECT_INTELLIGENCE_V1`. La logica di dominio non dipende dal provider: in una release produttiva l'engine potrà essere sostituito da un modello enterprise mantenendo `AgentFinding` come contratto d'uscita.
