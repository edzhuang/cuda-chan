# CUDA-chan Setup Guide

Complete step-by-step guide to get CUDA-chan running.

## Part 1: Getting API Keys

### 1.1 Anthropic API (Claude) - REQUIRED

1. Go to https://console.anthropic.com
2. Sign up for an account
3. Go to "API Keys" section
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Save it securely - you'll add it to `.env` later

**Cost**: Pay-as-you-go, approximately $3-5 per streaming hour

### 1.2 ElevenLabs API (Voice) - REQUIRED

1. Go to https://elevenlabs.io
2. Sign up for an account
3. Choose a plan:
   - Free: 10,000 characters/month (good for testing)
   - Starter: $5/month for 30,000 characters (recommended)
4. Go to Profile Settings → API Keys
5. Copy your API key
6. Browse voices at https://elevenlabs.io/voice-library
7. Find a voice you like and copy its Voice ID

### 1.3 YouTube Data API (Optional)

**Option A: Official API** (more reliable, requires setup)

1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create credentials (OAuth 2.0)
5. Download credentials JSON

**Option B: pytchat** (easier, no API key needed)
- Uses web scraping
- May be less reliable
- No setup required - it's the default

**Recommendation**: Start with pytchat (Option B), switch to official API later if needed.

## Part 2: Installing Software

### 2.1 Python Installation

**macOS**:
```bash
brew install python@3.11
```

**Windows**:
- Download from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH"

**Linux**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

Verify installation:
```bash
python3 --version  # Should be 3.10 or higher
```

### 2.2 VTube Studio Installation

1. Download VTube Studio:
   - **Windows/Mac**: https://denchisoft.com
   - **iOS**: App Store
   - **Android**: Google Play

2. Get a Live2D Model:
   - **Free models**: https://booth.pm (search "Live2D model free")
   - **Commission**: Hire an artist on VGen, Fiverr, etc.
   - **Create your own**: Use Live2D Cubism Editor

3. Import model into VTube Studio:
   - Open VTube Studio
   - Click "+" to add model
   - Select your `.model3.json` file

### 2.3 Tesseract OCR (for screen reading)

**macOS**:
```bash
brew install tesseract
```

**Windows**:
- Download installer from https://github.com/UB-Mannheim/tesseract/wiki
- Install to default location
- Add to PATH: `C:\Program Files\Tesseract-OCR`

**Linux**:
```bash
sudo apt install tesseract-ocr
```

Verify:
```bash
tesseract --version
```

## Part 3: CUDA-chan Installation

### 3.1 Clone Repository

```bash
cd ~/Code  # or your preferred directory
git clone <repository-url>
cd cuda-chan
```

### 3.2 Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### 3.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will take a few minutes. If you get errors:
- Make sure you're in the virtual environment
- Try `pip3` instead of `pip`
- Check Python version is 3.10+

### 3.4 Configure Environment

```bash
# Copy example file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or: vim .env, code .env, etc.
```

Fill in at minimum:
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_VOICE_ID=your-voice-id-here
```

Save and close.

## Part 4: VTube Studio Configuration

### 4.1 Enable Plugin API

1. Open VTube Studio
2. Go to Settings (gear icon)
3. Navigate to "Plugins"
4. Enable "Allow plugins"
5. Keep VTube Studio running

### 4.2 Set Up Hotkeys (Expressions)

For CUDA-chan to control your avatar's emotions, set up these hotkeys:

1. In VTube Studio, click the folder icon (bottom right)
2. Go to "Hotkeys" tab
3. Create these hotkeys:

| Hotkey Name | What It Does |
|-------------|--------------|
| `Happy` | Smile expression |
| `Sad` | Sad/frown expression |
| `Excited` | Wide eyes, big smile |
| `Focused` | Narrowed eyes, neutral mouth |
| `Surprised` | Wide eyes, open mouth |
| `Neutral` | Default expression |

**How to create a hotkey**:
1. Click "Add Hotkey"
2. Name it (e.g., "Happy")
3. Add actions:
   - "Change Expression" → Select a happy expression
   - Or: "Set Parameter" → Adjust MouthSmile to 0.8
4. Save

## Part 5: First Run

### 5.1 Test Configuration

```bash
python main.py
```

You should see:
```
╔═══════════════════════════════════════════════════════╗
║         Autonomous AI VTuber System v0.1.0           ║
╚═══════════════════════════════════════════════════════╝

