from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from whisper_stt import feedback
from whisper_stt.audio import AudioRecorder
from whisper_stt.config import Config
from whisper_stt.hotkey import HotkeyManager
from whisper_stt.injector import inject_text
from whisper_stt.transcriber import Transcriber
from whisper_stt.tray import TrayIcon

logger = logging.getLogger(__name__)


class App:
    def __init__(self, config: Config, config_path: Path | None = None) -> None:
        self._config = config
        self._config_path = config_path
        self._audio = AudioRecorder(config)
        self._transcriber = Transcriber(config)
        self._hotkey = HotkeyManager(config)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._injecting = False
        self._tray = TrayIcon(on_quit=self._shutdown, on_settings=self._open_settings)

    def run(self) -> None:
        # Load model in background
        self._tray.set_status("Loading model...")
        if self._config.preload_model:
            future = self._executor.submit(self._load_model)
            future.add_done_callback(self._on_model_loaded)
        else:
            self._tray.set_status("Ready (model not preloaded)")
            self._hotkey.register(self._on_press, self._on_release)

        # Block on tray event loop (main thread)
        self._tray.run()

    def _load_model(self) -> None:
        logger.info("Loading whisper model: %s", self._config.model_size)
        self._transcriber.load()
        logger.info("Model loaded successfully")

    def _on_model_loaded(self, future: object) -> None:
        try:
            # Re-raise any exception from model loading
            future.result()  # type: ignore[union-attr]
            self._tray.set_status("Ready")
            self._hotkey.register(self._on_press, self._on_release)
            logger.info("Hotkey registered: %s", self._config.hotkey)
        except Exception:
            logger.exception("Failed to load model")
            self._tray.set_status("Error: model load failed")
            if self._config.play_sound:
                feedback.beep_error()

    def _on_press(self) -> None:
        if self._injecting or self._audio.is_recording:
            return
        if not self._transcriber.is_loaded:
            logger.info("Hotkey pressed but model not ready yet")
            if self._config.play_sound:
                feedback.beep_error()
            return
        self._audio.start()
        self._tray.set_recording(True)
        self._tray.set_status("Recording...")
        if self._config.play_sound:
            feedback.beep_start()
        logger.info("Recording started")

    def _on_release(self) -> None:
        if not self._audio.is_recording:
            return
        audio = self._audio.stop()
        self._tray.set_recording(False)
        self._tray.set_status("Transcribing...")
        logger.info("Recording stopped, submitting transcription (%.1f sec)", audio.size / self._config.sample_rate)
        self._executor.submit(self._transcribe_and_inject, audio)

    def _transcribe_and_inject(self, audio) -> None:
        try:
            text = self._transcriber.transcribe(audio)
            logger.info("Transcription: %s", text)
            if text:
                self._injecting = True
                try:
                    inject_text(text)
                finally:
                    self._injecting = False
            if self._config.play_sound:
                feedback.beep_done()
        except Exception:
            logger.exception("Transcription failed")
            if self._config.play_sound:
                feedback.beep_error()
        finally:
            self._tray.set_status("Ready")

    def _open_settings(self) -> None:
        if self._config_path is None:
            return
        from whisper_stt.settings_gui import open_settings_window
        open_settings_window(self._config, self._config_path, self._apply_config)

    def _apply_config(self, new_config: Config) -> None:
        old = self._config
        self._config = new_config

        # Hotkey change: re-register
        if old.hotkey != new_config.hotkey or old.mode != new_config.mode:
            self._hotkey.unregister()
            self._hotkey = HotkeyManager(new_config)
            self._hotkey.register(self._on_press, self._on_release)
            logger.info("Hotkey re-registered: %s", new_config.hotkey)

        # Model-affecting settings: reload model
        if (old.model_size != new_config.model_size
                or old.device != new_config.device
                or old.compute_type != new_config.compute_type):
            self._tray.set_status("Reloading model...")
            self._transcriber = Transcriber(new_config)
            future = self._executor.submit(self._load_model)
            future.add_done_callback(self._on_model_loaded)
            logger.info("Model reload triggered")
        else:
            # Hot-reload: update transcriber config reference
            self._transcriber._config = new_config

        # Update audio recorder config
        self._audio._config = new_config
        logger.info("Config applied")

    def _shutdown(self) -> None:
        logger.info("Shutting down...")
        self._hotkey.unregister()
        self._audio.close()
        self._executor.shutdown(wait=False, cancel_futures=True)
