#!/usr/bin/env python3
"""GoPro Photo.

Scatta una foto e la scarica dalla GoPro Hero 4.
"""

import logging
import os
import sys

from goprocam import GoProCamera
from goprocam import constants

# ─── Configurazione ──────────────────────────────────────────

GOPRO_IP: str = os.getenv("GOPRO_IP", "10.5.5.9")

# ─── Logging ──────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("goprophoto")


# ─── Photo ───────────────────────────────────────────────────

class GoProPhoto:
    """Scatto foto remoto e download dalla GoPro."""

    def __init__(self) -> None:
        log.info("Connessione alla GoPro (%s)...", GOPRO_IP)
        self._gopro = GoProCamera.GoPro(GOPRO_IP)

    def take_photo(self) -> None:
        """Imposta modalità Photo, scatta e scarica l'ultima foto."""
        log.info("Impostazione modalità Photo...")
        self._gopro.mode(
            constants.Mode.PhotoMode,
            constants.Mode.SubMode.Photo.Single,
        )
        self._gopro.gpControlSet(
            constants.Photo.RESOLUTION,
            constants.Photo.Resolution.R5M,
        )

        log.info("Scatto foto...")
        photo_path = self._gopro.take_photo(0)

        log.info("Download: %s", photo_path)
        self._gopro.downloadLastMedia(photo_path)
        log.info("Foto scaricata con successo.")


# ─── Main ────────────────────────────────────────────────────

def main() -> None:
    goprophoto = GoProPhoto()
    try:
        goprophoto.take_photo()
    except KeyboardInterrupt:
        log.info("Interruzione ricevuta")
    except Exception as e:
        log.error("Errore: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
