from __future__ import annotations

import ctypes
import logging
import threading
import time
from collections.abc import Callable

from whisper_stt.config import Config

logger = logging.getLogger(__name__)

_user32 = ctypes.windll.user32
_user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
_user32.GetAsyncKeyState.restype = ctypes.c_short

# Virtual key codes
_VK_MAP: dict[str, int] = {
    "ctrl": 0x11, "control": 0x11,
    "lctrl": 0xA2, "rctrl": 0xA3,
    "shift": 0x10,
    "lshift": 0xA0, "rshift": 0xA1,
    "alt": 0x12, "menu": 0x12,
    "lalt": 0xA4, "ralt": 0xA5,
    "space": 0x20,
    "tab": 0x09,
    "enter": 0x0D, "return": 0x0D,
    "esc": 0x1B, "escape": 0x1B,
    **{f"f{i}": 0x70 + i - 1 for i in range(1, 13)},
    **{chr(c): c for c in range(0x30, 0x3A)},
    **{chr(c).lower(): c for c in range(0x41, 0x5B)},
}

POLL_INTERVAL = 0.015  # 15ms

# Alt VK codes — need special handling to suppress menu activation
_ALT_VKS = {0x12, 0xA4, 0xA5}  # VK_MENU, VK_LMENU, VK_RMENU

KEYEVENTF_KEYUP = 0x0002


class HotkeyManager:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._thread: threading.Thread | None = None
        self._running = False

    def register(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        if self._running:
            logger.debug("Hotkey already registered, skipping")
            return

        hotkey = self._config.hotkey.strip().lower()
        vk = _VK_MAP.get(hotkey)
        if vk is None and "+" in hotkey:
            keys = [k.strip().lower() for k in hotkey.split("+")]
            vk = _VK_MAP.get(keys[-1])
        if vk is None:
            raise ValueError(f"Unknown key: {hotkey!r}")

        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            args=(vk, on_press, on_release),
            daemon=True,
        )
        self._thread.start()

    def _poll_loop(
        self,
        vk: int,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        active = False
        logger.info(
            "GetAsyncKeyState polling started for VK=0x%x (interval=%.0fms, no hooks, AHK-safe)",
            vk, POLL_INTERVAL * 1000,
        )

        while self._running:
            state = _user32.GetAsyncKeyState(vk)
            key_down = bool(state & 0x8000)

            if key_down and not active:
                active = True
                if vk in _ALT_VKS:
                    # Inject a dummy key to prevent Alt from activating the menu bar
                    _user32.keybd_event(0xFF, 0, 0, 0)
                    _user32.keybd_event(0xFF, 0, KEYEVENTF_KEYUP, 0)
                logger.debug("Poll: key down (vk=0x%x)", vk)
                threading.Thread(target=on_press, daemon=True).start()
            elif not key_down and active:
                active = False
                logger.debug("Poll: key up (vk=0x%x)", vk)
                threading.Thread(target=on_release, daemon=True).start()

            time.sleep(POLL_INTERVAL)

        logger.info("GetAsyncKeyState polling stopped")

    def unregister(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
