#!/usr/bin/env python3
"""GoPro Streaming Bridge.

Riceve il flusso UDP dalla GoPro Hero 4 e lo converte in RTMP
verso Nginx-RTMP per generare lo stream HLS.

Supervisore: monitora socket RTMP e stream GoPro, auto-recovery.
"""

import json
import logging
import multiprocessing
import os
import re
import signal
import socket
import subprocess
import time
import urllib.request
import urllib.error
from typing import Optional

from goprocam import GoProCamera

# ─── Configurazione ──────────────────────────────────────────

GOPRO_IP: str = os.getenv("GOPRO_IP", "10.5.5.9")
RTMP_URL: str = os.getenv("RTMP_URL", "rtmp://localhost:1935/live/gopro")
KEEPALIVE_INTERVAL: int = int(os.getenv("KEEPALIVE_INTERVAL", "8"))
UDP_PORT: int = int(os.getenv("UDP_PORT", "8554"))
NGINX_RTMP_PORT: int = 1935

# ─── Logging ──────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("goprostream")


# ─── KeepAlive ───────────────────────────────────────────────


def _keepalive_worker(ip_addr: str) -> None:
    """Worker per il keepalive. Gira in processo separato."""
    from goprocam import GoProCamera

    gopro = GoProCamera.GoPro(ip_addr)
    log.info("KeepAlive worker avviato")
    gopro.KeepAlive()  # While True della libreria


class KeepAliveTimer:
    """Mantiene attivo il WiFi della GoPro in processo separato."""

    def __init__(self, gopro: GoProCamera.GoPro) -> None:
        self._ip_addr = gopro.ip_addr
        self._process: Optional[multiprocessing.Process] = None

    def start(self) -> None:
        """Avvia il processo KeepAlive."""
        if self._process and self._process.is_alive():
            log.warning("KeepAlive già in esecuzione")
            return

        self._process = multiprocessing.Process(
            target=_keepalive_worker,
            args=(self._ip_addr,),
            daemon=True,
            name="KeepAlive",
        )
        self._process.start()
        log.info("KeepAlive avviato (PID: %d)", self._process.pid)

    def stop(self) -> None:
        """Ferma il processo KeepAlive in modo pulito."""
        if not self._process:
            return

        if self._process.is_alive():
            log.info("Ferma KeepAlive (PID: %d)...", self._process.pid)
            self._process.terminate()  # SIGTERM
            self._process.join(timeout=3)

            if self._process.is_alive():
                log.warning("KeepAlive non risponde, kill forzato")
                self._process.kill()  # SIGKILL
                self._process.join(timeout=2)

        log.info("KeepAlive fermato")

    @property
    def is_running(self) -> bool:
        """True se il processo è attivo."""
        return self._process is not None and self._process.is_alive()

    @property
    def pid(self) -> Optional[int]:
        """PID del processo."""
        return self._process.pid if self._process else None


# ─── Health Checks ───────────────────────────────────────────


def _get_ffmpeg_socket_inodes(pid: int) -> list[str]:
    """Restituisce gli inode dei socket di un processo."""
    inodes = []
    try:
        fd_dir = f"/proc/{pid}/fd"
        for fd in os.listdir(fd_dir):
            try:
                link = os.readlink(f"{fd_dir}/{fd}")
                match = re.search(r"socket:\[(\d+)\]", link)
                if match:
                    inodes.append(match.group(1))
            except OSError:
                continue
    except OSError:
        pass
    return inodes


def _check_rtmp_socket(pid: int) -> bool:
    """Check 1: Verifica se il socket RTMP di FFmpeg è ESTABLISHED.

    Se nginx droppa il publisher, il socket entra in FIN_WAIT_2.
    Questo rileva il problema PRIMA che il buffer TCP si riempia.
    """
    try:
        inodes = _get_ffmpeg_socket_inodes(pid)
        if not inodes:
            return False

        with open(f"/proc/{pid}/net/tcp") as f:
            for line in f:
                for inode in inodes:
                    if inode in line:
                        # Campo stato è il 4 dopo "local_address remote_address"
                        parts = line.split()
                        if len(parts) >= 4:
                            state = parts[3]
                            if state == "01":  # ESTABLISHED
                                return True
                            # 06=CLOSE_WAIT, 08=FIN_WAIT_2, 07=LAST_ACK
                            return False
        return False
    except (OSError, IndexError):
        return False


