# Matrice pulsanti → conseguenze — V0.3.8

## Regola fondamentale

**READ MANY, WRITE LITTLE.** Le azioni del cockpit possono modificare soltanto il layer operativo. Non modificano Galileo, Pipedrive, Outlook, planning ufficiale, documenti tecnici, PO/contratto o altri master data.

| Pulsante | Oggetto | Conseguenza persistente | Cosa NON fa |
|---|---|---|---|
| Apri operatività | UI | apre il workspace | non modifica dati |
| Crea attività / verifica | Action | crea owner/reparto, scadenza e origine | non modifica la condizione sorgente |
| Prendi in carico / Riassegna | Action | aggiorna l'owner operativo | non cambia ruoli nei sistemi sorgente |
| Invio | ActionMessage | registra il messaggio OUTBOUND e prova a copiarne il testo | non invia email/Teams/WhatsApp |
| Registra risposta ricevuta | ActionMessage | registra una risposta arrivata fuori dal cockpit | non chiude automaticamente l'azione |
| Conferma e chiudi | Action | chiude dopo validazione del richiedente | non chiude automaticamente la causa sorgente |
| Conferma finding | AgentFinding | `NEW → VALIDATED` | non modifica KPI/master data |
| Scarta finding | AgentFinding / CockpitDecision | registra la disposizione `DISMISSED` | non cancella la fonte |
| Recepisci nel cockpit | Finding validato | crea/aggiorna una conseguenza nel layer operativo | non scrive nelle sorgenti ufficiali |
| Conferma saving | CockpitDecision | classifica il residuo come saving consolidato | non rialloca budget né modifica Galileo |
| Chiarisci / Congela condizione | CockpitDecision | salva interpretazione contrattuale operativa con fonte/validatore | non modifica PO/contratto originale |
| Riapri chiarimento | CockpitDecision | riapre l'interpretazione operativa con motivo | non altera la fonte |
| Crea verifica al Commerciale | Action | apre verifica su un change potenziale | non formalizza un extra |
| Genera piano di recupero confidence | Action | crea azioni sui gap Low/Insufficient | non modifica direttamente dati mancanti |
| Analizza comunicazioni | Intelligence | crea/aggiorna finding | non applica finding |

## Regola alert/azione

Un alert deterministico resta attivo finché la sua condizione sorgente è vera. Un'azione completata non equivale alla risoluzione della criticità. Una risposta ricevuta passa prima dalla validazione del richiedente.
