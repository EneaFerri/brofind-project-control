## Cosa cambia

<!-- Breve descrizione. Slice del piano V1, se applicabile (es. S3). -->

## Autorità di riferimento

<!-- Paragrafi del Product Freeze, sezione del Data Contract, mockup canonico usato. -->

## Checklist

- [ ] Nessuna scrittura su dati sorgente (READ MANY, WRITE LITTLE)
- [ ] Dati mancanti/non aggiornati mai mostrati come regolari
- [ ] Permessi verificati lato server per ogni nuova azione
- [ ] Modifiche allo schema con migrazione Alembic
- [ ] Test aggiunti/aggiornati; CI verde
- [ ] Per modifiche UI: screenshot affiancato al mockup canonico
- [ ] Testi utente in italiano e comprensibili
- [ ] Eventuali IMPLEMENTATION GAP registrati, non risolti riprogettando
- [ ] Nessun dato reale di clienti, documento interno o segreto
