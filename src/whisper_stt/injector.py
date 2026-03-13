from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging

logger = logging.getLogger(__name__)

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

WM_CHAR = 0x0102

_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = ctypes.wintypes.HWND

_user32.GetWindowThreadProcessId.argtypes = [
    ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD),
]
_user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD

_user32.AttachThreadInput.argtypes = [
    ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.wintypes.BOOL,
]
_user32.AttachThreadInput.restype = ctypes.wintypes.BOOL

_user32.GetFocus.argtypes = []
_user32.GetFocus.restype = ctypes.wintypes.HWND

_user32.PostMessageW.argtypes = [
    ctypes.wintypes.HWND, ctypes.c_uint,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
_user32.PostMessageW.restype = ctypes.wintypes.BOOL


def inject_text(text: str) -> None:
    """Inject text into the active window using WM_CHAR messages.

    Posts WM_CHAR directly to the focused window, completely bypassing
    the IME input pipeline. This avoids conversion candidates and
    doesn't interfere with AutoHotKey.
    """
    if not text:
        return

    logger.debug("Injecting text via WM_CHAR: %s", text)

    # Get the foreground window and its focused child control
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        logger.warning("No foreground window found")
        return

    target_thread = _user32.GetWindowThreadProcessId(hwnd, None)
    current_thread = _kernel32.GetCurrentThreadId()

    # Attach to target thread to get the focused control
    attached = _user32.AttachThreadInput(current_thread, target_thread, True)
    focus_hwnd = _user32.GetFocus() or hwnd
    if attached:
        _user32.AttachThreadInput(current_thread, target_thread, False)

    logger.debug("Target: hwnd=0x%x, focus=0x%x", hwnd or 0, focus_hwnd or 0)

    # Post WM_CHAR for each character (bypasses IME completely)
    count = 0
    for char in text:
        code = ord(char)
        if _user32.PostMessageW(focus_hwnd, WM_CHAR, code, 0):
            count += 1
        else:
            logger.warning("PostMessageW failed for char U+%04X (error=%d)",
                           code, ctypes.GetLastError())

    logger.debug("Posted %d/%d WM_CHAR messages", count, len(text))
