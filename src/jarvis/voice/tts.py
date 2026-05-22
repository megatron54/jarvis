"""Text-to-Speech using Kokoro TTS."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class TTSEngine:
    """Text-to-Speech engine using Kokoro."""

    def __init__(self, voice: str = "af_heart", speed: float = 1.0):
        self._voice = voice
        self._speed = speed
        self._pipeline: Any = None

    def initialize(self) -> None:
        """Load the TTS pipeline."""
        try:
            from kokoro import KPipeline
            self._pipeline = KPipeline(lang_code="a")  # auto-detect language
            logger.info("TTS engine initialized", voice=self._voice)
        except ImportError:
            logger.error("kokoro not installed. Install with: pip install kokoro")
        except Exception as e:
            logger.error("Failed to initialize TTS", error=str(e))

    def synthesize(self, text: str, output_path: str | Path | None = None) -> bytes | None:
        """Synthesize text to speech. Returns WAV bytes or saves to file."""
        if not self._pipeline:
            return None

        import numpy as np
        import io
        import wave

        # Generate audio
        audio_segments = []
        for _, _, audio in self._pipeline(text, voice=self._voice, speed=self._speed):
            if audio is not None:
                audio_segments.append(audio)

        if not audio_segments:
            return None

        # Concatenate all audio segments
        full_audio = np.concatenate(audio_segments)

        # Convert to WAV bytes
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(24000)
            wf.writeframes((full_audio * 32767).astype(np.int16).tobytes())

        wav_bytes = buffer.getvalue()

        if output_path:
            Path(output_path).write_bytes(wav_bytes)

        return wav_bytes

    def stream_synthesize(self, text: str):
        """Generator that yields audio chunks for streaming playback."""
        if not self._pipeline:
            return

        import numpy as np

        for _, _, audio in self._pipeline(text, voice=self._voice, speed=self._speed):
            if audio is not None:
                yield (audio * 32767).astype(np.int16).tobytes()
