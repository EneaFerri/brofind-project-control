# V0.3.2 — Workflow operativo e tracciabilità

Questa release rende più immediato il lavoro sul progetto senza appesantire la vista executive.

## Principi
- Il pannello operativo resta aperto durante Analizza → Conferma → Registra.
- Ogni pulsante produce una conseguenza persistente e un feedback esplicito.
- Le criticità executive mostrano il blocco e permettono di aprire la fonte che lo genera.
- I segnali dalle comunicazioni non influenzano lo stato della commessa finché non vengono confermati e registrati.
- Per P-26004, un sollecito cliente registrato crea una criticità visibile; se è presente anche documentazione mancante, la vista executive aggrega i due aspetti in un unico blocco comprensibile.

## Attività
- Le attività possono essere riassegnate a un altro utente demo.
- Ogni task ha una conversazione interna.
- È possibile scrivere un messaggio manualmente oppure preparare un testo suggerito e modificarlo prima di registrarlo.
- Completare un task non chiude automaticamente la criticità sorgente.

## Fonti
- Ogni criticità espone “Vedi cosa lo genera”.
- La tab Fonti e comunicazioni raccoglie mail e dati strutturati (milestone, fatture, budget, attività, issue e varianti).

## Test
18 test automatici coprono regole, workflow AI, visibilità, riassegnazione task, messaggi e caso P-26004.
