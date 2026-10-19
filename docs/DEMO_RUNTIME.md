# Runtime locale della demo

Questa procedura è il percorso supportato per la demo Windows del Cockpit.
Non richiede Docker e non richiede di copiare un ambiente virtuale da un altro
PC.

## Prerequisito Python

Il runtime demo supporta **Python 3.13, 3.14 e 3.15** (`requires-python`
in pyproject.toml).

- Da v1.0.1 tutte le dipendenze di requirements.txt sono disponibili come
  wheel precompilate per 3.13, 3.14 e 3.15 su Windows, Linux e macOS: il
  setup non richiede compilazione locale (bloccata da Smart App Control).
  Unica eccezione: red-black-tree-mod (dipendenza di extract-msg) è
  distribuito solo come sorgente, ma è puro Python e non serve compilatore.
- Per questo sono stati rimossi pandas (non usato dal codice) e pyyaml
  (incluso da uvicorn[standard], serve solo a --log-config YAML): gli altri
  extra "standard" di uvicorn sono elencati esplicitamente.
- Non aggiornare le dipendenze sul PC della demo.

start_demo.bat cerca, in ordine, Python 3.15, 3.14 e 3.13 e rifiuta una
.venv creata con una versione diversa.

## Trasferimento sul PC Brofind

1. Copiare o estrarre l'intero repository senza .venv, cache, database
   runtime o log.
2. Installare Python 3.13, 3.14 o 3.15 includendo il Python Launcher per
   Windows.
3. Per il primo setup, assicurarsi che il PC possa installare i pacchetti
   indicati in requirements.txt.
4. Eseguire start_demo.bat.

Se .venv non esiste, lo script:

1. cerca una versione supportata di Python (3.15, poi 3.14, poi 3.13);
2. crea <repository>\.venv;
3. installa requirements.txt;
4. verifica import e coerenza delle dipendenze;
5. avvia il server solo se il setup è riuscito.

Agli avvii successivi non viene eseguito pip install: la .venv locale viene
validata e il Cockpit può partire offline.

La .venv non è trasferibile tra PC. Se è incompleta o usa una versione Python
non supportata, rimuoverla e ripetere il setup sul PC di destinazione.

## Dipendenze e test di sviluppo

Le dipendenze di test sono separate dalle dipendenze runtime della demo.
Non vengono installate da start_demo.bat e non sono incluse in requirements.txt.

Per installarle nella .venv locale:

    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

Per eseguire i test:

    .\.venv\Scripts\python.exe -m pytest

## Avvio normale

Eseguire start_demo.bat.

Lo script risolve sempre la root del repository, anche se viene richiamato da
un'altra working directory. Uvicorn parte in una finestra nascosta. Il browser
viene aperto soltanto quando /health conferma:

- status = ok;
- runtime = demo;
- database attivo coerente con il percorso richiesto.

Un errore di setup, avvio o health check produce exit code non zero e non apre
il browser.

Smoke test senza browser:

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -NoBrowser -Port 18080

## Database

Percorsi runtime:

- demo attiva: data/demo/brofind_demo.db;
- sviluppo: data/development/brofind_control_dev.db;
- test: data/test/brofind_test_<pid>.db.

Questi path sono risolti dalla root del repository e non dalla current working
directory.

Il file storico data/brofind_control_v038.db resta invariato e non è usato
come fallback dai nuovi runtime.

Il percorso riservato a un futuro golden database è:

    data/demo/golden/

Questo change-set non crea il golden DB. Quando sarà disponibile, il recovery
dovrà copiare il golden verso data/demo/brofind_demo.db esclusivamente a
server fermo. Il golden non dovrà mai essere aperto direttamente dal runtime.

## Backup e recovery

Per effettuare un backup:

1. arrestare il processo Uvicorn;
2. copiare data/demo/brofind_demo.db;
3. conservare la copia con nome e data chiaramente identificabili.

Non usare /api/demo/reset durante la presentazione. Nel runtime demo il reset
distruttivo è disabilitato e il relativo comando non è mostrato in Dashboard.
Il reset resta disponibile soltanto nei runtime development e test.

## Configurazione

Variabili supportate:

- BROFIND_RUNTIME: development, demo o test;
- BROFIND_DATABASE_PATH: percorso SQLite assoluto o relativo alla root;
- DATABASE_URL: compatibilità per il solo runtime development.

Il runtime test è fail-closed: richiede un BROFIND_DATABASE_PATH esplicito
sotto data/test e non usa mai DATABASE_URL o altri fallback.
