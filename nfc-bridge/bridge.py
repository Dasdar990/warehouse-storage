#!/usr/bin/env python3
"""
NFC badge bridge per il login con dongle MIKROE-2540 (NXP PN7150).
====================================================================

Il binario NXP-NCI_Linux_example non è una tastiera HID: stampa semplicemente
righe di testo sul proprio stdout quando un badge viene avvicinato o
allontanato. Il browser non può leggere lo stdout di un processo, quindi
questo script fa da ponte ("bridge"):

    dongle USB --(NCI/HID)--> binario NXP --(stdout)--> questo script
                                                              |
                                                    WebSocket locale (JSON)
                                                              |
                                                          pagina di login

Va eseguito SULLA STESSA macchina il cui browser mostra la pagina di
login (di solito il totem/kiosk a cui è collegata la dongle), perché il
WebSocket viene esposto solo su localhost per default. Il backend può
invece girare altrove: il bridge non parla mai con l'API, si limita a
notificare il browser, che poi chiama lui stesso `/auth/badge-login`
(vedi `frontend/composables/useNfcBridge.ts`).

Uso
---
    pip install -r requirements.txt
    python3 bridge.py /percorso/del/binario/nxp-nci-demo
    python3 bridge.py /percorso/del/binario/nxp-nci-demo --ws-host 127.0.0.1 --ws-port 8765

Formato dei messaggi WebSocket (uno per riga, JSON):
    {"type": "badge_tap",     "uid": "E6528382"}   -> badge letto
    {"type": "badge_removed"}                       -> badge allontanato
    {"type": "reader_status", "status": "waiting"}   -> reader in attesa di un tag
"""

import argparse
import asyncio
import json
import re
import subprocess
import sys
import threading
import time
from typing import Optional, Set

try:
    import websockets
