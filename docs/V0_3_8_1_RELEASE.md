# Brofind Project Control V0.3.8.1 — Confidence Foundation Fix

Patch di fondazione emersa dalla review guidata della V0.3.8.

## Principio
La confidence misura ciò che l'azienda sa della commessa, non quanto lavoro di normalizzazione è già stato completato nel cockpit.

## Modifiche
- separati i veri gap informativi dal backlog di strutturazione/validazione del cockpit;
- separata la confidence dello stato economico corrente dalla confidence del forecast finale;
- 9028: Economia Alta, Procurement Media, Contratto Media, Tempi Insufficiente, Tecnica Media; overall Media;
- la vicinanza alla consegna non abbassa più la confidence procurement: resta un segnale di rischio operativo;
- le condizioni contrattuali già presenti nel dossier ma non ancora frozen sono backlog di processing, non automaticamente gap informativi;
- il conteggio in UI mostra aree da migliorare, non il numero grezzo di frasi/gap;
- pacchetto contrattuale completo rende il dominio contratto valutabile;
- correzione sticky header del portfolio sotto la barra globale.

## Regola preservata
READ MANY, WRITE LITTLE: nessun dato sorgente viene modificato dal cockpit.
