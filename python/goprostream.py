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

# Auto-recovery GoPro
MAX_GOPRO_RETRIES: int = int(os.getenv("MAX_GOPRO_RETRIES", "30"))  # 30 × 10s = 5 min
GOPRO_CHECK_INTERVAL: int = int(os.getenv("GOPRO_CHECK_INTERVAL", "10"))  # secondi
WARNING_FILE: str = os.getenv("WARNING_FILE", "/mnt/hls/warning.json")

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

# Stati TCP per il check socket RTMP
KILL_STATES = {"06", "07"}  # CLOSE_WAIT, LAST_ACK — connessione morta
TRANSIENT_STATES = {"02", "03", "04", "08"}  # SYN_*, FIN_WAIT_* — transitorio

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


def _check_rtmp_socket(pid: int) -> str:
    """Check 1: Verifica lo stato del socket RTMP di FFmpeg.

    Return:
        'ESTABLISHED' — connessione attiva
        'TRANSIENT' — stato transitorio (SYN_SENT, FIN_WAIT_*)
        'DEAD' — connessione morta (CLOSE_WAIT, LAST_ACK)
        'UNKNOWN' — stato sconosciuto
        'NOSOCKET' — nessun socket trovato
    """
    try:
        inodes = _get_ffmpeg_socket_inodes(pid)
        if not inodes:
            return "NOSOCKET"

        with open(f"/proc/{pid}/net/tcp") as f:
            for line in f:
                for inode in inodes:
                    if inode in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            state = parts[3]
                            if state == "01":  # ESTABLISHED
                                return "ESTABLISHED"
                            elif state in KILL_STATES:
                                return "DEAD"
                            elif state in TRANSIENT_STATES:
                                return "TRANSIENT"
                            else:
                                return "UNKNOWN"
        return "NOSOCKET"
    except (OSError, IndexError):
        return "NOSOCKET"


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


def _check_gopro_online() -> bool:
    """Verifica se la GoPro è raggiungibile via HTTP."""
    try:
        req = urllib.request.Request(f"http://{GOPRO_IP}/gp/gpControl/status")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _check_gopro_streaming_status() -> bool:
    """Verifica se la GoPro è in modalità streaming (status.17=1)."""
    try:
        req = urllib.request.Request(f"http://{GOPRO_IP}/gp/gpControl/status")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            status = data.get("status", {})
            return str(status.get("17")) == "1"  # 1 = multistream attivo
    except Exception:
        return False


