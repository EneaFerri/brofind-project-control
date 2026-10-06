# Brofind Project Control V0.3.5 — UX & Readability Pass

## Obiettivo
Rendere il cockpit interpretabile in pochi secondi prima di aggiungere nuove funzioni. La release non cambia il principio di autorità dei dati e non introduce un ETC strutturato obbligatorio.

## Portfolio
- 5 KPI principali invece di 7 card equivalenti.
- Conteggio distinto `Da intervenire` e `Da presidiare`.
- Stato delle dimensioni espresso con colore + testo.
- `N/D` grigio e `Dati parziali` neutro.
- Badge `Dati controllo reali` / `Demo` per distinguere la 9028 dalle commesse simulate.
- Metriche secondarie (extra non formalizzati, rischio penali, segnali) spostate sotto la sintesi.

## Pagina commessa
- Le aree `N/D` non simulano una criticità e non sono cliccabili come se contenessero alert.
- Il blocco principale diventa `Cosa richiede attenzione`.
- Severità localizzate in italiano.
- Il controllo economico occupa tutta la larghezza utile.
- `Forecast finale` ridotto a nota compatta quando non consolidabile.
- `Copertura informativa` sostituisce il falso senso di closing nelle fasi di esecuzione.

## Controllo VdA
Vista iniziale `Rilevanti`, con filtri:
- Criticità
- Acquisti aperti
- Acquisti conclusi
- Con extra
- Tutte

Terminologia:
- `Disponibile` -> `Budget disponibile`
- `Procurement` -> `Acquisti`
- `Budget` -> `Stato economico`

Le righe a zero restano disponibili ma non dominano la vista iniziale.

## Grammatica cromatica
- rosso: problema concreto / intervento;
- giallo: presidio / rischio / incertezza significativa;
- verde: fonte disponibile + valutazione regolare;
- grigio: N/D;
- grigio-azzurro: dati parziali.

## Validazione
Suite automatica: 28 test passati.
La regola economica di progetto resta beta e dovrà essere validata su altre commesse mature prima di essere congelata.
