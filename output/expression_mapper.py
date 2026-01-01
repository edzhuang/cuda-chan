"""Maps emotions to VTube Studio expressions."""

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
from utils.logger import log


class Emotion(Enum):
    """Emotion types."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    FOCUSED = "focused"
    SURPRISED = "surprised"
    THINKING = "thinking"
    CONFUSED = "confused"
    ANGRY = "angry"


@dataclass
class ExpressionConfig:
    """Configuration for a VTube Studio expression."""
    hotkey_name: str  # VTube Studio hotkey to trigger
    parameter_changes: Dict[str, float]  # Direct parameter changes
    duration: Optional[float] = None  # How long to hold expression (None = until changed)
    intensity: float = 1.0  # Expression intensity (0.0 - 1.0)


class ExpressionMapper:
    """Maps CUDA-chan's emotions to VTube Studio expressions."""

    # Default mapping of emotions to VTube Studio controls
    DEFAULT_MAPPINGS = {
        Emotion.NEUTRAL: ExpressionConfig(
            hotkey_name="Neutral",
            parameter_changes={
                "MouthSmile": 0.0,
                "MouthOpen": 0.0,
                "EyesWide": 0.0,
            },
            intensity=1.0
        ),
        Emotion.HAPPY: ExpressionConfig(
            hotkey_name="Happy",
            parameter_changes={
                "MouthSmile": 0.8,
                "MouthOpen": 0.3,
                "EyesWide": 0.2,
            },
            intensity=1.0
        ),
        Emotion.SAD: ExpressionConfig(
            hotkey_name="Sad",
            parameter_changes={
                "MouthSmile": -0.5,
                "MouthOpen": 0.1,
                "EyesWide": -0.2,
            },
            intensity=1.0
        ),
        Emotion.EXCITED: ExpressionConfig(
            hotkey_name="Excited",
            parameter_changes={
                "MouthSmile": 1.0,
                "MouthOpen": 0.5,
                "EyesWide": 0.8,
            },
            intensity=1.0
        ),
        Emotion.FOCUSED: ExpressionConfig(
            hotkey_name="Focused",
            parameter_changes={
                "MouthSmile": 0.0,
                "MouthOpen": 0.0,
                "EyesWide": -0.3,
            },
            intensity=0.8
        ),
        Emotion.SURPRISED: ExpressionConfig(
            hotkey_name="Surprised",
            parameter_changes={
                "MouthSmile": 0.0,
                "MouthOpen": 0.8,
                "EyesWide": 1.0,
            },
            intensity=1.0,
            duration=2.0  # Brief surprise
        ),
        Emotion.THINKING: ExpressionConfig(
            hotkey_name="Thinking",
            parameter_changes={
                "MouthSmile": 0.2,
                "MouthOpen": 0.0,
                "EyesWide": -0.1,
            },
            intensity=0.7
        ),
        Emotion.CONFUSED: ExpressionConfig(
            hotkey_name="Confused",
            parameter_changes={
                "MouthSmile": 0.0,
                "MouthOpen": 0.2,
                "EyesWide": 0.3,
            },
            intensity=0.8
        ),
        Emotion.ANGRY: ExpressionConfig(
            hotkey_name="Angry",
            parameter_changes={
                "MouthSmile": -0.7,
                "MouthOpen": 0.3,
                "EyesWide": -0.5,
            },
            intensity=1.0
        ),
    }

    def __init__(self, custom_mappings: Optional[Dict[Emotion, ExpressionConfig]] = None):
        """
        Initialize expression mapper.

        Args:
            custom_mappings: Custom emotion -> expression mappings (overrides defaults)
        """
        self.mappings = self.DEFAULT_MAPPINGS.copy()

        if custom_mappings:
            self.mappings.update(custom_mappings)

        log.info(f"Expression mapper initialized with {len(self.mappings)} emotion mappings")

    def get_expression(self, emotion: str) -> Optional[ExpressionConfig]:
        """
        Get expression configuration for an emotion.

        Args:
            emotion: Emotion name (string)

        Returns:
            Expression configuration or None if not found
        """
        try:
            emotion_enum = Emotion(emotion.lower())
            return self.mappings.get(emotion_enum)
        except ValueError:
            log.warning(f"Unknown emotion: {emotion}")
            return self.mappings[Emotion.NEUTRAL]

    def get_hotkey(self, emotion: str) -> Optional[str]:
        """
        Get VTube Studio hotkey name for an emotion.

        Args:
            emotion: Emotion name

        Returns:
            Hotkey name or None
        """
        expression = self.get_expression(emotion)
        return expression.hotkey_name if expression else None

    def get_parameters(self, emotion: str) -> Dict[str, float]:
        """
        Get parameter changes for an emotion.

        Args:
            emotion: Emotion name

        Returns:
            Dictionary of parameter changes
        """
        expression = self.get_expression(emotion)
        return expression.parameter_changes if expression else {}

    def blend_emotions(
        self,
        primary_emotion: str,
        secondary_emotion: str,
        blend_factor: float = 0.5
    ) -> Dict[str, float]:
        """
        Blend two emotions together.

        Args:
            primary_emotion: Primary emotion
            secondary_emotion: Secondary emotion
            blend_factor: How much of secondary emotion (0.0 - 1.0)

        Returns:
            Blended parameter changes
        """
        primary_params = self.get_parameters(primary_emotion)
        secondary_params = self.get_parameters(secondary_emotion)

        blended = {}
        all_params = set(primary_params.keys()) | set(secondary_params.keys())

        for param in all_params:
            primary_val = primary_params.get(param, 0.0)
            secondary_val = secondary_params.get(param, 0.0)
            blended[param] = primary_val * (1 - blend_factor) + secondary_val * blend_factor

        log.debug(f"Blended {primary_emotion} and {secondary_emotion} (factor={blend_factor})")
        return blended

    def add_custom_mapping(self, emotion_name: str, expression_config: ExpressionConfig):
        """
        Add or override an emotion mapping.

        Args:
            emotion_name: Name of the emotion
            expression_config: Expression configuration
        """
        try:
            emotion_enum = Emotion(emotion_name.lower())
            self.mappings[emotion_enum] = expression_config
            log.info(f"Custom mapping added for emotion: {emotion_name}")
        except ValueError:
            log.error(f"Invalid emotion name: {emotion_name}")

    def get_speaking_animation_params(self, intensity: float = 0.5) -> Dict[str, float]:
        """
        Get parameters for speaking animation.

        Args:
            intensity: Speech intensity (0.0 - 1.0)

        Returns:
            Parameter changes for speaking
        """
        return {
            "MouthOpen": intensity * 0.6,
            "MouthSmile": intensity * 0.2,
        }

    def get_idle_animation_params(self) -> List[Dict[str, float]]:
        """
        Get parameters for idle breathing/blinking animation.

        Returns:
            List of keyframe parameters
        """
        return [
            {"MouthOpen": 0.0, "EyesWide": 0.0},  # Normal
            {"MouthOpen": 0.05, "EyesWide": 0.1},  # Slight open
            {"MouthOpen": 0.0, "EyesWide": 0.0},  # Back to normal
            {"MouthOpen": 0.0, "EyesWide": -0.5},  # Blink
            {"MouthOpen": 0.0, "EyesWide": 0.0},  # Normal
        ]

    def validate_parameters(self, params: Dict[str, float]) -> bool:
        """
        Validate that parameter values are within acceptable range.

        Args:
            params: Parameter dictionary

        Returns:
            True if valid
        """
        for param, value in params.items():
            if not isinstance(value, (int, float)):
                log.error(f"Invalid parameter value type for {param}: {type(value)}")
                return False
            if not -1.0 <= value <= 1.0:
                log.warning(f"Parameter {param} value {value} out of range [-1.0, 1.0]")
                return False
        return True


if __name__ == "__main__":
    # Test the expression mapper
    mapper = ExpressionMapper()

    print("Testing expression mapper:\n")

    # Test each emotion
    for emotion in ["happy", "sad", "excited", "neutral", "surprised"]:
        expression = mapper.get_expression(emotion)
        if expression:
            print(f"{emotion.upper()}:")
            print(f"  Hotkey: {expression.hotkey_name}")
            print(f"  Parameters: {expression.parameter_changes}")
            print(f"  Intensity: {expression.intensity}")
            print()

    # Test blending
    print("Blending happy + excited (50/50):")
    blended = mapper.blend_emotions("happy", "excited", 0.5)
    print(f"  {blended}")
    print()

    # Test speaking animation
    print("Speaking animation parameters:")
    speaking = mapper.get_speaking_animation_params(intensity=0.7)
    print(f"  {speaking}")
