from __future__ import annotations

import numpy as np
import sounddevice as sd

from whisper_stt.config import Config


class AudioRecorder:
    def __init__(self, config: Config) -> None:
        self._sample_rate = config.sample_rate
        self._buffer: list[np.ndarray] = []
        self._recording = False
        self._stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=config.channels,
            dtype="float32",
            callback=self._callback,
            blocksize=1024,
        )
        self._stream.start()

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        if self._recording:
            self._buffer.append(indata.copy())

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        self._buffer.clear()
        self._recording = True

    def stop(self) -> np.ndarray:
        self._recording = False
        if not self._buffer:
            return np.array([], dtype="float32")
        audio = np.concatenate(self._buffer, axis=0)
        self._buffer.clear()
        return audio.flatten()

    def close(self) -> None:
        self._stream.stop()
        self._stream.close()
