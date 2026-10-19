"""Avvio della demo portatile per Windows: doppio clic su "Avvia Cockpit", nessun comando da digitare.

Il server gira dentro la finestra aperta dal doppio clic: finché la finestra è aperta il Cockpit
funziona, chiudendola si spegne. Nessun processo nascosto da arrestare a parte.
"""

import json
import logging
import os
import socket
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEMO_DATA = ROOT / "data" / "demo"
DATABASE_PATH = DEMO_DATA / "brofind_demo.db"
LOG_PATH = DEMO_DATA / "logs" / "cockpit.log"
UNBLOCK_MARKER = ROOT / "data" / ".file_sbloccati"
PORTS = range(8080, 8100)
STARTUP_TIMEOUT_SECONDS = 180

RIGA = "=" * 64


def stampa(testo: str = "") -> None:
    print(testo, flush=True)


def prepara_finestra() -> None:
    """Titolo della finestra e disattivazione della "modifica rapida" della console.

    Con la modifica rapida attiva, un clic nella finestra mette in pausa l'output e il server si blocca
    finché non si preme un tasto: per chi non conosce la console sembrerebbe un Cockpit "congelato".
    """
    if os.name != "nt":
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleTitleW("Brofind Control Cockpit - Demo")
    handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        enable_quick_edit, enable_extended_flags = 0x0040, 0x0080
        kernel32.SetConsoleMode(handle, (mode.value & ~enable_quick_edit) | enable_extended_flags)


def sblocca_file_scaricati() -> None:
    """Rimuove il contrassegno "scaricato da Internet" dai file della demo (come Unblock-File), una volta sola.

    Se lo zip è arrivato via email o browser, Windows marca ogni file estratto e può rifiutare di caricare
    le librerie della demo. È l'equivalente di Proprietà > "Sblocca" sullo zip, applicato a questa cartella.
    """
    if os.name != "nt" or UNBLOCK_MARKER.exists():
        return
    for directory, _subdirs, files in os.walk(ROOT):
        for name in files:
            try:
                os.remove(os.path.join(directory, name) + ":Zone.Identifier")
            except OSError:
                pass
    UNBLOCK_MARKER.parent.mkdir(parents=True, exist_ok=True)
    UNBLOCK_MARKER.write_text("ok\n", encoding="ascii")


def leggi_health(port: int) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
            return json.load(response)
    except Exception:
        return None


def e_questo_cockpit(health: dict | None) -> bool:
    return bool(health) and health.get("runtime") == "demo" and health.get("database") == DATABASE_PATH.name


def porta_libera(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def configura_log() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def apri_browser_quando_pronto(port: int, server) -> None:
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline and not server.should_exit:
        if e_questo_cockpit(leggi_health(port)):
            webbrowser.open(url)
            stampa()
            stampa(RIGA)
            stampa("   IL COCKPIT È ACCESO e si è aperto nel browser.")
            stampa(f"   Indirizzo: {url}")
            stampa()
            stampa("   >> NON chiudere questa finestra mentre usi il Cockpit.")
            stampa('      Puoi ridurla a icona con il tasto "_" in alto a destra.')
            stampa()
            stampa("   >> Quando hai finito, chiudi questa finestra con la X:")
            stampa("      il Cockpit si spegne. I dati inseriti restano salvati.")
            stampa(RIGA)
            return
        time.sleep(0.5)
    if not server.should_exit:
        stampa()
        stampa("   Il Cockpit non ha risposto in tempo.")
        stampa('   Chiudi questa finestra e fai di nuovo doppio clic su "Avvia Cockpit".')
        stampa(f"   Se il problema si ripete, invia a chi ti ha dato la demo il file:\n   {LOG_PATH}")
        server.should_exit = True


def main() -> int:
    prepara_finestra()
    stampa(RIGA)
    stampa("   BROFIND CONTROL COCKPIT - DEMO")
    stampa(RIGA)
    stampa()

    for port in PORTS:
        if e_questo_cockpit(leggi_health(port)):
            stampa("   Il Cockpit è già acceso in un'altra finestra: lo apro nel browser.")
            webbrowser.open(f"http://127.0.0.1:{port}")
            time.sleep(4)
            return 0

    port = next((candidate for candidate in PORTS if porta_libera(candidate)), None)
    if port is None:
        stampa("   Non ho trovato una porta libera sul computer per avviare il Cockpit.")
        stampa("   Riavvia il computer e riprova.")
        return 1

    stampa("   Avvio in corso, attendi qualche secondo...")
    stampa("   (la prima volta può servire fino a un minuto)")

    sblocca_file_scaricati()
    configura_log()

    # Impostati prima di importare l'applicazione: app.config li legge all'import.
    os.environ["BROFIND_RUNTIME"] = "demo"
    os.environ["BROFIND_DATABASE_PATH"] = str(DATABASE_PATH)
    os.environ.pop("DATABASE_URL", None)
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import uvicorn

    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=port, log_config=None)
    server = uvicorn.Server(config)
    threading.Thread(target=apri_browser_quando_pronto, args=(port, server), daemon=True).start()
    try:
        server.run()
    except SystemExit as exit_request:
        if exit_request.code not in (None, 0):
            raise RuntimeError(f"Il server si è fermato con codice {exit_request.code}.") from exit_request
    if not server.started:
        raise RuntimeError("Il server non è partito.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        logging.getLogger("avvio_demo").error("Avvio non riuscito\n%s", traceback.format_exc())
        stampa()
        stampa("   Avvio del Cockpit non riuscito.")
        stampa('   Chiudi questa finestra e riprova con un doppio clic su "Avvia Cockpit".')
        stampa("   Se il problema si ripete, invia a chi ti ha dato la demo il file:")
        stampa(f"   {LOG_PATH}")
        sys.exit(1)
