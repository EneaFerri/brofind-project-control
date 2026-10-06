# Demo B1 — runbook rapido

## Avvio

1. Dalla root del repository, eseguire `start_demo.bat`.
2. Attendere l'apertura automatica del browser: avviene solo dopo `/health` valido.
3. Per un controllo manuale: `http://127.0.0.1:8080/health` deve rispondere `status: ok`, `runtime: demo`.

## Preparazione sorgenti

Con la `.venv` già predisposta, dalla root eseguire:

    .\.venv\Scripts\python.exe scripts\prepare_b1_demo_sources.py

Lo script locale copia nei tre percorsi `data_sources/DEMO-B1-001/` il file Galileo, il contratto PDF e l'email Outlook EML. Non usa Internet.

## Percorso demo

1. Come Direzione (selettore **Utente** in basso a sinistra) creare `DEMO-B1-001` da **Nuova commessa**, con PM `A. Greco` e Commerciale `S. Riva`.
2. Nella commessa aprire **Fonti** (header): **Aggiorna fonti**, poi **Importa dati Galileo**, **Leggi documenti** e **Leggi email**.
3. Aprire **AI** (header) → **Analizza fonti**. Confermare `Cliente` e `Valore contratto`; lasciare `Cap penali` **Da verificare**.
4. Come PM, nella pagina **Criticità** creare l'attività dal segnale della fattura scaduta; come Amministrazione prenderla in carico e rispondere da **Attività**; come PM confermare e chiudere.
5. In **Portfolio** verificare la commessa in rosso: sforamento locale EUR 40.000 (**Economics**) e fattura scaduta EUR 200.000 (**Billing & Payment**).

## Arresto server

Eseguire `stop_demo.bat`. Arresta esclusivamente il processo `.venv` che esegue `uvicorn app.main:app` in ascolto sulla porta 8080; non termina altri processi Python.

## Recupero in caso di errore

1. Per ripartire con dati demo puliti: eseguire `stop_demo.bat`, rinominare `data\demo\brofind_demo.db` in `brofind_demo.db.bak` e rilanciare `start_demo.bat`.
2. Se `/health` non risponde, controllare `data/demo/logs/server.stderr.log`.
3. Se la `.venv` è incompleta o non è Python 3.13, eliminarla manualmente e rilanciare `start_demo.bat` per il setup iniziale.
4. Se mancano le sorgenti B1, rieseguire `scripts/prepare_b1_demo_sources.py`.
