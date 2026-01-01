"""Text-to-Speech manager using ElevenLabs API."""

import asyncio
from pathlib import Path
from typing import Optional
import pygame
from elevenlabs import ElevenLabs, VoiceSettings
from elevenlabs.client import AsyncElevenLabs

from config.settings import settings
from utils.logger import log


class TTSManager:
    """Manages text-to-speech using ElevenLabs."""

    def __init__(self):
        """Initialize TTS manager."""
        # Initialize ElevenLabs client
        self.client = AsyncElevenLabs(api_key=settings.api.elevenlabs_api_key)

        # Voice settings
        self.voice_id = settings.personality.voice_settings.voice_id
        self.voice_settings = VoiceSettings(
            stability=settings.personality.voice_settings.stability,
            similarity_boost=settings.personality.voice_settings.similarity_boost,
            style=settings.personality.voice_settings.style,
            use_speaker_boost=settings.personality.voice_settings.use_speaker_boost
        )

        # Temp directory for playback
        self.temp_dir = settings.get_cache_dir() / "tts_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Audio playback
        pygame.mixer.init()
        self.is_speaking = False
        self.audio_queue = asyncio.Queue()

        # Statistics
        self.total_characters_generated = 0

        log.info(f"TTS manager initialized (voice_id={self.voice_id[:20]}...)")

    async def generate_speech(self, text: str, use_cache: bool = False) -> Optional[bytes]:
        """
        Generate speech audio from text.

        Args:
            text: Text to speak
            use_cache: Whether to use cache (disabled by default)

        Returns:
            Audio data as bytes or None if failed
        """
        if not text or not text.strip():
            log.warning("Empty text provided for TTS")
            return None

        # Caching disabled - always generate fresh audio
        try:
            log.debug(f"Generating TTS for: {text[:50]}...")

            # Call ElevenLabs API
            # Using eleven_turbo_v2_5 - free tier compatible model
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",
                voice_settings=self.voice_settings
            )

            # Collect audio chunks
            audio_data = b""
            async for chunk in audio_generator:
                audio_data += chunk

            # Update statistics
            self.total_characters_generated += len(text)

            return audio_data

        except Exception as e:
            log.error(f"TTS generation failed: {e}")
            return None

    async def speak(self, text: str, wait: bool = False) -> bool:
        """
        Speak text (queues for playback).

        Args:
            text: Text to speak
            wait: If True, wait until speaking completes

        Returns:
            True if queued successfully
        """
        if not text or not text.strip():
            return False

        # Check character limit
        if len(text) > 500:
            log.warning(f"Text too long ({len(text)} chars), truncating")
            text = text[:500]

        log.info(f"Queuing speech: {text[:50]}...")

        # Generate audio
        audio_data = await self.generate_speech(text)
        if not audio_data:
            return False

        # Queue for playback
        await self.audio_queue.put({
            "audio": audio_data,
            "text": text
        })

        if wait:
            # Wait until this audio finishes playing
            while not self.audio_queue.empty() or self.is_speaking:
                await asyncio.sleep(0.1)

        return True

    async def playback_worker(self):
        """Background worker to play queued audio."""
        log.info("TTS playback worker started")

        while True:
            try:
                # Get next audio from queue
                audio_item = await self.audio_queue.get()

                if audio_item is None:  # Shutdown signal
                    break

                audio_data = audio_item["audio"]
                text = audio_item["text"]

                # Save to temp file for pygame
                temp_path = self.temp_dir / "temp_playback.mp3"
                with open(temp_path, "wb") as f:
                    f.write(audio_data)

                # Play audio
                self.is_speaking = True
                log.debug(f"Playing: {text[:50]}...")

                try:
                    pygame.mixer.music.load(str(temp_path))
                    pygame.mixer.music.play()

                    # Wait until playback finishes
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)

                except Exception as e:
                    log.error(f"Audio playback failed: {e}")

                finally:
                    self.is_speaking = False
                    log.debug("Playback completed")

            except Exception as e:
                log.error(f"Playback worker error: {e}")
                self.is_speaking = False

        log.info("TTS playback worker stopped")

    async def stop_speaking(self):
        """Stop current speech playback."""
        if self.is_speaking:
            pygame.mixer.music.stop()
            self.is_speaking = False
            log.info("Speech stopped")

    async def clear_queue(self):
        """Clear all queued audio."""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        log.info("Audio queue cleared")

    def estimate_duration(self, text: str) -> float:
        """
        Estimate speech duration in seconds.

        Args:
            text: Text to speak

        Returns:
            Estimated duration in seconds
        """
        # Rough estimate: ~150 words per minute, ~5 chars per word
        words = len(text) / 5
        duration = (words / 150) * 60
        return max(1.0, duration)  # Minimum 1 second

    async def test_voice(self, test_text: str = "Hello! This is a test of my voice.") -> bool:
        """
        Test voice generation.

        Args:
            test_text: Text to test with

        Returns:
            True if successful
        """
        log.info("Testing TTS voice...")
        audio_data = await self.generate_speech(test_text, use_cache=False)

        if audio_data:
            log.success("TTS test successful")
            return True
        else:
            log.error("TTS test failed")
            return False

    def get_statistics(self) -> dict:
        """Get TTS usage statistics."""
        return {
            "total_characters_generated": self.total_characters_generated,
            "is_speaking": self.is_speaking,
            "queue_size": self.audio_queue.qsize()
        }

    async def cleanup(self):
        """Cleanup resources."""
        # Signal playback worker to stop
        await self.audio_queue.put(None)
        await self.stop_speaking()
        pygame.mixer.quit()
        log.info("TTS manager cleaned up")


if __name__ == "__main__":
    # Test TTS manager
    async def test_tts():
        tts = TTSManager()

        # Start playback worker
        playback_task = asyncio.create_task(tts.playback_worker())

        # Test voice
        if await tts.test_voice():
            # Test speaking
            await tts.speak("Hello everyone! I'm CUDA-chan, ready to play some games!")
            await asyncio.sleep(1)
            await tts.speak("This is a test of the text to speech system.", wait=True)

            print(f"\nStatistics: {tts.get_statistics()}")

        # Cleanup
        await tts.cleanup()
        await playback_task

    # Uncomment to test (requires valid API key and voice ID)
    # asyncio.run(test_tts())
    print("TTS manager module loaded. Requires ElevenLabs API key and voice ID to test.")