except ImportError:
    print(
        "Manca la dipendenza 'websockets'. Installala con:\n"
        "    pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Pattern per estrarre l'UID dall'output del binario NXP. L'output reale
# osservato con MIKROE-2540 + PN7150 è del tipo:
#
#   [nxp-nci]       NFCID = e6 52 83 82
#
# ma alcune versioni/varianti del pacchetto NXP usano "UID" o "NFCID1"
# invece di "NFCID" da solo, quindi il pattern copre tutte e tre le forme.
# ---------------------------------------------------------------------------
UID_PATTERN = re.compile(
    r"(?:NFCID1?|UID)\s*[:=]?\s*((?:[0-9A-Fa-f]{2}[\s:]?){4,10})"
)
CARD_REMOVED_PATTERN = re.compile(r"CARD REMOVED", re.IGNORECASE)
WAITING_PATTERN = re.compile(r"WAITING FOR DEVICE DISCOVERY", re.IGNORECASE)

# Se lo stesso UID viene notificato due volte più veloce di così, la seconda
# viene ignorata: protegge da eventuali doppi trigger del binario NXP senza
# introdurre un vero e proprio ritardo percepibile da chi usa il badge.
DEBOUNCE_SECONDS = 1.0


class NxpNciReader:
    """
    Avvia l'eseguibile NXP come sottoprocesso e legge il suo stdout in un
    thread separato, invocando le callback quando rileva un tag, la sua
    rimozione, o un cambio di stato del reader.
    """

    def __init__(
        self,
        executable_path: str,
        on_tag: Optional[callable] = None,
        on_removed: Optional[callable] = None,
        on_waiting: Optional[callable] = None,
    ):
        self.executable_path = executable_path
        self.on_tag = on_tag
        self.on_removed = on_removed
        self.on_waiting = on_waiting
        self.process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
        self._reader_thread: Optional[threading.Thread] = None
        self._last_uid: Optional[str] = None
        self._last_uid_time: float = 0.0

    def start(self) -> None:
        """
        Avvia il processo NXP e il thread di lettura dell'output.

        NOTA sul buffering: quando lo stdout di un programma C viene
        reindirizzato a una pipe invece che a un terminale, la libc passa da
        "line buffered" a "fully buffered" e l'output resta bloccato nel
        buffer interno finché non si riempie o il processo termina. Usiamo
        `stdbuf -oL` (coreutils) per forzare il line-buffering anche su pipe.
        """
        cmd = ["stdbuf", "-oL", "-eL", self.executable_path]
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            print(
                "Attenzione: 'stdbuf' non trovato, l'output potrebbe arrivare "
                "in ritardo (bufferizzato). Su macOS installa 'coreutils' con "
                "brew e usa 'gstdbuf'.",
                file=sys.stderr,
            )
            self.process = subprocess.Popen(
                [self.executable_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def _read_loop(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        for raw_line in self.process.stdout:
            if self._stop_event.is_set():
                break
            line = raw_line.rstrip()
            if not line:
                continue

            print(f"[nxp-nci] {line}")

            if CARD_REMOVED_PATTERN.search(line):
                if self.on_removed:
                    self.on_removed()
                continue

            if WAITING_PATTERN.search(line):
                if self.on_waiting:
                    self.on_waiting()
                continue

            match = UID_PATTERN.search(line)
            if match:
                uid = self._normalize_uid(match.group(1))
                if self._is_debounced(uid):
                    continue
                if self.on_tag:
                    self.on_tag(uid)

    def _is_debounced(self, uid: str) -> bool:
        now = time.monotonic()
        is_repeat = uid == self._last_uid and (now - self._last_uid_time) < DEBOUNCE_SECONDS
        self._last_uid = uid
        self._last_uid_time = now
        return is_repeat

    @staticmethod
    def _normalize_uid(raw: str) -> str:
        """Normalizza l'UID rimuovendo spazi/':' e mettendo in maiuscolo.

        Stessa normalizzazione applicata lato backend
        (`normalize_badge_uid` in `user_service.py`), così un badge letto
        qui corrisponde sempre a quanto salvato nel database.
        """
        cleaned = re.sub(r"[\s:]", "", raw)
        return cleaned.upper()

    def stop(self) -> None:
        self._stop_event.set()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()


class BridgeServer:
    """Server WebSocket locale che inoltra gli eventi del reader ai client connessi (di norma una sola scheda di login aperta nel browser)."""

    def __init__(self):
        self.clients: Set["websockets.WebSocketServerProtocol"] = set()

    async def handler(self, websocket) -> None:
        self.clients.add(websocket)
        print(f"Client connesso ({len(self.clients)} totali)")
        try:
            async for _ in websocket:
                pass  # non ci aspettiamo messaggi dal client, solo lo teniamo aperto
        finally:
            self.clients.discard(websocket)
            print(f"Client disconnesso ({len(self.clients)} totali)")

    async def broadcast(self, message: dict) -> None:
        if not self.clients:
            return
        payload = json.dumps(message)
        # gather con return_exceptions per non far fallire il broadcast
        # intero se un client si è disconnesso proprio in questo istante.
        await asyncio.gather(
            *(client.send(payload) for client in list(self.clients)),
            return_exceptions=True,
        )


async def run(executable: str, ws_host: str, ws_port: int) -> None:
    loop = asyncio.get_running_loop()
    server = BridgeServer()

    def on_tag(uid: str) -> None:
        print(f">>> Badge letto! UID: {uid}")
        asyncio.run_coroutine_threadsafe(
            server.broadcast({"type": "badge_tap", "uid": uid}), loop
        )

    def on_removed() -> None:
        asyncio.run_coroutine_threadsafe(
            server.broadcast({"type": "badge_removed"}), loop
        )

    def on_waiting() -> None:
        asyncio.run_coroutine_threadsafe(
            server.broadcast({"type": "reader_status", "status": "waiting"}), loop
        )

    reader = NxpNciReader(executable, on_tag=on_tag, on_removed=on_removed, on_waiting=on_waiting)
    reader.start()

    async with websockets.serve(server.handler, ws_host, ws_port):
        print(f"Bridge NFC in ascolto su ws://{ws_host}:{ws_port}")
        print(f"Avvio {executable} ... (Ctrl+C per uscire)")
        try:
            while reader._reader_thread and reader._reader_thread.is_alive():
                await asyncio.sleep(1)
            print("Il processo NXP si è chiuso inaspettatamente.")
        except asyncio.CancelledError:
            pass
        finally:
            reader.stop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bridge WebSocket tra il reader NFC PN7150 (dongle MIKROE-2540) e la pagina di login."
    )
    parser.add_argument("executable", help="Percorso del binario NXP-NCI_Linux_example")
    parser.add_argument("--ws-host", default="127.0.0.1", help="Host su cui esporre il WebSocket (default: 127.0.0.1)")
    parser.add_argument("--ws-port", type=int, default=8765, help="Porta WebSocket (default: 8765)")
    args = parser.parse_args()

    try:
        asyncio.run(run(args.executable, args.ws_host, args.ws_port))
    except KeyboardInterrupt:
        print("\nArresto in corso...")


if __name__ == "__main__":
    main()
