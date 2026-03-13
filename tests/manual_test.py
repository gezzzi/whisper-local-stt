"""Manual test: record 3 seconds of audio and transcribe to Japanese text.

Run this script to verify the core pipeline works:
    python tests/manual_test.py
"""
from __future__ import annotations

import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURATION = 3  # seconds


def main() -> None:
    print("Loading model (large-v3-turbo, float16, CUDA)...")
    model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    print("Model loaded.\n")

    print(f"Recording {DURATION} seconds... Speak in Japanese!")
    audio = sd.rec(
        DURATION * SAMPLE_RATE,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    audio = audio.flatten()
    print(f"Recorded {audio.size} samples ({audio.size / SAMPLE_RATE:.1f}s)\n")

    print("Transcribing...")
    t0 = time.perf_counter()
    segments, info = model.transcribe(
        audio,
        language="ja",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
        without_timestamps=True,
    )
    text = "".join(seg.text for seg in segments)
    elapsed = time.perf_counter() - t0

    print(f"Result: {text}")
    print(f"Time: {elapsed:.3f}s")
    print(f"Detected language: {info.language} (prob={info.language_probability:.2f})")


if __name__ == "__main__":
    main()
