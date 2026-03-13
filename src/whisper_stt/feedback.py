from __future__ import annotations

import threading
import winsound


def beep_start() -> None:
    """Short high beep to indicate recording started."""
    threading.Thread(
        target=lambda: winsound.Beep(1000, 150),
        daemon=True,
    ).start()


def beep_done() -> None:
    """Two short beeps to indicate transcription complete."""
    def _play() -> None:
        winsound.Beep(1200, 100)
        winsound.Beep(1500, 100)
    threading.Thread(target=_play, daemon=True).start()


def beep_error() -> None:
    """Low beep to indicate an error."""
    threading.Thread(
        target=lambda: winsound.Beep(400, 300),
        daemon=True,
    ).start()
