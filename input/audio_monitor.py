"""Audio monitor for capturing streamer microphone input."""

import asyncio
import numpy as np
from typing import Optional, Callable
import sounddevice as sd
from collections import deque

from utils.logger import log


class AudioMonitor:
    """Monitors microphone input and detects speech."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: Optional[int] = None,
        threshold: float = 0.02,
        buffer_duration: float = 3.0
    ):
        """
        Initialize audio monitor.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            device: Audio device index (None for default)
            threshold: Voice activity detection threshold
            buffer_duration: Duration of audio buffer in seconds
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.threshold = threshold

        # Audio buffer to store recent audio
        buffer_size = int(sample_rate * buffer_duration)
        self.audio_buffer = deque(maxlen=buffer_size)

        self.stream: Optional[sd.InputStream] = None
        self.is_monitoring = False
        self.speech_callback: Optional[Callable] = None

        # Voice activity detection state
        self.is_speaking = False
        self.silence_frames = 0
        self.speech_frames = 0
        self.min_speech_frames = 10  # Minimum frames to consider speech
        self.max_silence_frames = 15  # Max silence before ending speech

        log.info(f"Audio monitor initialized (rate={sample_rate}Hz, device={device or 'default'})")

    def _audio_callback(self, indata, frames, time, status):
        """
        Callback for audio stream.

        Args:
            indata: Input audio data
            frames: Number of frames
            time: Time info
            status: Stream status
        """
        if status:
            log.warning(f"Audio stream status: {status}")

        # Convert to numpy array and get magnitude
        audio_data = indata[:, 0] if self.channels > 1 else indata.flatten()
        magnitude = np.abs(audio_data).mean()

        # Add to buffer
        self.audio_buffer.extend(audio_data.tolist())

        # Voice activity detection
        if magnitude > self.threshold:
            self.speech_frames += 1
            self.silence_frames = 0

            if not self.is_speaking and self.speech_frames >= self.min_speech_frames:
                self.is_speaking = True
                log.info("Speech detected - started")
        else:
            self.silence_frames += 1
            self.speech_frames = 0

            if self.is_speaking and self.silence_frames >= self.max_silence_frames:
                self.is_speaking = False
                log.info("Speech detected - ended, transcribing...")

                # Trigger speech callback with buffered audio
                if self.speech_callback:
                    audio_array = np.array(list(self.audio_buffer), dtype=np.float32)
                    asyncio.create_task(self.speech_callback(audio_array))

    async def start(self):
        """Start monitoring audio input."""
        if self.is_monitoring:
            log.warning("Audio monitor already running")
            return

        try:
            # List available devices for debugging
            devices = sd.query_devices()
            log.debug(f"Available audio devices: {len(devices)}")

            # Start audio stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device,
                callback=self._audio_callback,
                blocksize=1024
            )

            self.stream.start()
            self.is_monitoring = True
            log.success("Audio monitor started - listening for streamer voice")

        except Exception as e:
            log.error(f"Failed to start audio monitor: {e}")
            raise

    async def stop(self):
        """Stop monitoring audio input."""
        if not self.is_monitoring:
            return

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            self.is_monitoring = False
            self.audio_buffer.clear()
            log.info("Audio monitor stopped")

        except Exception as e:
            log.error(f"Error stopping audio monitor: {e}")

    def set_speech_callback(self, callback: Callable):
        """
        Set callback for when speech is detected.

        Args:
            callback: Async function to call with audio data
        """
        self.speech_callback = callback

    def get_current_audio(self) -> np.ndarray:
        """
        Get current audio buffer.

        Returns:
            Audio data as numpy array
        """
        return np.array(list(self.audio_buffer), dtype=np.float32)

    @staticmethod
    def list_devices():
        """List available audio input devices."""
        devices = sd.query_devices()
        print("\n" + "="*60)
        print("Available Audio Input Devices:")
        print("="*60 + "\n")

        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                default = " (DEFAULT)" if i == sd.default.device[0] else ""
                print(f"[{i}] {device['name']}{default}")
                print(f"    Channels: {device['max_input_channels']}")
                print(f"    Sample Rate: {device['default_samplerate']:.0f} Hz")
                print()


if __name__ == "__main__":
    # Test audio monitor
    AudioMonitor.list_devices()

    print("\nTo test audio monitoring, uncomment the code below:")
    print("Note: This will listen to your microphone for 10 seconds\n")

    # async def test():
    #     monitor = AudioMonitor()
    #
    #     def on_speech(audio_data):
    #         print(f"Speech detected! Audio length: {len(audio_data)} samples")
    #
    #     monitor.set_speech_callback(on_speech)
    #     await monitor.start()
    #
    #     print("Listening... speak into your microphone")
    #     await asyncio.sleep(10)
    #
    #     await monitor.stop()
    #     print("Test complete")
    #
    # asyncio.run(test())
