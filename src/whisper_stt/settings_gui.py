from __future__ import annotations

import dataclasses
import logging
import threading
import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from pathlib import Path

from whisper_stt.config import Config, save_config

logger = logging.getLogger(__name__)

_window_open = False

# Dark theme colors
_BG = "#1e1e1e"
_BG_FRAME = "#2d2d2d"
_BG_INPUT = "#3c3c3c"
_FG = "#f0f0f0"
_FG_DIM = "#999999"
_FG_ACCENT = "#6cb6ff"
_BORDER = "#555555"

# Display metadata for settings fields
_FIELD_META: dict[str, dict] = {
    "hotkey": {
        "label": "Hotkey",
        "widget": "entry",
        "help": "e.g. ralt, f9, ctrl+shift+space",
    },
    "mode": {
        "label": "Mode",
        "widget": "combo",
        "values": ["push_to_talk", "toggle"],
    },
    "model_size": {
        "label": "Model",
        "widget": "combo",
        "values": ["large-v3-turbo"],
        "restart": True,
    },
    "language": {
        "label": "Language",
        "widget": "combo",
        "values": ["ja", "en", "zh", "ko", "de", "fr", "es", "auto"],
    },
    "beam_size": {
        "label": "Beam Size",
        "widget": "spin",
        "from": 1,
        "to": 10,
    },
    "device": {
        "label": "Device",
        "widget": "combo",
        "values": ["cuda", "cpu"],
        "restart": True,
    },
    "compute_type": {
        "label": "Compute Type",
        "widget": "combo",
        "values": ["float16", "int8", "float32"],
        "restart": True,
    },
    "play_sound": {
        "label": "Sound Feedback",
        "widget": "check",
    },
    "vad_filter": {
        "label": "VAD Filter",
        "widget": "check",
    },
}

# Group definitions
_GROUPS: list[tuple[str, list[str]]] = [
    ("Hotkey", ["hotkey", "mode"]),
    ("Whisper", ["model_size", "language", "beam_size"]),
    ("Performance", ["device", "compute_type"]),
    ("Behavior", ["play_sound", "vad_filter"]),
]


def _apply_dark_titlebar(root: tk.Tk) -> None:
    """Use Windows DWM API to set the title bar to dark mode."""
    try:
        import ctypes
        root.update()  # ensure HWND exists
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass  # fail silently on unsupported OS versions


def _apply_dark_theme(root: tk.Tk) -> None:
    """Apply a dark color scheme using tk and ttk styling."""
    root.configure(bg=_BG)
    _apply_dark_titlebar(root)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=_BG, foreground=_FG,
                    fieldbackground=_BG_INPUT, borderwidth=1,
                    font=("Segoe UI", 11))

    style.configure("TFrame", background=_BG)
    style.configure("TLabel", background=_BG, foreground=_FG,
                    font=("Segoe UI", 11))
    style.configure("Dim.TLabel", background=_BG, foreground=_FG_DIM,
                    font=("Segoe UI", 9))
    style.configure("Help.TLabel", background=_BG, foreground=_FG_DIM,
                    font=("Segoe UI", 9))

    style.configure("TLabelframe", background=_BG, foreground=_FG_ACCENT,
                    bordercolor=_BORDER)
    style.configure("TLabelframe.Label", background=_BG, foreground=_FG_ACCENT,
                    font=("Segoe UI", 11, "bold"))

    _input_font = ("Segoe UI Semibold", 12)

    style.configure("TEntry", fieldbackground=_BG_INPUT, foreground=_FG,
                    insertcolor=_FG, bordercolor=_BG_FRAME, borderwidth=0,
                    lightcolor=_BG_FRAME, darkcolor=_BG_FRAME,
                    font=_input_font, padding=(4, 4))

    style.configure("TCombobox", fieldbackground=_BG_INPUT, foreground=_FG,
                    background=_BG_FRAME, bordercolor=_BG_FRAME, borderwidth=0,
                    lightcolor=_BG_FRAME, darkcolor=_BG_FRAME,
                    arrowcolor=_FG, arrowsize=16,
                    font=_input_font, padding=(4, 4))
    style.map("TCombobox",
              fieldbackground=[("readonly", _BG_INPUT)],
              foreground=[("readonly", _FG)],
              selectbackground=[("readonly", _FG_ACCENT)],
              selectforeground=[("readonly", "#ffffff")])
    root.option_add("*TCombobox*Listbox.background", _BG_INPUT)
    root.option_add("*TCombobox*Listbox.foreground", _FG)
    root.option_add("*TCombobox*Listbox.font", _input_font)
    root.option_add("*TCombobox*Listbox.selectBackground", _FG_ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    style.configure("TSpinbox", fieldbackground=_BG_INPUT, foreground=_FG,
                    background=_BG_FRAME, bordercolor=_BG_FRAME, borderwidth=0,
                    lightcolor=_BG_FRAME, darkcolor=_BG_FRAME,
                    arrowcolor=_FG, arrowsize=16,
                    font=_input_font, padding=(4, 4))

    # Custom checkbox images (checkmark instead of X)
    from PIL import Image, ImageDraw, ImageTk
    size = 20

    # Unchecked: dark rounded box
    img_off = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_off)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=3,
                        fill=_BG_INPUT, outline=_BORDER)
    _cb_off = ImageTk.PhotoImage(img_off)

    # Checked: accent rounded box with checkmark
    img_on = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_on)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=3,
                        fill=_FG_ACCENT, outline=_FG_ACCENT)
    d.line([(4, 10), (8, 15), (15, 4)], fill="#ffffff", width=2)
    _cb_on = ImageTk.PhotoImage(img_on)

    # Keep references so images aren't garbage collected
    root._cb_images = (_cb_off, _cb_on)  # type: ignore[attr-defined]

    style.element_create("custom_check", "image", _cb_off,
                         ("selected", _cb_on))
    style.layout("TCheckbutton", [
        ("Checkbutton.padding", {"children": [
            ("custom_check", {"side": "left", "sticky": ""}),
            ("Checkbutton.label", {"side": "left", "sticky": ""}),
        ], "sticky": "nswe"}),
    ])
    style.configure("TCheckbutton", background=_BG, foreground=_FG)
    style.map("TCheckbutton",
              background=[("active", _BG_FRAME)])

    style.configure("TButton", background=_BG_FRAME, foreground=_FG,
                    bordercolor=_BORDER, font=("Segoe UI", 11),
                    padding=(16, 6))
    style.map("TButton",
              background=[("active", _FG_ACCENT)],
              foreground=[("active", "#ffffff")])

    style.configure("Accent.TButton", background=_FG_ACCENT, foreground="#ffffff",
                    bordercolor=_FG_ACCENT, font=("Segoe UI", 11, "bold"),
                    padding=(16, 6))
    style.map("Accent.TButton",
              background=[("active", "#4a8abf")])


