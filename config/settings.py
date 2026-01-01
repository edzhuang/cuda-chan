"""Configuration management for CUDA-chan."""

import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class VoiceSettings(BaseModel):
    """ElevenLabs voice configuration."""
    voice_id: str = ""
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True


class PersonalityConfig(BaseModel):
    """Personality configuration."""
    name: str
    full_name: str
    description: str
    personality_traits: list[str]
    speaking_style: list[str]
    behavioral_constraints: list[str]
    backstory: str
    catchphrases: dict
    emotional_states: dict
    voice_settings: VoiceSettings
    gaming: dict
    chat_interaction: dict
    stream_behavior: dict
    content_guidelines: dict


class APIConfig(BaseModel):
    """API credentials and endpoints."""
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    elevenlabs_api_key: str = Field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    youtube_api_key: str = Field(default_factory=lambda: os.getenv("YOUTUBE_API_KEY", ""))


class VTubeStudioConfig(BaseModel):
    """VTube Studio connection settings."""
    host: str = Field(default_factory=lambda: os.getenv("VTUBE_STUDIO_HOST", "localhost"))
    port: int = Field(default_factory=lambda: int(os.getenv("VTUBE_STUDIO_PORT", "8001")))
    token: str = Field(default_factory=lambda: os.getenv("VTUBE_STUDIO_TOKEN", ""))


class YouTubeConfig(BaseModel):
    """YouTube stream configuration."""
    video_id: str = Field(default_factory=lambda: os.getenv("YOUTUBE_VIDEO_ID", ""))
    channel_id: str = Field(default_factory=lambda: os.getenv("YOUTUBE_CHANNEL_ID", ""))


class SystemConfig(BaseModel):
    """System configuration."""
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    tick_rate: float = Field(default_factory=lambda: float(os.getenv("TICK_RATE", "1.0")))
    max_context_messages: int = Field(default_factory=lambda: int(os.getenv("MAX_CONTEXT_MESSAGES", "20")))


class RateLimitConfig(BaseModel):
    """API rate limiting configuration."""
    claude_max_rpm: int = Field(default_factory=lambda: int(os.getenv("CLAUDE_MAX_RPM", "50")))
    claude_max_tokens: int = Field(default_factory=lambda: int(os.getenv("CLAUDE_MAX_TOKENS_PER_REQUEST", "2000")))
    elevenlabs_max_chars_per_month: int = Field(default_factory=lambda: int(os.getenv("ELEVENLABS_MAX_CHARACTERS_PER_MONTH", "100000")))


class SafetyConfig(BaseModel):
    """Safety and failsafe configuration."""
    enable_failsafe: bool = Field(default_factory=lambda: os.getenv("ENABLE_FAILSAFE", "true").lower() == "true")
    max_actions_per_second: int = Field(default_factory=lambda: int(os.getenv("MAX_ACTIONS_PER_SECOND", "10")))
    pyautogui_failsafe: bool = Field(default_factory=lambda: os.getenv("PYAUTOGUI_FAILSAFE", "true").lower() == "true")


class VisionConfig(BaseModel):
    """Computer vision configuration."""
    enable_screen_capture: bool = Field(default_factory=lambda: os.getenv("ENABLE_SCREEN_CAPTURE", "true").lower() == "true")
    screen_capture_interval: float = Field(default_factory=lambda: float(os.getenv("SCREEN_CAPTURE_INTERVAL", "1.0")))


class GameConfig(BaseModel):
    """Game configuration."""
    default_game: str = Field(default_factory=lambda: os.getenv("DEFAULT_GAME", "browser"))


class Settings:
    """Global settings manager."""

    def __init__(self):
        self.api = APIConfig()
        self.vtube_studio = VTubeStudioConfig()
        self.youtube = YouTubeConfig()
        self.system = SystemConfig()
        self.rate_limits = RateLimitConfig()
        self.safety = SafetyConfig()
        self.vision = VisionConfig()
        self.game = GameConfig()
        self.personality = self._load_personality()

    def _load_personality(self) -> PersonalityConfig:
        """Load personality configuration from YAML file."""
        personality_file = PROJECT_ROOT / "config" / "personality.yaml"

        if not personality_file.exists():
            raise FileNotFoundError(f"Personality file not found: {personality_file}")

        with open(personality_file, "r") as f:
            data = yaml.safe_load(f)

        # Override voice_id from environment if provided
        if os.getenv("ELEVENLABS_VOICE_ID"):
            data["voice_settings"]["voice_id"] = os.getenv("ELEVENLABS_VOICE_ID")

        return PersonalityConfig(**data)

    def validate(self) -> tuple[bool, list[str]]:
        """Validate that all required settings are present."""
        errors = []

        # Check API keys
        if not self.api.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is not set")
        if not self.api.elevenlabs_api_key:
            errors.append("ELEVENLABS_API_KEY is not set")

        # Check VTube Studio
        if not self.vtube_studio.token:
            errors.append("VTUBE_STUDIO_TOKEN is not set (can be obtained after first connection)")

        # Check voice ID
        if not self.personality.voice_settings.voice_id:
            errors.append("ELEVENLABS_VOICE_ID is not set")

        return len(errors) == 0, errors

    def get_data_dir(self) -> Path:
        """Get data directory path."""
        data_dir = PROJECT_ROOT / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir

    def get_cache_dir(self) -> Path:
        """Get cache directory path."""
        cache_dir = PROJECT_ROOT / "data" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def get_logs_dir(self) -> Path:
        """Get logs directory path."""
        logs_dir = PROJECT_ROOT / "data" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir


# Global settings instance
settings = Settings()


def load_config() -> Settings:
    """Load and return configuration."""
    return settings


if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    is_valid, errors = config.validate()

    print(f"Configuration loaded for: {config.personality.name}")
    print(f"Valid: {is_valid}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
