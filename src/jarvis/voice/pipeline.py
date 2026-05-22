"""Voice pipeline: Wake Word → STT → LLM → TTS."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

logger = structlog.get_logger()


class VoicePipeline:
    """Complete voice interaction pipeline."""

    def __init__(self, stt_engine: Any, tts_engine: Any, ollama_client: Any):
        self._stt = stt_engine
        self._tts = tts_engine
        self._ollama = ollama_client
        self._listening = False

    async def process_audio(self, audio_data: bytes, session_id: str = "voice") -> bytes | None:
        """Process audio input: STT → LLM → TTS. Returns audio response."""
        # 1. Speech to Text
        text = self._stt.transcribe_stream(audio_data)
        if not text.strip():
            return None

        logger.info("Voice input", text=text)

        # 2. LLM Response
        response = await self._ollama.chat(
            messages=[
                {"role": "system", "content": "You are Jarvis, a voice assistant. Keep responses concise and natural for spoken delivery. Max 2-3 sentences."},
                {"role": "user", "content": text},
            ]
        )

        response_text = response["content"]
        logger.info("Voice response", text=response_text[:100])

        # 3. Text to Speech
        audio_response = self._tts.synthesize(response_text)
        return audio_response

    async def start_listening(self) -> None:
        """Start the continuous listening loop with wake word detection."""
        try:
            from openwakeword.model import Model as WakeWordModel
            import sounddevice as sd
            import numpy as np

            ww_model = WakeWordModel(wakeword_models=["hey_jarvis"])
            logger.info("Wake word detection active")

            self._listening = True
            sample_rate = 16000
            chunk_size = 1280  # 80ms at 16kHz

            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning("Audio status", status=status)
                # Process wake word
                audio_chunk = (indata[:, 0] * 32767).astype(np.int16)
                prediction = ww_model.predict(audio_chunk)
                for name, score in prediction.items():
                    if score > 0.5:
                        logger.info("Wake word detected!", score=score)
                        # TODO: trigger recording and processing

            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk_size,
                callback=audio_callback,
            ):
                while self._listening:
                    await asyncio.sleep(0.1)

        except ImportError:
            logger.error("Voice dependencies not installed. Install with: pip install jarvis[voice]")

    def stop_listening(self) -> None:
        """Stop the listening loop."""
        self._listening = False
