# CUDA-chan 🤖✨

An AI sidekick for streamers - provides live commentary, reactions, and chat engagement while you game!

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎬 What is CUDA-chan?

CUDA-chan is your **AI streaming companion** - think of her as your co-host who:
- **Listens** to you via microphone and responds naturally
- **Watches** your gameplay and provides commentary
- **Engages** with your chat actively
- **Reacts** to exciting moments with you
- **Supports** you with encouragement and banter

**You** play the game. **You** run the stream. CUDA-chan makes it more fun!

## ✨ Features

- **🎤 Voice Interaction** - Listens to you via microphone (Whisper speech-to-text)
- **🎭 Live2D Avatar** - Animated expressions via VTube Studio
- **🗣️ Natural Voice** - Responds with ElevenLabs text-to-speech
- **👀 Screen Awareness** - Watches your gameplay for context
- **💬 Chat Engagement** - Monitors and responds to YouTube chat
- **🧠 AI Personality** - Powered by Claude Sonnet 4.5
- **😊 Expressive Reactions** - Changes emotions based on context
- **🛡️ Safe & Supportive** - Never backseats, always encourages

## 📋 Requirements

### Software
- Python 3.10+
- [VTube Studio](https://denchisoft.com) (free)
- Microphone for streamer input

### API Keys
- [Anthropic API](https://console.anthropic.com) (~$2-4/hour)
- [ElevenLabs](https://elevenlabs.io) (free tier: ~10k chars/month)

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/edzhuang/cuda-chan.git
cd cuda-chan
./scripts/setup.sh

# Configure API keys
cp .env.example .env
nano .env  # Add your API keys

# Install audio dependencies
pip install sounddevice openai-whisper torch

# Run
python main.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## 🎮 How It Works

```
┌─────────────────────────────────────────────────────┐
│              YOU (The Streamer)                     │
│         Playing game + Talking                      │
└──────────┬──────────────┬───────────────────────────┘
           │              │
    ┌──────▼────┐  ┌──────▼────────┐
    │ Microphone│  │  Game Screen  │
    └──────┬────┘  └──────┬────────┘
           │              │
           │      ┌───────▼─────────┐
           │      │ Screen Capture  │
           │      └───────┬─────────┘
           │              │
    ┌──────▼──────────────▼────────┐
    │      CUDA-chan (AI Sidekick) │
    │  • Listens to you            │
    │  • Watches the game          │
    │  • Reads chat                │
    │  • Reacts & comments         │
    └──────┬───────────────────────┘
           │
    ┌──────▼────────┐
    │  VTube Studio │
    │  (Live2D)     │
    └───────────────┘
```

## 🎙️ Usage

### Basic Streaming Setup

1. **Start VTube Studio** with your Live2D model
2. **Run CUDA-chan**: `python main.py`
3. **Start streaming** - CUDA-chan will appear as your sidekick!
4. **Talk naturally** - She'll respond to you
5. **Play your game** - She'll react and comment

### Interaction Examples

**You**: "Alright chat, let's try this boss again!"
**CUDA-chan**: "You've got this! Third time's the charm, right?"

**Chat**: "@CUDA-chan what do you think of this strategy?"
**CUDA-chan**: "Ooh, interesting! I think it could work if we're careful with the timing!"

**[Exciting moment happens]**
**CUDA-chan**: "OH! That was so close! Did you see that?!"

### Tips for Best Experience

- **Talk to CUDA-chan** - She responds best when you engage with her
- **Let her breathe** - She won't talk over you, give her space to respond
- **Involve chat** - She loves engaging with your viewers
- **Natural flow** - Treat her like a friend who's watching with you

## ⚙️ Configuration

### Personality Customization

Edit [config/personality.yaml](config/personality.yaml) to customize CUDA-chan's:
- Personality traits
- Speaking style
- Catchphrases
- Response patterns

### Key Settings (.env)

```bash
# AI & Voice
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...  # Pre-made voice recommended

# VTube Studio
VTUBE_STUDIO_HOST=localhost
VTUBE_STUDIO_PORT=8001
VTUBE_STUDIO_TOKEN=...  # Obtained on first run

# Performance
TICK_RATE=1.0              # How often AI makes decisions
CLAUDE_MAX_RPM=50          # API rate limit

# Audio Input (Optional - for advanced users)
AUDIO_DEVICE_INDEX=0       # Microphone device
WHISPER_MODEL_SIZE=base    # tiny, base, small, medium, large
```

## 📊 Cost Tracking

Typical costs per hour of streaming:

| Activity Level | Claude API | ElevenLabs | Total/Hour |
|---------------|-----------|------------|------------|
| Light (calm stream) | ~$1.50 | ~$0.20 | ~$1.70 |
| Moderate | ~$2.50 | ~$0.40 | ~$2.90 |
| Active (lots of talk) | ~$4.00 | ~$0.60 | ~$4.60 |

**Free Tier Limits**:
- ElevenLabs: 10,000 chars/month (~5-10 min of speech)
- Consider upgrading for regular streaming

## 🏗️ Project Structure

```
cuda-chan/
├── input/           # NEW: Audio monitoring & speech-to-text
├── config/          # Personality & prompts (UPDATED for sidekick mode)
├── core/            # Orchestrator & event management
├── ai/              # Claude AI integration
├── vision/          # Screen watching (observation only)
├── output/          # VTube Studio + TTS
├── chat/            # YouTube chat integration
├── control/         # DEPRECATED: No longer controls games
├── games/           # DEPRECATED: No longer plays games
├── utils/           # Logging and utilities
└── main.py          # Entry point
```

## 🎯 Roadmap

### ✅ Current (Sidekick MVP)
- Microphone input & speech-to-text
- Natural conversation with streamer
- Screen observation & commentary
- Chat engagement
- Expressive avatar reactions

### 🚧 Phase 2 (Planned)
- [ ] Better voice activity detection
- [ ] Conversation context memory
- [ ] Custom voice training support
- [ ] Multi-language support
- [ ] OBS integration for scene detection
- [ ] Twitch chat support

### 💡 Phase 3 (Future)
- [ ] Multiple AI personality modes
- [ ] Learning from stream analytics
- [ ] Community clip reactions
- [ ] Collaboration features for duo streams

## 🐛 Troubleshooting

### No Microphone Input
- Check microphone permissions
- Run `python -m input.audio_monitor` to list devices
- Set correct `AUDIO_DEVICE_INDEX` in `.env`

### Whisper Loading Slow
- First load downloads model (~1GB for base)
- Use smaller model: `WHISPER_MODEL_SIZE=tiny`
- Models cached after first download

### CUDA-chan Talks Too Much
- Increase `TICK_RATE` in `.env` (slower decisions)
- Adjust personality in `config/personality.yaml`

### VTube Studio Won't Connect
- Check VTube Studio is running
- Enable Plugin API in settings
- Verify token in `.env`

See [SETUP_GUIDE.md](SETUP_GUIDE.md#troubleshooting) for more help.

## 🤝 Contributing

Contributions welcome! This is a new direction for the project. Ideas needed for:
- Better voice activity detection
- Improved context awareness
- Multi-platform chat support
- Performance optimizations

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Credits

- **AI**: Powered by [Anthropic Claude](https://anthropic.com)
- **Voice**: [ElevenLabs](https://elevenlabs.io)
- **Avatar**: [VTube Studio](https://denchisoft.com)
- **Speech-to-Text**: [OpenAI Whisper](https://github.com/openai/whisper)
- **Inspiration**: Neuro-sama and the VTuber community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/edzhuang/cuda-chan/issues)
- **Documentation**: [Setup Guide](SETUP_GUIDE.md)
- **Logs**: Check `data/logs/` for debugging

---

**Made with ❤️ for streamers who want an AI friend**

*CUDA-chan: Your supportive streaming sidekick!*