class SettingsWindow:
    def __init__(
        self,
        root: tk.Tk,
        config: Config,
        config_path: Path,
        on_save: Callable[[Config], None],
    ) -> None:
        self._root = root
        self._config = config
        self._config_path = config_path
        self._on_save = on_save
        self._vars: dict[str, tk.Variable] = {}

        _apply_dark_theme(root)
        self._build_ui()

    def _build_ui(self) -> None:
        root = self._root
        root.title("Whisper STT - Settings")
        root.resizable(False, False)

        # Bring to front
        root.lift()
        root.attributes("-topmost", True)
        root.after(100, lambda: root.attributes("-topmost", False))

        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        for group_name, fields in _GROUPS:
            frame = ttk.LabelFrame(main, text=group_name, padding=10)
            frame.pack(fill="x", pady=(0, 8))

            for field_name in fields:
                meta = _FIELD_META[field_name]
                current_val = getattr(self._config, field_name)

                row = ttk.Frame(frame)
                row.pack(fill="x", pady=3)

                label_text = meta["label"]
                if meta.get("restart"):
                    label_text += " *"
                ttk.Label(row, text=label_text, width=18, anchor="w").pack(side="left")

                widget_type = meta["widget"]

                if widget_type == "entry":
                    var = tk.StringVar(value=str(current_val))
                    ttk.Entry(row, textvariable=var, width=25).pack(side="left", fill="x", expand=True)

                elif widget_type == "combo":
                    var = tk.StringVar(value=str(current_val))
                    combo = ttk.Combobox(row, textvariable=var, values=meta["values"],
                                         state="readonly", width=22)
                    combo.pack(side="left")
                    if str(current_val) not in meta["values"]:
                        combo.config(state="normal")
                        combo.set(str(current_val))

                elif widget_type == "spin":
                    var = tk.IntVar(value=int(current_val))
                    ttk.Spinbox(row, textvariable=var, from_=meta["from"],
                                to=meta["to"], width=8).pack(side="left")

                elif widget_type == "check":
                    var = tk.BooleanVar(value=bool(current_val))
                    ttk.Checkbutton(row, variable=var).pack(side="left")

                if meta.get("help"):
                    ttk.Label(row, text=meta["help"], style="Help.TLabel").pack(side="left", padx=(8, 0))

                self._vars[field_name] = var

        # Note about restart
        ttk.Label(main, text="* requires model reload", style="Dim.TLabel").pack(anchor="w", pady=(0, 6))

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(4, 0))

        ttk.Button(btn_frame, text="Save", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Cancel",
                   command=self._root.destroy).pack(side="right")

    def _save(self) -> None:
        values: dict[str, object] = {}
        for field in dataclasses.fields(Config):
            if field.name in self._vars:
                var = self._vars[field.name]
                values[field.name] = var.get()
            else:
                values[field.name] = getattr(self._config, field.name)

        try:
            new_config = Config(**values)
        except Exception:
            logger.exception("Invalid config values")
            return

        save_config(new_config, self._config_path)
        logger.info("Config saved to %s", self._config_path)

        self._on_save(new_config)
        self._root.destroy()


def open_settings_window(
    config: Config,
    config_path: Path,
    on_save: Callable[[Config], None],
) -> None:
    """Open the settings GUI on a new thread."""
    global _window_open
    if _window_open:
        return
    _window_open = True

    def _run() -> None:
        global _window_open
        try:
            root = tk.Tk()
            root.protocol("WM_DELETE_WINDOW", root.destroy)
            SettingsWindow(root, config, config_path, on_save)
            root.mainloop()
        finally:
            _window_open = False

    threading.Thread(target=_run, daemon=True).start()
