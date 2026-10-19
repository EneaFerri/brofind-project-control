"""Riporta la demo portatile ai dati iniziali, conservando una copia dei dati attuali.

Il database corrente viene spostato in data/demo/backup/ (mai cancellato); al prossimo avvio il Cockpit
ricrea i dati dimostrativi di partenza.
"""

import sys
from datetime import datetime

from avvio_demo import DATABASE_PATH, DEMO_DATA, PORTS, RIGA, e_questo_cockpit, leggi_health, stampa


def main() -> int:
    stampa(RIGA)
    stampa("   BROFIND CONTROL COCKPIT - RIPRISTINO DATI DEMO")
    stampa(RIGA)
    stampa()

    if any(e_questo_cockpit(leggi_health(port)) for port in PORTS):
        stampa("   Il Cockpit è ancora acceso.")
        stampa("   Chiudi prima la finestra del Cockpit, poi rifai doppio clic qui.")
        return 1

    if not DATABASE_PATH.exists():
        stampa("   La demo è già ai dati iniziali: non c'è nulla da ripristinare.")
        return 0

    stampa("   Questa operazione cancella dal Cockpit tutte le prove fatte")
    stampa("   (attività, decisioni, conferme...) e riporta i dati iniziali.")
    stampa("   Una copia dei dati attuali viene comunque conservata.")
    stampa()
    risposta = input("   Per confermare scrivi SI e premi INVIO: ").strip().upper()
    if risposta not in {"SI", "SÌ"}:
        stampa()
        stampa("   Nessuna modifica: i dati sono rimasti come prima.")
        return 0

    backup_dir = DEMO_DATA / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for suffix in ("", "-wal", "-shm"):
        current = DATABASE_PATH.with_name(DATABASE_PATH.name + suffix)
        if current.exists():
            current.rename(backup_dir / f"brofind_demo_{stamp}.db{suffix}")

    stampa()
    stampa("   Fatto. Al prossimo avvio il Cockpit ripartirà dai dati iniziali.")
    stampa(f"   Copia dei dati precedenti: {backup_dir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError:
        stampa()
        stampa("   Non è stato possibile ripristinare i dati: chiudi la finestra del Cockpit e riprova.")
        sys.exit(1)
