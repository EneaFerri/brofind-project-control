# 07 — Decisioni aperte

**Data:** 2026-10-06 · Ogni voce indica la slice che blocca e una proposta.

| ID | Decisione | Blocca | Proposta |
|---|---|---|---|
| OD-01 | Recuperare i freeze mancanti: Workflow v1.1, Operational Control v1.0, Collaboration v1.0, UI Freeze Gestione operativa v1.0, DEC-019…026; eventuale lavoro "Stage 1 / economic_v1" | S10 (anche S4 per economic_v1) | recuperarli dal PC Windows / dalle sessioni precedenti; altrimenti riscriverli in forma compatta con approvazione |
| OD-02 | Lingua delle etichette di navigazione: inglese (Shell Contract, A14, mockup) o italiano (Italiano-first, glossario) | S2 | navigazione come nei mockup (autorità più recente), tutto il resto in italiano; titoli di pagina in italiano (es. "Controllo tecnico" come già nel mockup V05) |
| OD-03 | Autorità visiva: Figma (nodi citati in `03_UI_GOVERNANCE` §9) o gli 8 PNG (A14) | S2 | gli 8 PNG + Shell Contract (A14 è successivo); aggiornare `03_UI_GOVERNANCE` di conseguenza |
| OD-04 | Fornitore di identità aziendale: Microsoft 365 / Entra ID? | S12 (S1 solo come interfaccia) | Entra ID OIDC sul tenant brofind.com |
| OD-05 | Macro-famiglie di costo (Materiali, Subforniture, Manodopera, Trasporti, Service, Altro nel mockup V04) e mappatura VdA → famiglia | S4 | definirle con Amministrazione; nel frattempo raggruppare per natura VdA dichiarandolo |
| OD-06 | Metodo numerico dell'avanzamento reale per il Payment | S5 | `N/D` esplicito finché non approvato; candidati: % milestone maturate pesate, costo assorbito/forecast |
| OD-07 | Destino delle commesse simulate P-26001…012 | S3 | sostituirle con il dataset demo V1 coerente; mantenere 9028 e DEMO-B1-001 come regressione |
| OD-08 | AI generativa per il drawer: fornitore, dove girano i dati, budget | S11 | decidere con Direzione/IT; fino ad allora drawer con risposte deterministiche e nessun invio di dati all'esterno |
| OD-09 | Soglie di default: freschezza per fonte, lead time per categoria, tolleranza billing | S3–S7 | default dichiarati nei Settings, marcati "provvisori" in UI fino ad approvazione |
| OD-10 | Catalogo ruoli applicativi e perimetri iniziali | S1 | ruoli di esempio di ADR-005, da confermare |
| OD-11 | Integrazione reale Galileo (API, DB, export) e Outlook (casella condivisa vs cartella) | S12+ | per V1 restano import da cartella; integrazione live dopo v1.0 |
| OD-12 | Hosting in rete aziendale: server Windows o Linux/Docker, chi lo gestisce | S12 | da definire con IT Brofind |
| OD-13 | Chi approva i gate (A22) | tutte | indicare il Product Owner |
| OD-14 | Rendere pubblico il repository: con quali dati e documenti (mockup con nomi clienti) | prima della pubblicazione | sostituire i mockup con versioni anonimizzate; verificare la storia Git |
