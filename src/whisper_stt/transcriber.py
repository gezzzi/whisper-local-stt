from __future__ import annotations

import logging
import time

import numpy as np
from faster_whisper import WhisperModel

from whisper_stt.config import Config

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._model: WhisperModel | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        self._model = WhisperModel(
            self._config.model_size,
            device=self._config.device,
            compute_type=self._config.compute_type,
        )

    def transcribe(self, audio: np.ndarray) -> str:
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        if audio.size == 0:
            return ""
        t0 = time.perf_counter()
        segments, info = self._model.transcribe(
            audio,
            language=self._config.language,
            beam_size=self._config.beam_size,
            vad_filter=self._config.vad_filter,
            vad_parameters={"min_silence_duration_ms": 300},
            condition_on_previous_text=self._config.condition_on_previous_text,
            without_timestamps=True,
            no_speech_threshold=0.4,
            log_prob_threshold=-1.0,
        )
        parts: list[str] = []
        avg_logprobs: list[float] = []
        for seg in segments:
            parts.append(seg.text)
            avg_logprobs.append(seg.avg_logprob)

        elapsed = time.perf_counter() - t0
        audio_dur = audio.size / self._config.sample_rate
        text = "".join(parts).strip()

        # Log performance and quality metrics
        avg_confidence = sum(avg_logprobs) / len(avg_logprobs) if avg_logprobs else 0.0
        logger.info(
            "Transcription stats: beam=%d, inference=%.2fs, audio=%.1fs, "
            "RTF=%.2f, confidence=%.3f, lang=%s(prob=%.2f)",
            self._config.beam_size, elapsed, audio_dur,
            elapsed / audio_dur if audio_dur > 0 else 0,
            avg_confidence, info.language, info.language_probability,
        )

        return text
