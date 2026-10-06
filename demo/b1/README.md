# Demo B1 — contratto del caso congelato

Questa directory contiene il caso dimostrativo versionabile `DEMO-B1-001`.
Gli asset sono deliberatamente limitati a un PDF testuale concordato, un
workbook Excel controllato e una email EML di follow-up pagamento. Non
costituiscono un formato di import generale.

## Confini del caso

- Stato logico alla creazione: `ACQUISIZIONE_DATI`.
- PM: A. Greco (`pm_greco`).
- Commerciale: S. Riva (`sales_riva`).
- Prospettiva futura Amministrazione: Amministrazione — Demo (`admin_demo`).
- Valuta: EUR.
- Persistenza prevista: SQLite locale.
- Nessuna autenticazione reale e nessuna integrazione live.
- Il PDF è testuale; OCR, scansioni, dossier multipli e revisioni sono esclusi.
- Il workbook ha formato fisso e contiene soltanto `CONTROL_SNAPSHOT`,
  `CONTROL_LINES` e `INVOICES`.
- `PAYMENTS` è escluso. `INVOICES.Paid_Amount` è l'unica fonte autorevole del
  pagato per il caso B1.

Alla creazione della commessa sono noti soltanto codice, PM e Commerciale.
Cliente, valore e gli altri dati contrattuali non sono confermati prima della
review del PDF. Un eventuale placeholder reso necessario dal modello dati
applicativo dovrà essere marcato come tecnico e non confermato, non alimentare
lo screening e non essere presentato come dato sorgente.

## File

- `case_manifest.json`: identità, dati contrattuali attesi, workbook congelato
  e regole di autorità/provenienza.
- `expected_results.json`: risultati osservabili richiesti nella vertical slice.
- `source/DEMO-B1-001_contract.txt`: sorgente canonica del PDF testuale.
- `assets/DEMO-B1-001_contract.pdf`: contratto dimostrativo.
- `assets/DEMO-B1-001_control.xlsx`: dati economici VdA/CDA e fattura.
- `assets/DEMO-B1-001_payment_followup.eml`: comunicazione Outlook demo sul pagamento.
- `SHA256SUMS`: impronte degli asset e delle specifiche.

## Risultati obbligatori

Il caso è costruito affinché, dopo review e importazione controllata, risultino:

- sforamento economico rilevato: EUR 40.000;
- fattura scaduta residua: EUR 200.000;
- entrambe le situazioni richiedono intervento;
- almeno un dato CORE confermato e il `penalty_cap` lasciato da verificare;
- Action assegnabile ad Amministrazione con scambio PM → Amministrazione → PM;
- comparsa coerente della commessa nel Portfolio Direzione.

La severity tecnica dell'alert e l'etichetta esatta di priorità del Portfolio
non sono congelate in questo change-set. Se l'applicazione produrrà `HIGH` o
`Da intervenire`, tali esiti saranno confermati nell'Acceptance Test.

## Regole per i change-set successivi

1. Il valore operativo contrattuale può derivare soltanto da un valore
   confermato dall'utente.
2. La catena concettuale resta:
   `SOURCE VALUE → EXTRACTED VALUE → USER CONFIRMED VALUE → OPERATIONAL VALUE`.
3. Un valore `TO_VERIFY` non alimenta controlli critici.
4. Il workbook può essere interpretato soltanto secondo il formato congelato
   nel manifest; non è promessa compatibilità con workbook arbitrari.
5. Gli importi sono netti, in EUR. Le date sono ISO 8601 nel manifest e vere
   date Excel nel workbook.
6. Gli asset non devono essere importati nel database da questo change-set.

## Verifica di integrità

Le impronte in `SHA256SUMS` consentono di verificare che gli asset usati nella
demo coincidano con quelli approvati. Il file non include la propria impronta.

