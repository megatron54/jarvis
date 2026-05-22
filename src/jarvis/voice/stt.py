"""Speech-to-Text using faster-whisper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class STTEngine:
    """Speech-to-Text engine using faster-whisper."""

    def __init__(self, model_size: str = "small", device: str = "cuda", compute_type: str = "float16"):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model: Any = None

    def initialize(self) -> None:
        """Load the Whisper model."""
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
            logger.info("STT engine initialized", model=self._model_size, device=self._device)
        except ImportError:
            logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
        except Exception as e:
            logger.error("Failed to initialize STT", error=str(e))

    def transcribe(self, audio_path: str | Path, language: str | None = None) -> str:
        """Transcribe an audio file to text."""
        if not self._model:
            return ""

        segments, info = self._model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        text = " ".join(segment.text.strip() for segment in segments)
        logger.debug("Transcription complete", language=info.language, duration=info.duration)
        return text

    def transcribe_stream(self, audio_data: bytes, language: str | None = None) -> str:
        """Transcribe audio bytes (e.g., from microphone)."""
        if not self._model:
            return ""

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            f.write(audio_data)
            f.flush()
            return self.transcribe(f.name, language=language)
