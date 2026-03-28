from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging

logger = logging.getLogger(__name__)

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

WM_CHAR = 0x0102
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

# Console window class names
_CONSOLE_CLASSES = {
    "ConsoleWindowClass",       # cmd.exe / legacy console
    "CASCADIA_HOSTING_WINDOW_CLASS",  # Windows Terminal
    "PseudoConsoleWindow",      # ConPTY
}

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

_user32.GetClassNameW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int,
]
_user32.GetClassNameW.restype = ctypes.c_int

_user32.SendInput.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_int]
_user32.SendInput.restype = ctypes.c_uint


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]
    _anonymous_ = ("_u",)
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("_u", _U),
    ]


def _is_console_window(hwnd: int) -> bool:
    """Check if the window is a console/terminal window."""
    buf = ctypes.create_unicode_buffer(256)
    _user32.GetClassNameW(hwnd, buf, 256)
    class_name = buf.value
    logger.debug("Window class: %s", class_name)
    return class_name in _CONSOLE_CLASSES


def _inject_send_input(text: str) -> None:
    """Inject text using SendInput with KEYEVENTF_UNICODE (for console windows)."""
    inputs = []
    for char in text:
        code = ord(char)
        # Key down
        ki_down = _KEYBDINPUT(
            wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE,
            time=0, dwExtraInfo=None,
        )
        inp_down = _INPUT(type=INPUT_KEYBOARD)
        inp_down.ki = ki_down
        inputs.append(inp_down)
        # Key up
        ki_up = _KEYBDINPUT(
            wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
            time=0, dwExtraInfo=None,
        )
        inp_up = _INPUT(type=INPUT_KEYBOARD)
        inp_up.ki = ki_up
        inputs.append(inp_up)

    arr = (_INPUT * len(inputs))(*inputs)
    sent = _user32.SendInput(len(inputs), arr, ctypes.sizeof(_INPUT))
    logger.debug("SendInput: sent %d/%d events", sent, len(inputs))


def inject_text(text: str) -> None:
    """Inject text into the active window.

    Uses WM_CHAR for GUI windows (bypasses IME) and falls back to
    SendInput for console/terminal windows.
    """
    if not text:
        return

    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        logger.warning("No foreground window found")
        return

    # Console windows don't respond to WM_CHAR, use SendInput instead
    if _is_console_window(hwnd):
        logger.debug("Injecting text via SendInput (console): %s", text)
        _inject_send_input(text)
        return

    logger.debug("Injecting text via WM_CHAR: %s", text)

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
