# How to Talk with CUDA-chan

## Microphone Input Now Active! ✅

The microphone input system is **fully integrated** into the orchestrator. CUDA-chan can now:
- ✅ Listen to your microphone
- ✅ Read YouTube chat
- ✅ Watch your screen
- ✅ Speak via TTS
- ✅ Show emotions
- ✅ Respond to you as a sidekick!

## How It Works

### 1. Voice Input (Primary Mode)
**Just speak naturally** - No special commands needed!

1. **Start CUDA-chan** - The microphone will activate automatically
2. **Speak** - CUDA-chan listens via Whisper transcription
3. **She responds** - Via TTS with her voice and emotions

**Important Behavior:**
- CUDA-chan will **NOT speak while you're speaking** - she's polite!
- If she's speaking and you start talking, she'll **stop immediately** to listen
- Your voice input has **CRITICAL priority** (highest in the system)

### 2. Chat Interaction
You can also type in YouTube live chat for backup communication.

**Example:**
```
You (in chat): @CUDA-chan how are you?
CUDA-chan: I'm doing great! Ready to help with the stream!
```

### 3. Screen Observation
CUDA-chan watches what's on screen and can comment on it (vision system active).

## Setup Requirements

### Install Audio Dependencies

```bash
# Install required packages
pip install sounddevice openai-whisper torch torchaudio
```

### Configure Microphone (Optional)

If you have multiple microphones, you can specify which one to use:

```bash
# List available audio devices
python -c "from input.audio_monitor import AudioMonitor; AudioMonitor.list_devices()"
```

Then add to your `.env`:
```bash
AUDIO_DEVICE_INDEX=0  # Your microphone device number
WHISPER_MODEL_SIZE=base  # tiny, base, small, medium, large
```

**Model Size Recommendations:**
- `tiny` - Fastest, least accurate (~1GB RAM)
- `base` - **Recommended** - Good balance (~1GB RAM)
- `small` - Better accuracy (~2GB RAM)
- `medium` - High accuracy (~5GB RAM)
- `large` - Best accuracy (~10GB RAM)

## Testing Your Microphone

```bash
# Test microphone detection
python -c "from input.audio_monitor import AudioMonitor; AudioMonitor.list_devices()"

# Test speech-to-text
python -c "
from input.speech_to_text import SpeechToText
import asyncio

async def test():
    stt = SpeechToText(model_size='base')
    await stt.load_model()
    print('Whisper loaded successfully!')

asyncio.run(test())
"
```

## How CUDA-chan Listens

### Voice Activity Detection (VAD)
- Automatically detects when you start speaking
- Buffers 3 seconds of audio
- Transcribes when you stop speaking
- No manual activation needed!

### Speech Priority System
1. **CRITICAL** - Your voice (streamer microphone)
2. **HIGH** - Chat mentions (@CUDA-chan)
3. **MEDIUM** - General chat messages
4. **LOW** - Idle commentary

### Polite AI Behavior
- Won't interrupt you while speaking
- Stops mid-sentence if you start talking
- Waits for natural pauses to respond
- Focuses on being a supportive sidekick

## Running CUDA-chan

```bash
# Just run normally - microphone activates automatically
python main.py
```

You should see:
```
[INFO] Initializing streamer voice input...
[SUCCESS] Whisper base model loaded
[SUCCESS] Audio monitor started - listening for streamer voice
[SUCCESS] Microphone input active - CUDA-chan can now hear you!
```

## Troubleshooting

### "Failed to initialize microphone"
**Solution:**
1. Check that your microphone is connected and working
2. Verify permissions (macOS/Linux may need microphone access)
3. Try specifying device index in `.env`
4. Check if another app is using the microphone

### "Whisper not available"
**Solution:**
```bash
pip install openai-whisper torch torchaudio
```

### Speech not detected
**Solution:**
1. Check your microphone volume/gain
2. Try lowering the threshold in `AudioMonitor` (default: 0.02)
3. Speak louder or move closer to microphone
4. Check device selection with `list_devices()`

### AI speaks over me
**Solution:**
- This shouldn't happen! The system is designed to detect your speech and stop
- If it does, please report as a bug - there may be VAD tuning needed
- Try adjusting `threshold` in audio_monitor.py

## Features

### Real-Time Transcription
- Uses OpenAI Whisper (local, no API calls)
- Runs on CPU or GPU (auto-detects)
- English by default (configurable for other languages)
- Fast turnaround with `base` model

### Smart Interruption Handling
- Detects when streamer starts speaking
- Immediately stops AI speech
- Clears audio queue to listen
- Resumes naturally after streamer finishes

### Context-Aware Responses
- Remembers recent conversation
- Knows what's on screen (vision)
- Sees chat messages
- Responds as supportive sidekick

## Example Interactions

**You:** "Hey CUDA-chan, how's it going?"
**CUDA-chan:** "Hey! I'm doing great, excited to be here with you! What are we playing today?"

**You:** "What do you think about this game?"
**CUDA-chan:** "Ooh, this looks interesting! The graphics are really nice. Are you going for a speedrun or just exploring?"

**You:** "Should I go left or right here?"
**CUDA-chan:** "Hmm, I'd say right - I think I saw something shiny over there! But it's your call, I'm just along for the ride!"

---

**Ready to stream with your AI sidekick!** 🎮🤖
