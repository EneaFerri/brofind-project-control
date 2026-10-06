# V0.3.1 — UX / Workflow Revision

## Obiettivo
Separare la vista executive dal lavoro operativo e rendere deterministica la conseguenza di ogni comando utente.

## Modifiche principali
- Workspace operativo laterale con tab `Azioni`, `Project Intelligence`, `Evidenze`.
- Pagina progetto alleggerita: stati, KPI, criticità principali, esposizioni e controlli strutturati.
- Finding AI esclusi dal Rules Engine fino all'applicazione esplicita.
- Stato finding esteso con `APPLIED` e tracciamento della conseguenza.
- Endpoint `/api/findings/{id}/apply`.
- `create-action` non cambia lo stato dell'alert.
- Gli alert deterministici non possono essere chiusi manualmente.
- Feedback toast esplicito per le operazioni principali.
- `Prova una mail` e `Analizza comunicazioni` restituiscono risultati leggibili.
- 16 test automatici PASS.