Checking configuration...
✓ Configuration valid
```

If you see errors:
- Check `.env` file has correct API keys
- Verify VTube Studio is running
- Check logs in `data/logs/`

### 5.2 Authenticate with VTube Studio

On first run, you'll see:
```
Received authentication token: abc123...
Add this token to your .env file as VTUBE_STUDIO_TOKEN
```

1. Copy the token
2. Add to `.env`:
   ```bash
   VTUBE_STUDIO_TOKEN=your-token-here
   ```
3. Restart CUDA-chan

### 5.3 Test Voice

CUDA-chan will say a greeting when it starts. You should hear:
- Speech through your speakers
- Avatar mouth moving in VTube Studio

If no sound:
- Check system volume
- Verify ElevenLabs API key and Voice ID
- Check logs for TTS errors

## Part 6: Streaming Setup

### 6.1 OBS Studio Setup

1. Download OBS: https://obsproject.com
2. Add Sources:
   - **Window Capture**: Select VTube Studio
   - **Game Capture**: For capturing games
3. Test your scene

### 6.2 YouTube Stream Setup

1. Go to YouTube Studio → Go Live
2. Set up your stream (title, category, etc.)
3. Copy the video ID from URL
   - URL: `https://youtube.com/watch?v=VIDEO_ID_HERE`
   - Copy just the ID part
4. Add to `.env`:
   ```bash
   YOUTUBE_VIDEO_ID=your-video-id-here
   ```
5. Start your stream in OBS
6. Restart CUDA-chan

### 6.3 Full Streaming Session

**Startup Order**:
1. Start VTube Studio
2. Start OBS
3. Start YouTube stream
4. Start CUDA-chan: `python main.py`
5. CUDA-chan will greet viewers and start monitoring chat

**Monitoring**:
- Watch `data/logs/cuda_chan_YYYY-MM-DD.log` for activity
- Check console for real-time updates
- Monitor API costs in logs

**Shutdown**:
1. Press Ctrl+C in CUDA-chan terminal
2. Wait for graceful shutdown
3. Stop YouTube stream
4. Close OBS and VTube Studio

## Part 7: Testing Without Streaming

### 7.1 Test Mode (No Stream)

You can test CUDA-chan without streaming:

1. Don't set `YOUTUBE_VIDEO_ID` in `.env`
2. Run: `python main.py`
3. CUDA-chan will:
   - Still control the avatar
   - Still speak (testing prompts)
   - Make autonomous decisions
   - But won't respond to chat

### 7.2 Test Individual Components

**Test VTube Studio**:
```python
python -c "from output.vtube_controller import VTubeStudioController; import asyncio; asyncio.run(VTubeStudioController().connect())"
```

**Test TTS**:
```python
python output/tts_manager.py
```

**Test Screen Capture**:
```python
python vision/screen_capture.py
```

## Part 8: Troubleshooting

### Common Issues

**"Configuration errors found"**
- Check all required keys are in `.env`
- Verify no extra spaces or quotes around values
- Use `.env.example` as reference

**"Failed to connect to VTube Studio"**
- Ensure VTube Studio is running
- Check Plugin API is enabled
- Try restarting VTube Studio
- Check firewall isn't blocking localhost:8001

**"TTS generation failed"**
- Verify ElevenLabs API key is valid
- Check you have characters remaining
- Test voice ID is correct
- Check internet connection

**"Chat monitor failed to start"**
- Verify video ID is correct
- Check stream is actually live
- Try pytchat mode (default)
- Check YouTube API quota if using official API

**High CPU/Memory Usage**
- Lower `TICK_RATE` in `.env` to 1.5 or 2.0
- Disable screen capture if not gaming
- Close unnecessary applications

**Avatar not responding**
- Check hotkeys are named correctly (case-sensitive)
- Verify authentication token in `.env`
- Check VTube Studio logs
- Try manual hotkey trigger to test

### Getting Help

1. **Check Logs**: `data/logs/cuda_chan_YYYY-MM-DD.log`
2. **Enable Debug**: Set `LOG_LEVEL=DEBUG` in `.env`
3. **Test Components**: Run individual test scripts
4. **Check Issues**: GitHub issues page

## Part 9: Next Steps

### After Setup

1. **Customize Personality**: Edit `config/personality.yaml`
2. **Adjust Settings**: Modify `.env` for your needs
3. **Test Games**: Try simple browser games
4. **Monitor Costs**: Keep eye on API usage
5. **Iterate**: Adjust based on stream feedback

### Recommended Settings for First Stream

```bash
# .env
TICK_RATE=1.5  # Slower = fewer API calls
CLAUDE_MAX_RPM=30  # Conservative rate limit
MAX_ACTIONS_PER_SECOND=5  # Safe input speed
LOG_LEVEL=INFO  # Standard logging
```

### When Ready to Optimize

After a few successful streams:
- Lower `TICK_RATE` to 1.0 for faster responses
- Increase `CLAUDE_MAX_RPM` if hitting limits
- Enable advanced features
- Add custom games

## Resources

- **VTube Studio Docs**: https://denchisoft.com/vtube-studio-docs
- **ElevenLabs Docs**: https://docs.elevenlabs.io
- **Anthropic Docs**: https://docs.anthropic.com
- **CUDA-chan Wiki**: [Your wiki URL]

## Support

Need help?
- Open an issue on GitHub
- Check troubleshooting section above
- Review logs in `data/logs/`

---

**Estimated Setup Time**: 1-2 hours for first-time setup
**Difficulty**: Intermediate (requires basic terminal/API knowledge)
