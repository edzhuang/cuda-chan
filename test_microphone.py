#!/usr/bin/env python3
"""Test microphone input and voice activity detection."""

import asyncio
import numpy as np
from input.audio_monitor import AudioMonitor
import sys

async def test_microphone():
    """Test microphone detection with various thresholds."""

    print("\n" + "="*60)
    print("CUDA-chan Microphone Test")
    print("="*60 + "\n")

    # List available devices
    print("Available audio devices:")
    AudioMonitor.list_devices()
    print()

    # Test with current threshold
    threshold = 0.015
    print(f"Testing with threshold={threshold}")
    print("Speak into your microphone for 10 seconds...")
    print("Watch for 'SPEECH DETECTED!' messages\n")

    speech_detected = False

    def on_speech(audio_data):
        nonlocal speech_detected
        speech_detected = True
        magnitude = np.abs(audio_data).mean()
        max_magnitude = np.abs(audio_data).max()
        print(f"\n✅ SPEECH DETECTED!")
        print(f"   Samples: {len(audio_data)}")
        print(f"   Average magnitude: {magnitude:.4f}")
        print(f"   Max magnitude: {max_magnitude:.4f}")
        print(f"   Threshold: {threshold:.4f}\n")

    monitor = AudioMonitor(threshold=threshold)
    monitor.set_speech_callback(on_speech)

    try:
        await monitor.start()

        # Monitor for 10 seconds, showing live magnitude
        print("Listening... (audio levels shown below)")
        print("-" * 60)

        for i in range(100):  # 10 seconds (100 * 0.1s)
            await asyncio.sleep(0.1)

            # Get current audio and show magnitude
            if i % 5 == 0:  # Every 0.5 seconds
                current_audio = monitor.get_current_audio()
                if len(current_audio) > 0:
                    magnitude = np.abs(current_audio[-1000:]).mean()  # Last 1000 samples
                    bar_length = int(magnitude * 1000)  # Scale for display
                    bar = "█" * min(bar_length, 50)
                    status = "🔊 SPEAKING" if magnitude > threshold else "🔇 silence"
                    print(f"{status} | {magnitude:.4f} | {bar}", end="\r")

        print("\n" + "-" * 60)

        await monitor.stop()

        print("\nTest complete!")

        if speech_detected:
            print("✅ SUCCESS: Your microphone is working!")
            print("   Speech was detected successfully.")
        else:
            print("❌ PROBLEM: No speech detected!")
            print("\nPossible issues:")
            print("1. Microphone volume too low")
            print("2. Wrong microphone selected")
            print("3. Threshold too high for your environment")
            print("\nSuggestions:")
            print("- Check your system microphone volume/gain settings")
            print("- Try speaking louder or closer to the mic")
            print("- If you saw bars moving, but no detection, threshold is too high")
            print("- Try lowering threshold in orchestrator.py (currently 0.015)")
            print("  Recommended values: 0.01, 0.005, or even 0.001")

            # Show what the average magnitude was
            current_audio = monitor.get_current_audio()
            if len(current_audio) > 0:
                avg_mag = np.abs(current_audio).mean()
                max_mag = np.abs(current_audio).max()
                print(f"\nYour audio levels during test:")
                print(f"  Average: {avg_mag:.4f}")
                print(f"  Maximum: {max_mag:.4f}")
                print(f"  Current threshold: {threshold:.4f}")

                if max_mag > 0:
                    suggested = max_mag * 0.3  # 30% of max
                    print(f"  Suggested threshold: {suggested:.4f}")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        await monitor.stop()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_microphone())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
