from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pystray
from PIL import Image


class TrayIcon:
    def __init__(self, on_quit: Callable[[], None], on_settings: Callable[[], None] | None = None) -> None:
        self._on_quit = on_quit
        self._on_settings = on_settings
        self._status = "Starting..."
        assets = Path(__file__).resolve().parent.parent.parent / "assets"
        self._icon_idle = self._load_icon(assets / "icon.png")
        self._icon_recording = self._load_icon(assets / "icon_recording.png")
        self._tray: pystray.Icon | None = None

    def _load_icon(self, path: Path) -> Image.Image:
        if path.exists():
            return Image.open(path)
        # Fallback: generate a simple colored icon
        img = Image.new("RGB", (64, 64), "gray" if "recording" not in str(path) else "red")
        return img

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(self._status, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Settings...",
                lambda icon, item: self._on_settings() if self._on_settings else None,
                default=True,
            ),
            pystray.MenuItem("Quit", lambda icon, item: self._quit()),
        )

    def _quit(self) -> None:
        self._on_quit()
        if self._tray:
            self._tray.stop()

    def set_status(self, status: str) -> None:
        self._status = status
        if self._tray:
            self._tray.menu = self._build_menu()
            self._tray.update_menu()

    def set_recording(self, recording: bool) -> None:
        if self._tray:
            self._tray.icon = self._icon_recording if recording else self._icon_idle

    def run(self) -> None:
        self._tray = pystray.Icon(
            name="whisper-stt",
            icon=self._icon_idle,
            title="Whisper STT",
            menu=self._build_menu(),
        )
        self._tray.run()