def _check_gopro_streaming() -> bool:
    """Check 2: Verifica se la GoPro sta mandando dati UDP.

    Prova a ricevere un pacchetto UDP dalla GoPro.
    Se riceve dati → stream attivo.
    Se timeout → stream fermo.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.bind(("", UDP_PORT))
        data, addr = sock.recvfrom(1024)
        sock.close()
        return len(data) > 0
    except socket.timeout:
        return False
    except OSError:
        # Porta già in uso (da FFmpeg) → assume che FFmpeg stia ricevendo
        return True


def _check_udp_gopro() -> str:
    """Diagnostica: verifica se la GoPro è raggiungibile via UDP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        result = sock.connect_ex((GOPRO_IP, UDP_PORT))
        sock.close()
        if result == 0:
            return "OK"
        return f"FALLITO (errno: {result})"
    except Exception as e:
        return f"ERRORE: {e}"


def _check_gopro_status() -> str:
    """Diagnostica: verifica lo stato della GoPro via API HTTP."""
    try:
        req = urllib.request.Request(f"http://{GOPRO_IP}/gp/gpControl/status")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            status = data.get("status", {})
            wifi = status.get("3", "?")
            battery = status.get("70", "?")
            recording = status.get("50", "?")
            return f"WiFi={wifi}, battery={battery}%, REC={recording}"
    except Exception as e:
        return f"ERRORE: {e}"


def _check_hls_endpoint() -> str:
    """Diagnostica: verifica se l'endpoint HLS risponde."""
    try:
        req = urllib.request.Request("http://localhost:8080/hls/gopro.m3u8")
        with urllib.request.urlopen(req, timeout=3) as resp:
            size = len(resp.read())
            return f"HTTP {resp.status} ({size}B)"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"ERRORE: {e}"


# ─── Streaming ───────────────────────────────────────────────


class GoProStream:
    """Bridge streaming: GoPro UDP → FFmpeg → RTMP → Nginx → HLS."""

    def __init__(self) -> None:
        log.info("Connessione alla GoPro (%s)...", GOPRO_IP)
        self._gopro = GoProCamera.GoPro(GOPRO_IP)
        self._ffmpeg: Optional[subprocess.Popen[bytes]] = None
        self._keepalive: Optional[KeepAliveTimer] = None
        self._shutdown = False

    def _start_ffmpeg(self) -> None:
        """Avvia FFmpeg (o lo riavvia)."""
        # Ferma il vecchio FFmpeg se presente
        self._kill_ffmpeg()

        udp_url = f"udp://{GOPRO_IP}:{UDP_PORT}"
        cmd = (
            f"ffmpeg -y -f mpegts -i {udp_url} "
            f"-c copy -an "
            f"-f flv {RTMP_URL}"
        )
        log.info("Avvio FFmpeg: %s", cmd)

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

        log.info("FFmpeg avviato (PID: %d)", self._ffmpeg.pid)

    def _kill_ffmpeg(self) -> None:
        """Termina FFmpeg in modo pulito e raccoglie diagnostiche."""
        if not self._ffmpeg:
            return

        exit_code = self._ffmpeg.poll()
        if exit_code is None:
            # FFmpeg è ancora vivo, fallo fuori
            log.info("Chiusura FFmpeg (PID: %d)...", self._ffmpeg.pid)
            try:
                os.killpg(os.getpgid(self._ffmpeg.pid), signal.SIGTERM)
                self._ffmpeg.wait(timeout=5)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self._ffmpeg.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            exit_code = self._ffmpeg.poll()

        # Log exit code
        log.info("FFmpeg exit code: %s", exit_code)

        # Log ultime righe di stderr
        stderr = self._ffmpeg.stderr
        if stderr:
            try:
                stderr.seek(0, 2)
                size = stderr.tell()
                stderr.seek(max(0, size - 4096))
                lines = stderr.read().decode(errors="replace").strip().split("\n")
                last_lines = lines[-10:]
                if last_lines and any(l.strip() for l in last_lines):
                    log.error("FFmpeg stderr (ultime %d righe):", len(last_lines))
                    for line in last_lines:
                        if line.strip():
                            log.error("  | %s", line)
            except Exception as e:
                log.warning("Impossibile leggere stderr FFmpeg: %s", e)

        self._ffmpeg = None

    def _restart_stream_gopro(self) -> None:
        """Invia comando restart stream alla GoPro."""
        try:
            url = f"http://{GOPRO_IP}/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart"
            req = urllib.request.Request(url)
            urllib.request.urlopen(req, timeout=5)
            log.info("Restart stream GoPro inviato")
        except Exception as e:
            log.warning("Errore restart stream GoPro: %s", e)

    def start_stream(self) -> None:
        """Avvia lo streaming iniziale."""
        log.info("Avvio streaming...")
        self._gopro.livestream("start")
        time.sleep(1)
        self._start_ffmpeg()

        # Avvia KeepAlive
        self._keepalive = KeepAliveTimer(self._gopro)
        self._keepalive.start()

        log.info("Streaming attivo. Ctrl+C per fermare.")

    def stop_stream(self) -> None:
        """Ferma tutto: KeepAlive, FFmpeg, GoPro."""
        self._shutdown = True
        log.info("Ferma streaming...")

        if self._keepalive:
            self._keepalive.stop()

        self._kill_ffmpeg()

        try:
            self._gopro.livestream("stop")
        except Exception as e:
            log.warning("Errore fermando streaming GoPro: %s", e)

        try:
            self._gopro.power_off()
        except Exception as e:
            log.warning("Errore spegnendo GoPro: %s", e)

        log.info("Tutto fermato.")

    @property
    def is_running(self) -> bool:
        return self._ffmpeg is not None and self._ffmpeg.poll() is None