def _send_dashboard_warning(message: str) -> None:
    """Invia warning alla dashboard via file di stato."""
    data = {
        "timestamp": time.time(),
        "message": message,
        "level": "warning"
    }
    try:
        with open(WARNING_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        log.warning("Impossibile scrivere warning: %s", e)


def _clear_dashboard_warning() -> None:
    """Rimuove il warning dalla dashboard."""
    try:
        if os.path.exists(WARNING_FILE):
            os.remove(WARNING_FILE)
    except Exception:
        pass


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
        cmd = [
            "ffmpeg", "-y",
            "-f", "mpegts",
            "-i", udp_url,
            "-c", "copy",
            "-an",
            "-f", "flv",
            RTMP_URL,
        ]
        log.info("Avvio FFmpeg: %s", " ".join(cmd))

        self._ffmpeg = subprocess.Popen(
            cmd,
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
                self._ffmpeg.wait()
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
    transient_count = [0]  # lista mutabile per contatore transitori
    nosocket_count = [0]  # lista mutabile per contatore NOSOCKET
    gopro_retry_count = 0
    waiting_for_gopro = False

    while not stream._shutdown:
        time.sleep(1)
        elapsed = int(time.monotonic() - start_time)

        # Stato WAITING_FOR_GOPRO: attendi che la GoPro torni online
        if waiting_for_gopro:
            if elapsed > 0 and elapsed % GOPRO_CHECK_INTERVAL == 0 and elapsed != last_check:
                last_check = elapsed

                if _check_gopro_online():
                    log.info("GoPro tornata online dopo %d tentativi", gopro_retry_count)
                    _clear_dashboard_warning()
                    waiting_for_gopro = False
                    gopro_retry_count = 0
                    # Continua con il riavvio FFmpeg sotto
                else:
                    gopro_retry_count += 1
                    if gopro_retry_count >= MAX_GOPRO_RETRIES:
                        msg = f"GoPro offline da {MAX_GOPRO_RETRIES * GOPRO_CHECK_INTERVAL}s"
                        log.warning(msg)
                        _send_dashboard_warning(msg)
                        gopro_retry_count = 0  # reset, riprova
                    else:
                        log.info("GoPro offline (%d/%d), attesa...", gopro_retry_count, MAX_GOPRO_RETRIES)
                    continue  # salta il resto del loop, riprova dopo

        # Heartbeat ogni 60s
        if elapsed > 0 and elapsed % 60 == 0 and elapsed != last_check:
            pid = stream._ffmpeg.pid if stream._ffmpeg else "?"
            log.info("Supervisore: vivo da %ds (FFmpeg PID: %s)", elapsed, pid)
            last_check = elapsed

        # Health check ogni 10s (più frequente per transitori)
        if elapsed > 0 and elapsed % 10 == 0 and elapsed != last_check:
            last_check = elapsed
            _run_health_checks(stream, transient_count, nosocket_count)

        # Check KeepAlive
        if stream._keepalive and not stream._keepalive.is_running:
            log.warning("KeepAlive morto → restart")
            stream._keepalive.start()

        # Se FFmpeg è morto → restart con check GoPro
        if stream._ffmpeg and stream._ffmpeg.poll() is not None:
            log.warning("FFmpeg è morto (exit code: %s) → restart", stream._ffmpeg.poll())
            stream._kill_ffmpeg()

            # Check GoPro prima di riavviare FFmpeg
            if not _check_gopro_online():
                log.warning("GoPro non raggiungibile → attesa...")
                waiting_for_gopro = True
                gopro_retry_count = 0
                continue

            time.sleep(2)
            try:
                stream._start_ffmpeg()
                # Dopo FFmpeg, verifica se serve restart streaming
                if not _check_gopro_streaming_status():
                    log.info("GoPro non in streaming → invio restart")
                    stream._restart_stream_gopro()
            except RuntimeError as e:
                log.error("Impossibile riavviare FFmpeg: %s", e)
                time.sleep(5)


def _run_health_checks(stream: GoProStream, transient_count: list[int], nosocket_count: list[int]) -> None:
    """Esegue gli health check e agisce di conseguenza.

    Args:
        stream: oggetto GoProStream
        transient_count: lista con un solo intero (contatore transitori, mutabile)
        nosocket_count: lista con un solo intero (contatore NOSOCKET, mutabile)
    """
    results = []

    # Check 1: Socket RTMP
    if stream._ffmpeg and stream._ffmpeg.poll() is None:
        socket_status = _check_rtmp_socket(stream._ffmpeg.pid)
        results.append(f"socket={socket_status}")

        # Gestione NOSOCKET: se FFmpeg è vivo ma non ha socket RTMP
        # potrebbe non ricevere dati UDP dalla GoPro
        if socket_status == "NOSOCKET":
            nosocket_count[0] += 1
            if nosocket_count[0] >= 3:  # 30 secondi senza socket
                log.warning("Supervisore: NOSOCKET da 30s → GoPro potrebbe non streammare, invio restart")
                stream._restart_stream_gopro()
                nosocket_count[0] = 0
                time.sleep(3)  # aspetta che la GoPro riavvii lo streaming
        else:
            # Qualsiasi altro stato resetta il contatore
            nosocket_count[0] = 0

        if socket_status == "DEAD":
            log.warning("Supervisore: socket RTMP morto (CLOSE_WAIT/LAST_ACK) → kill FFmpeg")
            stream._kill_ffmpeg()

            # Check GoPro prima di riavviare
            if not _check_gopro_online():
                log.warning("GoPro non raggiungibile dopo DEAD socket → attesa")
                return  # il supervisore gestirà WAITING_FOR_GOPRO

            time.sleep(2)
            try:
                stream._start_ffmpeg()
                # Verifica se serve restart streaming
                if not _check_gopro_streaming_status():
                    log.info("GoPro non in streaming → invio restart")
                    stream._restart_stream_gopro()
                results.append("restart=OK")
            except RuntimeError as e:
                log.error("Restart FFmpeg fallito: %s", e)
                results.append("restart=FALLITO")
            return  # skip altri check, FFmpeg è stato riavviato

        elif socket_status == "TRANSIENT":
            transient_count[0] += 1
            if transient_count[0] >= 3:
                log.warning("Supervisore: socket RTMP in stato transitorio da 30s → kill FFmpeg")
                stream._kill_ffmpeg()

                # Check GoPro prima di riavviare
                if not _check_gopro_online():
                    log.warning("GoPro non raggiungibile dopo TRANSIENT → attesa")
                    return  # il supervisore gestirà WAITING_FOR_GOPRO

                time.sleep(2)
                try:
                    stream._start_ffmpeg()
                    # Verifica se serve restart streaming
                    if not _check_gopro_streaming_status():
                        log.info("GoPro non in streaming → invio restart")
                        stream._restart_stream_gopro()
                    results.append("restart=OK")
                except RuntimeError as e:
                    log.error("Restart FFmpeg fallito: %s", e)
                    results.append("restart=FALLITO")
                transient_count[0] = 0
                return
            else:
                log.info("Supervisore: socket transitorio (%d/3) → aspetto", transient_count[0])

        elif socket_status == "UNKNOWN":
            log.warning("Supervisore: socket RTMP stato sconosciuto: %s", socket_status)

        else:
            # ESTABLISHED o NOSOCKET con processo vivo → reset contatore
            transient_count[0] = 0
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
