# CUDA-chan 🤖✨

A fully autonomous AI VTuber system powered by Claude AI that can stream, chat with viewers, play games, and maintain a consistent personality.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎬 Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd cuda-chan
./scripts/setup.sh

# Configure (add your API keys)
nano .env

# Run
python main.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## ✨ Features

- **🎭 Live2D Avatar** - Full VTube Studio integration with emotion control
- **🗣️ Natural Voice** - ElevenLabs text-to-speech with caching
- **👀 Computer Vision** - Screen capture and OCR for game awareness
- **💬 Live Chat** - YouTube chat monitoring and natural responses
- **🎮 Game Playing** - Autonomous gameplay with keyboard/mouse control
- **🧠 AI Decision Making** - Claude-powered personality and responses
- **😊 Personality System** - Consistent character with customizable traits
- **🛡️ Safety Features** - Multiple failsafes and input validation

## 📋 Requirements

### Software
- Python 3.10+
- [VTube Studio](https://denchisoft.com) (free)
- Tesseract OCR

### API Keys
- [Anthropic API](https://console.anthropic.com) (~$3-5/hour)
- [ElevenLabs](https://elevenlabs.io) (~$0.30/hour)
- YouTube API (optional)

## 🚀 Installation

### Quick Setup (Recommended)

```bash
./scripts/setup.sh
```

### Manual Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run:
```bash
python main.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete instructions.

## 📖 Documentation

- **[Setup Guide](SETUP_GUIDE.md)** - Complete setup instructions
- **[Implementation Plan](.claude/plans/)** - System architecture and design

## 🎮 Usage

### Running CUDA-chan

1. Start VTube Studio with your model
2. Run: `python main.py`
3. CUDA-chan will connect and greet viewers

### Streaming Setup

1. Configure OBS to capture VTube Studio
2. Start YouTube live stream
3. Add video ID to `.env`
4. Restart CUDA-chan

### Chat Interaction

CUDA-chan automatically:
- Responds when mentioned
- Answers questions
- Reacts to game suggestions
- Maintains natural conversation

## ⚙️ Configuration

### Personality

Edit [config/personality.yaml](config/personality.yaml):

```yaml
name: "CUDA-chan"
personality_traits:
  - energetic
  - friendly
  - competitive
speaking_style:
  - casual language
  - gaming terminology
```

### Environment Variables

Key settings in `.env`:

```bash
# AI & Voice
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# Performance
TICK_RATE=1.0              # Decision frequency (seconds)
CLAUDE_MAX_RPM=50          # API rate limit
MAX_ACTIONS_PER_SECOND=10  # Input safety limit

# YouTube (optional)
YOUTUBE_VIDEO_ID=...
```

## 📊 Cost Tracking

Estimate costs:
```bash
python scripts/cost_tracker.py
```

Typical costs per hour:
- Conservative (6 decisions/min): ~$2.50/hr
- Moderate (10 decisions/min): ~$4.00/hr
- Active (15 decisions/min): ~$6.00/hr

## 🏗️ Project Structure

```
cuda-chan/
├── config/          # Configuration and personality
├── core/            # Main orchestrator and state management
├── ai/              # Claude AI integration
├── vision/          # Screen capture and analysis
├── control/         # Input control with safety
├── output/          # VTube Studio + TTS
├── chat/            # YouTube chat integration
├── games/           # Game controllers
├── utils/           # Utilities and logging
└── main.py          # Entry point
```

## 🔒 Safety Features

- **Action Validation** - Blocks dangerous commands
- **Rate Limiting** - Prevents API abuse
- **Failsafe Mode** - Emergency stop (move mouse to corner)
- **Input Whitelist** - Only safe keys allowed
- **Audit Logging** - All actions logged

## 🎯 Roadmap

### ✅ MVP (Current)
- Basic chat interaction
- VTube Studio control
- Simple game support
- TTS with caching

### 🚧 Phase 2 (Planned)
- [ ] Minecraft via Mineflayer
- [ ] OSU gameplay
- [ ] Advanced CV with game state
- [ ] Long-term memory
- [ ] Multi-game sessions

### 💡 Phase 3 (Future)
- [ ] Learning from gameplay
- [ ] Viewer preferences
- [ ] Multi-stream support
- [ ] Personality evolution

## 🐛 Troubleshooting

### VTube Studio Won't Connect
- Check VTube Studio is running
- Enable Plugin API in settings
- Verify token in `.env`

### No Voice Output
- Check ElevenLabs API key and voice ID
- Verify audio output device
- Check character quota

### High Costs
- Increase `TICK_RATE` to reduce decisions
- Lower `CLAUDE_MAX_RPM`
- Monitor with `scripts/cost_tracker.py`

See [SETUP_GUIDE.md](SETUP_GUIDE.md#part-8-troubleshooting) for more.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Credits

- **AI**: Powered by [Anthropic Claude](https://anthropic.com)
- **Voice**: [ElevenLabs](https://elevenlabs.io)
- **Avatar**: [VTube Studio](https://denchisoft.com)
- **Inspiration**: Neuro-sama and the VTuber community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Setup Guide](SETUP_GUIDE.md)
- **Logs**: Check `data/logs/` for debugging

---

**Made with ❤️ by the community**

*Note: This is an MVP. Features are being added iteratively.*