# ─── Supervisore ─────────────────────────────────────────────


def _supervisor(stream: GoProStream) -> None:
    """Loop principale: monitora e auto-recovery."""
    start_time = time.monotonic()
    last_check = 0

    while not stream._shutdown:
        time.sleep(1)
        elapsed = int(time.monotonic() - start_time)

        # Heartbeat ogni 60s
        if elapsed > 0 and elapsed % 60 == 0 and elapsed != last_check:
            pid = stream._ffmpeg.pid if stream._ffmpeg else "?"
            log.info("Supervisore: vivo da %ds (FFmpeg PID: %s)", elapsed, pid)
            last_check = elapsed

        # Health check ogni 30s
        if elapsed > 0 and elapsed % 30 == 0 and elapsed != last_check:
            last_check = elapsed
            _run_health_checks(stream)

        # Se FFmpeg è morto → restart
        if stream._ffmpeg and stream._ffmpeg.poll() is not None:
            log.warning("FFmpeg è morto (exit code: %s) → restart", stream._ffmpeg.poll())
            stream._kill_ffmpeg()
            time.sleep(2)
            try:
                stream._start_ffmpeg()
            except RuntimeError as e:
                log.error("Impossibile riavviare FFmpeg: %s", e)
                time.sleep(5)


def _run_health_checks(stream: GoProStream) -> None:
    """Esegue gli health check e agisce di conseguenza."""
    results = []

    # Check 1: Socket RTMP
    if stream._ffmpeg and stream._ffmpeg.poll() is None:
        socket_ok = _check_rtmp_socket(stream._ffmpeg.pid)
        results.append(f"socket={'OK' if socket_ok else 'MORTO'}")

        if not socket_ok:
            log.warning("Supervisore: socket RTMP non ESTABLISHED → kill FFmpeg")
            stream._kill_ffmpeg()
            time.sleep(2)
            try:
                stream._start_ffmpeg()
                results.append("restart=OK")
            except RuntimeError as e:
                log.error("Restart FFmpeg fallito: %s", e)
                results.append("restart=FALLITO")
            return  # skip altri check, FFmpeg è stato riavviato
    else:
        results.append("socket=N/A")

    # Check 2: GoPro streaming
    gopro_streaming = _check_gopro_streaming()
    results.append(f"gopro={'streaming' if gopro_streaming else 'fermo'}")

    if not gopro_streaming:
        log.warning("Supervisore: GoPro non sta streammando → restart stream")
        stream._restart_stream_gopro()
        time.sleep(3)

    # Diagnostica: HLS endpoint
    hls = _check_hls_endpoint()
    results.append(f"hls={hls}")

    log.info("Supervisore: %s", " | ".join(results))


# ─── Main ────────────────────────────────────────────────────


def main() -> None:
    stream = GoProStream()
    try:
        stream.start_stream()
        _supervisor(stream)
    except KeyboardInterrupt:
        log.info("Interruzione ricevuta")
    finally:
        stream.stop_stream()


if __name__ == "__main__":
    main()
