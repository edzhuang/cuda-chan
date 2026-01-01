# How to Talk with CUDA-chan

## Current Status: Audio Input Not Yet Integrated ⚠️

**Important**: The microphone input system has been created but is **not yet integrated** into the orchestrator. Right now, CUDA-chan can only:
- ✅ Read YouTube chat
- ✅ Watch your screen
- ✅ Speak via TTS
- ✅ Show emotions
- ❌ Listen to your microphone (not connected yet)

## What Works Now

### 1. Chat Interaction
Type in YouTube live chat and CUDA-chan will respond!

**Example:**
```
You (in chat): @CUDA-chan how are you?
CUDA-chan: I'm doing great! Ready to hang out with everyone!
```

### 2. Screen Observation
CUDA-chan watches what's on screen and can comment on it (vision system active).

## How to Enable Microphone (Future - Needs Integration)

Once the orchestrator is updated (see `core/orchestrator.py`), you'll be able to:

1. **Just speak naturally** - No special commands needed
2. **CUDA-chan listens** - Whisper transcribes your voice
3. **She responds** - Via TTS with her voice

### Setup Steps (When Integrated):

```bash
# 1. Install audio dependencies
pip install sounddevice openai-whisper torch

# 2. Test your microphone
python -m input.audio_monitor

# 3. Configure device (optional)
# Edit .env and add:
AUDIO_DEVICE_INDEX=0  # Your microphone device number
WHISPER_MODEL_SIZE=base  # tiny, base, small, medium, large

# 4. Run CUDA-chan
python main.py
```

## Integration TODO

The orchestrator needs these updates in `core/orchestrator.py`:

```python
# In __init__:
from input.audio_monitor import AudioMonitor
from input.speech_to_text import StreamerVoiceInput

self.audio_monitor = AudioMonitor()
self.voice_input = StreamerVoiceInput()

# In initialize():
await self.voice_input.initialize()
self.audio_monitor.set_speech_callback(self._on_streamer_speech)
await self.audio_monitor.start()

# New method:
async def _on_streamer_speech(self, audio_data):
    text = await self.voice_input.stt.transcribe(audio_data)
    if text:
        await self.event_queue.put(
            EventType.STREAMER_SPEECH,
            {"text": text},
            Priority.CRITICAL,
            "streamer_microphone"
        )
```

## Temporary Workaround: Use Chat

Until microphone is integrated, you can simulate talking by using YouTube chat:
- Type your messages in chat
- Mention @CUDA-chan to get her attention
- She'll respond as if you talked to her!

## Testing Microphone Components

Test the audio system components individually:

```bash
# Test microphone detection
python -c "from input.audio_monitor import AudioMonitor; AudioMonitor.list_devices()"

# Test speech-to-text (requires setup)
python -c "
from input.speech_to_text import SpeechToText
import asyncio

async def test():
    stt = SpeechToText(model_size='tiny')
    await stt.load_model()
    print('Whisper loaded successfully!')

asyncio.run(test())
"
```

## Current Limitations

Without orchestrator integration:
- ❌ Can't hear your voice via microphone
- ❌ Can't respond to spoken commands
- ❌ Won't react to streamer speech events
- ✅ All other features work (chat, vision, TTS, avatar)

## When Will This Work?

The microphone integration requires updating the orchestrator. This is on the TODO list but hasn't been implemented yet to avoid breaking existing functionality.

You can either:
1. **Wait** for orchestrator integration
2. **Use chat** as temporary substitute
3. **Integrate yourself** using the code examples above

---

**For now, communicate with CUDA-chan via YouTube chat!** 💬
