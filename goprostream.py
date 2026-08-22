#!/usr/bin/env python3
"""GoPro Streaming Bridge.

Riceve il flusso UDP dalla GoPro Hero 4 e lo converte in RTMP
verso Nginx-RTMP per generare lo stream HLS.
"""

import logging
import os
import signal
import subprocess
import threading
import time
from typing import Optional

from goprocam import GoProCamera

# ─── Configurazione ──────────────────────────────────────────

GOPRO_IP: str = os.getenv("GOPRO_IP", "10.5.5.9")
RTMP_URL: str = os.getenv("RTMP_URL", "rtmp://localhost:1935/live/gopro")
KEEPALIVE_INTERVAL: int = int(os.getenv("KEEPALIVE_INTERVAL", "8"))
UDP_PORT: int = int(os.getenv("UDP_PORT", "8554"))

# ─── Logging ──────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("goprostream")


# ─── KeepAlive ───────────────────────────────────────────────

class KeepAliveTimer:
    """Mantiene attivo il WiFi della GoPro inviando KeepAlive a intervallo regolare."""

    def __init__(self, gopro: GoProCamera.GoPro, interval: int = 8) -> None:
        self._gopro = gopro
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        log.info("KeepAlive avviato (ogni %ds)", self._interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)
        log.info("KeepAlive fermato")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._gopro.KeepAlive()
                log.debug("KeepAlive inviato")
            except Exception as e:
                log.warning("KeepAlive fallito: %s", e)
            self._stop_event.wait(self._interval)


# ─── Streaming ───────────────────────────────────────────────

class GoProStream:
    """Bridge streaming: GoPro UDP → FFmpeg → RTMP → Nginx → HLS."""

    def __init__(self) -> None:
        log.info("Connessione alla GoPro (%s)...", GOPRO_IP)
        self._gopro = GoProCamera.GoPro(GOPRO_IP)
        self._ffmpeg: Optional[subprocess.Popen[bytes]] = None
        self._keepalive: Optional[KeepAliveTimer] = None

    def start_stream(self) -> None:
        """Avvia lo streaming: GoPro → FFmpeg → RTMP."""
        log.info("Avvio streaming...")
        self._gopro.livestream("start")
        time.sleep(1)

        udp_url = f"udp://{GOPRO_IP}:{UDP_PORT}"
        cmd = (
            f"ffmpeg -y -f mpegts -i {udp_url} "
            f"-c copy -an "
            f"-f flv {RTMP_URL}"
        )
        log.info("FFmpeg: %s", cmd)

        self._ffmpeg = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        # Verifica che FFmpeg sia partito
        time.sleep(1)
        if self._ffmpeg.poll() is not None:
            stderr = self._ffmpeg.stderr
            err_output = stderr.read().decode(errors="replace") if stderr else "sconosciuto"
            log.error("FFmpeg è terminato immediatamente: %s", err_output)
            raise RuntimeError(f"FFmpeg non è partito: {err_output}")

        # Avvia KeepAlive
        self._keepalive = KeepAliveTimer(self._gopro, KEEPALIVE_INTERVAL)
        self._keepalive.start()

        log.info("Streaming attivo. Ctrl+C per fermare.")

    def stop_stream(self) -> None:
        """Ferma tutto: KeepAlive, FFmpeg, GoPro."""
        log.info("Ferma streaming...")

        # Ferma KeepAlive
        if self._keepalive:
            self._keepalive.stop()

        # Ferma FFmpeg
        if self._ffmpeg and self._ffmpeg.poll() is None:
            log.info("Chiusura FFmpeg...")
            try:
                os.killpg(os.getpgid(self._ffmpeg.pid), signal.SIGTERM)
                self._ffmpeg.wait(timeout=5)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self._ffmpeg.pid), signal.SIGKILL)

        # Ferma streaming GoPro
        try:
            self._gopro.livestream("stop")
        except Exception as e:
            log.warning("Errore fermando streaming GoPro: %s", e)

        # Spegni GoPro
        try:
            self._gopro.power_off()
        except Exception as e:
            log.warning("Errore spegnendo GoPro: %s", e)

        log.info("Tutto fermato.")

    @property
    def is_running(self) -> bool:
        return self._ffmpeg is not None and self._ffmpeg.poll() is None


# ─── Main ────────────────────────────────────────────────────

def main() -> None:
    stream = GoProStream()
    try:
        stream.start_stream()
        # Mantieni il processo vivo
        while stream.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Interruzione ricevuta")
    finally:
        stream.stop_stream()


if __name__ == "__main__":
    main()
