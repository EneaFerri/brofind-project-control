# Brofind Project Control V0.3.6 — Analysis Engine Pilot

## Obiettivo
La V0.3.6 non prova a generare un forecast ETC artificiale. Introduce invece una prima logica di analisi che incrocia dati Galileo, natura delle VdA, stato acquisti, fase di commessa e requisiti estratti dai documenti.

## Pilot 9028
- Ordine base PO-PILOT-001 marcato come pacchetto contrattuale acquisito/completo.
- PO Extra 1 formalizzato e acquisito.
- Requisito contrattuale LEL collegato alla VdA ANALIZZATORI.
- Secondo LEL da open points Rev.2 registrato come finding da validare, non come fatto contrattuale già approvato.
- Fase procurement impostata come `NEAR` sulla base del contesto del pilot; la data planning definitiva non è ancora una fonte strutturata.

## Procurement Analysis
Le VdA vengono classificate per natura: acquisto diretto, servizi/montaggi, ore interne, logistica, riserva o non classificata.

La colonna acquisti distingue ora:
- Non avviati
- Aperti
- In corso · chiusura N/D
- Conclusi
- Da contestualizzare
- N/A / N/D

Il rischio acquisti è separato dallo stato economico. In assenza di una required date affidabile, il motore segnala una verifica e non dichiara automaticamente un ritardo.

## Regola di affidabilità
Un requisito documentale non ancora validato come variazione non diventa automaticamente una criticità. Rimane un finding umano da confermare/applicare.
