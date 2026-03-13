from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from whisper_stt.app import App
from whisper_stt.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper Local STT")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config file (default: config.toml next to start.bat)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Resolve config path relative to the project root (where start.bat lives)
    if args.config is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        args.config = project_root / "config.toml"

    # Log to file (essential when running via pythonw which has no console)
    log_file = args.config.parent / "whisper_stt.log"
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            *([] if sys.stderr is None else [logging.StreamHandler()]),
        ],
    )

    config = load_config(args.config)
    app = App(config, config_path=args.config)
    app.run()


if __name__ == "__main__":
    main()
