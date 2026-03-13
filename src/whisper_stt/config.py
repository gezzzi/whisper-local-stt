from __future__ import annotations

import dataclasses
import tomllib
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Config:
    # Audio
    sample_rate: int = 16000
    channels: int = 1

    # Whisper
    model_size: str = "large-v3-turbo"
    device: str = "cuda"
    compute_type: str = "float16"
    beam_size: int = 3
    language: str = "ja"
    vad_filter: bool = True
    condition_on_previous_text: bool = False

    # Hotkey
    hotkey: str = "ralt"
    mode: str = "push_to_talk"

    # Behavior
    play_sound: bool = True
    preload_model: bool = True


# Fields exposed in the settings GUI (order matters for display)
GUI_FIELDS: list[str] = [
    "hotkey", "mode",
    "model_size", "language", "beam_size",
    "device", "compute_type",
    "play_sound", "vad_filter",
]


def load_config(path: Path | None = None) -> Config:
    if path is None:
        path = Path("config.toml")
    if not path.exists():
        return Config()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    # Only pass keys that Config knows about
    valid_keys = {field.name for field in dataclasses.fields(Config)}
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    return Config(**filtered)


def save_config(config: Config, path: Path) -> None:
    """Write config values to a TOML file."""
    lines: list[str] = []
    for field in dataclasses.fields(Config):
        val = getattr(config, field.name)
        if isinstance(val, bool):
            lines.append(f"{field.name} = {str(val).lower()}")
        elif isinstance(val, int):
            lines.append(f"{field.name} = {val}")
        elif isinstance(val, str):
            lines.append(f'{field.name} = "{val}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
