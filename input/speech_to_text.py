"""Speech-to-text transcription for streamer voice input."""

import asyncio
import numpy as np
from typing import Optional
import tempfile
import wave

from utils.logger import log

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    log.warning("Whisper not available - install with: pip install openai-whisper")


class SpeechToText:
    """Transcribes audio to text using Whisper."""

    def __init__(self, model_size: str = "base"):
        """
        Initialize speech-to-text.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
                       - tiny: fastest, least accurate (~1GB RAM)
                       - base: good balance (~1GB RAM) [RECOMMENDED]
                       - small: better accuracy (~2GB RAM)
                       - medium: high accuracy (~5GB RAM)
                       - large: best accuracy (~10GB RAM)
        """
        if not WHISPER_AVAILABLE:
            raise ImportError(
                "Whisper is required for speech-to-text. "
                "Install with: pip install openai-whisper"
            )

        self.model_size = model_size
        self.model = None
        self.is_loaded = False

        log.info(f"Speech-to-text initialized (model={model_size})")

    async def load_model(self):
        """Load Whisper model (async to avoid blocking)."""
        if self.is_loaded:
            return

        try:
            log.info(f"Loading Whisper {self.model_size} model...")

            # Load in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                whisper.load_model,
                self.model_size
            )

            self.is_loaded = True
            log.success(f"Whisper {self.model_size} model loaded")

        except Exception as e:
            log.error(f"Failed to load Whisper model: {e}")
            raise

    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: str = "en"
    ) -> Optional[str]:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio
            language: Language code (en, es, fr, etc.)

        Returns:
            Transcribed text or None if failed
        """
        if not self.is_loaded:
            await self.load_model()

        try:
            # Whisper expects float32 audio normalized to [-1, 1]
            audio_normalized = audio_data.astype(np.float32)

            # Ensure audio is in correct range
            max_val = np.abs(audio_normalized).max()
            if max_val > 1.0:
                audio_normalized = audio_normalized / max_val

            log.debug(f"Transcribing audio: {len(audio_normalized)} samples")

            # Run transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_normalized,
                    language=language,
                    fp16=False  # Disable FP16 for CPU compatibility
                )
            )

            text = result["text"].strip()

            if text:
                log.info(f"Transcribed: {text}")
                return text
            else:
                log.debug("No speech detected in audio")
                return None

        except Exception as e:
            log.error(f"Transcription failed: {e}")
            return None

    async def transcribe_file(self, audio_path: str, language: str = "en") -> Optional[str]:
        """
        Transcribe audio from file.

        Args:
            audio_path: Path to audio file
            language: Language code

        Returns:
            Transcribed text or None if failed
        """
        if not self.is_loaded:
            await self.load_model()

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(audio_path, language=language, fp16=False)
            )

            text = result["text"].strip()
            if text:
                log.info(f"Transcribed from file: {text}")
                return text

            return None

        except Exception as e:
            log.error(f"File transcription failed: {e}")
            return None


class StreamerVoiceInput:
    """High-level interface for streamer voice input."""

    def __init__(self, model_size: str = "base"):
        """Initialize streamer voice input system."""
        self.stt = SpeechToText(model_size=model_size)
        self.last_transcription = None
        self.transcription_queue = asyncio.Queue()

    async def initialize(self):
        """Initialize the voice input system."""
        await self.stt.load_model()
        log.success("Streamer voice input system ready")

    async def process_audio(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """
        Process audio and get transcription.

        Args:
            audio_data: Audio data from microphone
            sample_rate: Sample rate
        """
        text = await self.stt.transcribe(audio_data, sample_rate)

        if text:
            self.last_transcription = text
            await self.transcription_queue.put({
                "text": text,
                "timestamp": asyncio.get_event_loop().time()
            })

    async def get_transcription(self, timeout: float = 0.1) -> Optional[dict]:
        """
        Get next transcription from queue.

        Args:
            timeout: Max time to wait

        Returns:
            Transcription dict or None
        """
        try:
            return await asyncio.wait_for(
                self.transcription_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None


if __name__ == "__main__":
    # Test speech-to-text
    async def test():
        print("Testing Speech-to-Text...")

        if not WHISPER_AVAILABLE:
            print("ERROR: Whisper not installed")
            print("Install with: pip install openai-whisper")
            return

        stt = SpeechToText(model_size="base")
        await stt.load_model()

        # Test with a sample phrase
        print("\nWhisper model loaded successfully!")
        print("To test with actual audio, record a WAV file and use:")
        print("  text = await stt.transcribe_file('your_audio.wav')")

    asyncio.run(test())
